# extract Canadian-looking user ids

import argparse
import json
import os
import sys
from copy import deepcopy

# For printing status updates while running
NUM_TWEETS = 10000

PLACE = "place object"
PROFILE_LOCATION = "user profile location"
PROFILE_DESCRIPTION = "user profile description"


class CanadianFilter:
    def __init__(self, locations_fname="canadian_location_terms.txt", demonyms_fname="canadian_demonyms.txt"):
        # load the canadian demonyms and location terms
        with open(locations_fname, "r") as f:
            self.canadian_locs = set([i.lower() for i in f.read().split('\n') if len(i)])
        with open(demonyms_fname, "r") as f:
            self.canadian_demonyms = set([i.lower() for i in f.read().split('\n') if len(i)])

    def is_canadian(self, tweet_json):
        """ Determines if the author of a tweet is Canadian by applying a
        rule-based filter.

        Arguments:
            tweet_json: the json object representing a tweet whose
                        user we want to analyze

        Returns:
            result (dict): indicates the method / rule and evidence used to determine
                           that a user was Canadian.
                            result =  {"is_canadian" : BOOL,
                                       "method" : STRING,
                                       "evidence" : STRING,
                                       "country_code" : STRING,
                                       "description": STRING,
                                       "location" : STRING}
        """
        # Extract relevant info from the tweet
        tweetID = tweet_json["id"]
        desc = tweet_json["user"]["description"].lower()
        loc = tweet_json["user"]["location"].lower()
        userID = tweet_json["user"]["id"]

        # This json object is returned regardless of the verdict and contains
        # information about why the filter returned True or False.
        result =  {"is_canadian" : None,    # True if Canadian, False otherwise
                   "method" : None,         # indicates the rule used to make the verdict
                   "evidence" : None,       # the evidence that led to the verdict, if any
                   "country_code" : None,   # from place.country_code, if it exists
                   "description": desc,     # user profile description, lowercased
                   "location" : loc         # user profile location, lowercased
                   }

        # 1. Check whether the tweet is geotagged with a place object.
        place_country_code = None
        if "place" in tweet_json and tweet_json["place"] != None:
            place_country_code = tweet_json["place"]["country_code"]
        if place_country_code != None:
            if place_country_code == "CA":
                # The tweet is geotagged in Canada, return True.
                result["country_code"] = place_country_code
                result["is_canadian"] = True
                result["method"] = PLACE
                result["evidence"] = place_country_code
                return result
            else:
                # The tweet is geotagged outside of Canada, automatically return False.
                result["country_code"] = place_country_code
                result["is_canadian"] = False
                result["method"] = PLACE
                result["evidence"] = place_country_code
                return result

        # 2. Check whether the user's profile location contains a Canadian term.
        for d in self.canadian_locs:
            if d in loc:
                # The user's location field contains a Canadian term, return True.
                result["is_canadian"] = True
                result["method"] = PROFILE_LOCATION
                result["evidence"] = d
                return result

        # 3. Check if the user's description contains a Canadian demonym such
        #    as "Canadian" or "Albertan".
        for d in self.canadian_demonyms:
            if d in desc:
                # The user's description contains a Canadian demonym, return True
                result["is_canadian"] = True
                result["method"] = PROFILE_DESCRIPTION
                result["evidence"] = d

        return result

    def get_canadian_users(self, fpath):
        """
        Arguments:
            fpath: path to .jsonl file to index

        Returns:
            canadians: a set of all users found to be canadian
        """
        canadians = set()
        all_users = set()
        with open(fpath, "r") as json_file:
            print("Extracting Canadians from '{}'...".format(fpath))
            line = json_file.readline()
            i = 0 # count for printing status updates

            while line:
                d = json.loads(line)
                userID = d["user"]["id"]

                if i and i % NUM_TWEETS == 0:
                    # update the number of tweets processed so far
                    print("    i")

                # apply the filter
                result = self.is_canadian(d)

                # add canadian users to the canadian set
                if result["is_canadian"]:
                    canadians.add(str(userID))

                # keep track of the total number of users
                all_users.add(str(userID))
                line = json_file.readline()
                i += 1

        print(f"    Found {len(canadians)} Canadian users out of {len(all_users)} users")
        return canadians

if __name__ == "__main__":
    # When run from the terminal, this program will extract the authors of all tweets
    # from the input sample that appear to be Canadian. The resulting IDs will be stored
    # in the path specified by args.output_path.
    parser = argparse.ArgumentParser(description="Filter to extract users who seem Canadian based on their profile information")

    parser.add_argument("input_path",
                        help="The input folder containing .jsonl files",
                        type = str)
    parser.add_argument("output_path",
                        help="The file to which to write Canadian user IDs",
                        type = str)

    args = parser.parse_args()

    cf = CanadianFilter()
    out_file = open(args.output_path, "a")

    canadians = set()
    if os.path.isdir(args.input_path):
        for f in sorted(os.listdir(args.input_path)):
            fpath = os.path.join(args.input_path, f)
            new = cf.get_canadian_users(fpath)

            # add all newly found canadians to the overall set
            canadians = canadians.union(new)
    else:
        # process a single file
        canadians = cf.get_canadian_users(args.input_path)

    # write all Canadian IDs to the output file
    for c in canadians:
        out_file.write(c+"\n")

    out_file.close()
    print("Done searching all provided files.")
