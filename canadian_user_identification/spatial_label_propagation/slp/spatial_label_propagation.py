##
#  Copyright (c) 2015, David Jurgens
#
#  All rights reserved. See LICENSE file for details
##

"""
Can create a settings.json file with the following fields:

{
    "num_iterations" : INT,
    "location_source" : STRING
}

where
    num_iterations is the number of SLP iterations to run
    location_source is the name of a tsv.gz file mapping each user
                    ID to their lat and lon coordinates, i.e.,
                                USER_ID\tLAT\tLON
"""

import random
from geopy.point import Point
from geopy import distance
import os.path
import itertools
import gzip
import sys

from slp.settings import LOCATION_SOURCE, NUM_ITERATIONS

time_per_infer_user = 0
num_users_inferred = 0
time_per_geometric_median = 0
num_geometric_median = 0

class SpatialLabelPropagationModel:

    def __init__(self, user_id_to_location):
        self.user_id_to_location = user_id_to_location


    def infer_post_location(self, post):
        if not "user" in post:
            return None
        user = post["user"]

        if not "id" in user:
            return None

        user_id = user["id"]
        # If we know this user's location, report their home location
        if user_id in self.user_id_to_location:
            return self.user_id_to_location[user_id]
        else:
            return None


    def infer_posts_by_user(self, posts):
        if len(posts) == 0:
            return None

        # Each post is assumed originate from the user's home location, so just
        # infer the first post's location
        home_location = self.infer_post_location(posts[0])
        if home_location is None:
            return None

        # Then fill the array of post locations with the home location
        locations = []
        for i in range(0, len(posts)):
            locations.append((home_location.latitude, home_location.longitude))

        return locations


class SpatialLabelPropagation:
    def __init__(self, settings=None):
        # Location is represented as a lat/lon geopy Point
        self.user_id_to_location = {}
        if settings:
            self._settings = settings
            print("Loaded settings:", self._settings)
        else:
            self._settings = dict()

    def train_model(self, setting, dataset, model_dir):
        """
        Runs spatial label propagation (SLP) on the bi-directional @mention
        network present in the dataset.  The initial locations for SLP are
        set by identifying individuals with at least five GPS-tagged posts
        within 15km of each other.
        """

        print('Loading mention network')
        G = dataset.build_graph()
        all_users = set(G.iter_vertices())
        print('Loaded network with %d users and %d edges'
                     % (len(all_users), len(list(G.iter_edges()))))

        # This dict will contain a mapping from each user ID associated with at
        # least 5 posts within a 15km radius to the user's home location
        print('Loading known user locations')
        user_to_home_loc = {user: loc for (user, loc) in dataset.user_home_location_iter()}

        print('Loaded gold-standard locations of %s users (%s)'
                     % (len(user_to_home_loc),
                        float(len(user_to_home_loc)) / len(all_users)))

        # This dictionary is where we currently think a user is.  The subset of
        # users with known GPS-based home locations will always have their
        # gold-standard location set in this dict (i.e., it's not an estimate)
        user_to_estimated_location = {}

        # Update the initial data with the gold standard data
        user_to_estimated_location.update(user_to_home_loc)

        # This dictionary is the next prediction of where we think a user is
        # based on its neighbors.  This dict is separate from the current
        # estiamte to avoid mixing the two estimates during inference time.
        user_to_next_estimated_location = {}

        # TODO: make this configurable from the settings varaible
        if NUM_ITERATIONS in self._settings:
            num_iterations = self._settings[NUM_ITERATIONS]
        else:
            num_iterations = 4

        num_users = len(all_users)

        for iteration in range(0, num_iterations):
            print('Beginning iteration %s' % iteration)
            num_located_at_start = len(user_to_estimated_location)
            num_processed = 0
            for vertex in all_users:
                user_id = G.vp.user_id[vertex]
                user_to_next_estimated_location = self.update_user_location(vertex, G,
                                          user_to_home_loc,
                                          user_to_estimated_location,
                                          user_to_next_estimated_location)
                num_processed += 1
                if num_processed % 10000 == 0:
                    print('In iteration %d, processed %d users out of %d, located %d'
                                 % (iteration, num_processed, num_users, len(user_to_next_estimated_location)))
            num_located_at_end = len(user_to_next_estimated_location)
            print('At end of iteration %s, located %s users (%s new)' %
                         (iteration, num_located_at_end,
                          num_located_at_end - num_located_at_start))

            # Replace all the old location estimates with what we estimated
            # from this iteration
            user_to_estimated_location.update(user_to_next_estimated_location)

        print("Saving model (%s locations) to %s"
                    % (len(user_to_estimated_location), model_dir))

        # Short circuit early if the caller has specified that the model is not
        # to be saved into a directory
        if model_dir is None:
            return SpatialLabelPropagationModel(user_to_estimated_location)

        if not os.path.exists(model_dir):
            os.mkdir(model_dir)

        fh = open(os.path.join(model_dir, 'user-id-to-location.tsv'), 'w')

        for user_id, loc in user_to_estimated_location.items():
            fh.write("%s\t%s\t%s\n" % (user_id, loc[0], loc[1]))
        fh.close()
        return SpatialLabelPropagationModel(user_to_estimated_location)


    def update_user_location(self, vertex, G,
                             user_to_home_loc, user_to_estimated_location,
                             user_to_next_estimated_location):
        """
        Uses the provided social network and estimated user locations to update
        the location of the specified user_id in the
        user_to_next_estimated_location dict.  Users who have a home location
        (defined from GPS data) will always be updated with their home location.
        """
        user_id = str(G.vp.user_id[vertex])
        # Short-circuit if we already know where this user is located
        # so that we always preserve the "hint" going forward
        if user_id in user_to_home_loc:
            user_to_next_estimated_location[user_id] = user_to_home_loc[user_id]
            return user_to_next_estimated_location

        # For each of the users in the user's ego network, get their estimated
        # location, if any
        locations = []
        for neighbor_vertex in G.iter_all_neighbors(vertex): # G.neighbors_iter(user_id):
            neighbor_id = G.vp.user_id[neighbor_vertex]
            if neighbor_id in user_to_estimated_location:
                locations.append(user_to_estimated_location[neighbor_id])


        # If we have at least one location from the neighbors, use the
        # list of locations to infer a location for this individual.
        if len(locations) > 0:
            # NOTE: the median here could be replaced by any number of
            # functions (some of which we tried in the ICWSM paper).
            # For example, the social density method that Derek
            # suggested would replace the geometric median here as how
            # we estimate a user's location from their neighbors.
            median = get_geometric_median(locations)
            user_to_next_estimated_location[user_id] = median

        return user_to_next_estimated_location

    def load_model(self, model_dir, settings):
        """
        Reads in the user-id to location mapping from a file as the trained
        model.
        """
        user_id_to_location = {}

        model_file = gzip.open(os.path.join(model_dir, "user-to-lat-lon.tsv.gz"), 'r')
        for line in model_file:
            cols = line.split("\t")
            user_id = cols[0]
            lat = cols[1]
            lon = cols[2]
            user_id_to_location[user_id] = (float(lat), float(lon))
        print('NUM USERS: %d' % len(user_id_to_location))
        return SpatialLabelPropagationModel(user_id_to_location)

def get_user_location(user):

#   print user
#    print foo

    user_id = user["user_id"]
    posts = user["posts"]

    #print "getting location of %s"  % user_id

    # This method returns null if no location was found
    return user_id, get_home_location(posts)

def get_home_location(posts):
    """
    Returns the estimated home location of this user from their GPS-tagged
    posts, or None if the user could not be associated with any location
    """

    # The list of observed GPS locations for this user
    locations = []

    # Cycle through the posts and extract GPS locations
    for post in posts:
        if not "coordinates" in post:
            continue
            #print post
        coords = post["coordinates"]
        if coords is None:
            continue
            #print coords
        if not "type" in coords:
            continue

        coord_type = coords["type"]
        if coord_type is None:
            continue
        if not coord_type == "Point":
            continue
        coord_arr = coords["coordinates"]
        lat = coord_arr[0]
        lon = coord_arr[1]
        locations.append(Point(lat, lon))

        # We need at least 5 GPS tweets to infer a reliable home location
    if len(locations) < 5:
        return None

    # See if we can find at least 5 tweets within 15km of each other
    if has_home(locations):
        # Return the center as a proxy for this user's home location
        return get_geometric_median(locations)
    else:
        # Return that the user has no home location
        return None

def has_home(locations):
    """
    Returns True if the locations contain a subset of at least five points
    that are all within 15km of each other
    """

    n = len(locations)
    cur_locs = []
    for i in range(0, n-4):
        # Try adding the next location to start the search
        cur_locs.append(locations[i])
        for j in range(i+1, n):
            # If we recursively find a match starting from the current seed,
            # return success
            if can_find_home_match(cur_locs, locations, j, n):
                return True
        # Otherwise, remove the current seed and see if a different location
        # can be a member a subset matching the desired constraints
        cur_locs.pop()
    return False

def can_find_home_match(cur_locs, locations, next_index, n):
    """
    Searches the list of locations to see if some combination of locations
    starting at next_index can be added to the locations currently in
    cur_locs that satisfy the constraint that all locations in cur_locs
    must be at most 15km from each other.  If 5 such points are found,
    return success
    """

    # The next location to test
    loc2 = locations[next_index]

    # Check that the next point that could be added (at next_index) would
    # satisfy the distance requirement with the current location group
    for loc1 in cur_locs:
        if get_distance(loc1, loc2) > 15:
            return False

    # Push on the next location, to see if we can meet the requirements
    # while it is a member of the group
    cur_locs.append(locations[next_index])

    # If we have 5 locations that are all within 15km, return success!
    if len(cur_locs) == 5:
        return True

    # Search the remaining locations to see if some combination can satisfy
    # the requirements when this new location is added to the group
    for j in range(next_index+1, n):
        if can_find_home_match(cur_locs, locations, j, n):
            return True

    # Remove the last item added since no match could be found when it is a
    # member of the current location group
    cur_locs.pop()
    return False



def get_geometric_median(coordinates):
    """
    Returns the geometric median of the list of locations.
    """

    n = len(coordinates)

    # The geometric median is only defined for n > 3 points, so just return
    # an arbitrary point if we have fewer
    if n == 1:
        return coordinates[0]
    elif n == 2:
        return coordinates[random.randint(0, 1)]

    min_distance_sum = 10000000
    median = None # Point type

    # Loop through all the points, finding the point that minimizes the
    # geodetic distance to all other points.  By construction median will
    # always be assigned to some non-None value by the end of the loop.
    for i in range(0, n):
        p1 = coordinates[i]
        dist_sum = 0
        for j in range(0, n):

            # Skip self-comparison
            if i == j:
                continue

            p2 = coordinates[j]
            dist = get_distance(p1, p2)
            dist_sum += dist

            # Abort early if we already know this isn't the median
            if dist_sum > min_distance_sum:
                    break

        if dist_sum < min_distance_sum:
            min_distance_sum = dist_sum
            median = p1

    return median


def get_distance(p1, p2):
    """
    Computes the distance between the two latitude-longitude Points using
    Vincenty's Formula
    """
    return distance.distance(p1, p2).kilometers

