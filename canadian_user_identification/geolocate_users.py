# reads users from a .jsonl file where each line is a dictionary of the form
# { "user" : user_id, "tweets" : list_of_geotagged_tweets }
# Each geotagged tweet is assumed to have the "place" object.
# Then, users are geolocated by (1) checking that they have at least 3 tweets geotagged
# within a 100km radius and (2) computing the geometric median of the geotagged tweets for
# any such users.
# If users don't have at least 3 geotagged tweets in the given region, they are skipped.
# The result is a TSV file of
#   user_ID \t latitude \t longitude
# which can be used as seed data for the spatial label prop algorithm.

import argparse
import json
import os
import sys
from collections import defaultdict
import geopy.distance
import csv

# Argparse for input json file, must be unzipped!
parser = argparse.ArgumentParser(description="Takes a jsonl file mapping users to their geotagged tweets, and, for users with at least 3 tweets geotagged within 100 km, computes the geometric median of all their geotagged tweets to determine a ground-truth location for that user.")

parser.add_argument("input_path",
                    help="The input .jsonl file containing hydrated tweet data or folder containing such files",
                    type = str)

parser.add_argument("output_path",
                    help="The output tsv file where the output should be stored.",
                    type = str)

users = dict()


def geometric_median(tweets, min_locs):
    """
    Computes the geometric median of a list of geotagged tweets.
    Each tweet is expected to have the place object.

    Arguments:
        tweets (list): the list of geotagged tweets from the given user
        min_locs (int >= 1): the minimum number of geotagged tweets needed for a user to
                             be assigned a location

    Returns:
        median (tuple): the lat/lon coordinates of the geometric median
    """
    # get a list of location tuples, in the form lat/lon
    loc_list = []
    for t in tweets:
        # extract coordinates from the tweet, if available
        if "geo" in t and t["geo"] != None:
            # if there are coordinates, simply use those
            loc_list.append(tuple(t["geo"]["coordinates"]))
        elif "place" in t and t["place"] != None:
            # otherwise, use place information
            # since each polygon in the place object is a rectangle (at least in our data)
            # we can just use a formula for the midpoint of a rectangle
            # https://stackoverflow.com/questions/9734821/how-to-find-the-center-coordinate-of-rectangle
            polygon = t["place"]["bounding_box"]["coordinates"][0]

            if len(polygon) != 4:
                # expected a rectangular polygon
                print(json.dumps(t, indent=4))
                print("Error: Found place object whose polygon was not rectangular!")
                sys.exit()

            x1 = polygon[0][0]
            x2 = polygon[2][0]
            y1 = polygon[0][1]
            y2 = polygon[2][1]

            if x2 < x1:
                x1, x2 = x2, x1
            if y2 < y1:
                y1, y2 = y2, y1

            y_width = (y2 - y1)
            x_width = (x2 - x1)
            midpoint = (y1 + y_width / 2, x1 + x_width/2)
            loc_list.append(midpoint)

    if len(loc_list) < min_locs:
        # There were not enough tweets with locations to safely estimate
        return None

    median = None
    best_sum = float('inf')
    for i in range(len(loc_list)):
        sum_dist = 0
        for j in range(len(loc_list)):
            # extract coordinates, recall that each loc_list element
            # is (lat,lon), country
            coords1 = loc_list[i]
            coords2 = loc_list[j]
            d = geopy.distance.geodesic(coords1, coords2).km
            sum_dist += d

        if sum_dist < best_sum:
            median = loc_list[i]
            best_sum = sum_dist
    return median


def process_tweet_file(inpath, min_tweets=3):
    """
    Arguments:
        inpath: path to .jsonl file to process
        min_tweets (int): the minimum number of tweets that must be geotagged within
                          a 100 km radius for each user, defaults to 3.

    Returns:
        None, but stores the results in the global user dictionary
    """
    global users
    with open(inpath, "r") as json_file:
        print("Processing '{}'...".format(inpath))
        line = json_file.readline()

        while line:
            d = json.loads(line)
            # get the user ID
            user_id = d["user"]
            tweets = d["tweets"] # list of geotagged tweets from this user
            # try to find a ground-truth location for this user
            median = geometric_median(tweets, min_tweets)
            if median != None:
                print(median)
                users[user_id] = median

            line = json_file.readline()

if __name__ == "__main__":
    args = parser.parse_args()

    my_path = os.path.join(os.getcwd(), args.input_path)

    out_file = os.path.join(os.getcwd(), args.output_path)
    out_obj = open(out_file, "w")

    if os.path.isdir(my_path):
        for f in sorted(os.listdir(my_path)):
            fpath = os.path.join(my_path, f)
            process_tweet_file(fpath)
    else:
        process_tweet_file(my_path)

    tsv_writer = csv.writer(out_obj, delimiter="\t")
    for user, median in users.items():
        tsv_writer.writerow([user, median[0], median[1]])

    out_obj.close()
