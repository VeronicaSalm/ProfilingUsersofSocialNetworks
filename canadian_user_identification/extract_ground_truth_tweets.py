# Extracts all the tweets from users in the ground truth set,
# and all the tweets which mention those users
# Stores the resulting tweets in an output folder

import argparse
import json
import os
import sys
import time
from copy import deepcopy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import csv

# Argparse for input json file, must be unzipped!
parser = argparse.ArgumentParser(description="Extract all tweets geotagged in Canada, run vader on them, and store the tweets in an output folder")

parser.add_argument("input_path",
                    help="The input .jsonl file containing hydrated tweet data or folder containing such files",
                    type = str)

parser.add_argument("output_path",
                    help="The output folder where geotagged tweets should be stored.",
                    type = str)

# Variables for index fields
MEDIA = "media"
RT_STATUS = "retweeted_status"
ENTITIES = "entities"
EXT_ENTITIES = "extended_entities"

def process_tweet_file(inpath, out_json_file):
    """
    Arguments:
        inpath: path to .jsonl file to process
        out_json_file: .jsonl file object to which to store the extracted tweets

    Returns:
        None, but stores the tweets to the jsonl file represented by out_json_file
    """
    analyser = SentimentIntensityAnalyzer()
    global canadian_ids

    i = 0
    canadian_cnt = 0
    with open(inpath, "r") as json_file:
        print("Processing '{}'...".format(fpath))
        line = json_file.readline()

        while line:
            d = json.loads(line)
            ID = d["id"]

            canadian_mentioned = False
            for mention in d["entities"]["user_mentions"]:
                if mention["id_str"] in canadian_ids:
                    canadian_mentioned = True
                    break

            if d["user"]["id"] in canadian_ids or canadian_mentioned == True:
                # perform vader sentiment analysis
                canadian_cnt += 1
                score = analyser.polarity_scores(d["full_text"])
                d["vader_score"] = score

                # store the tweet
                print(json.dumps(d), file=out_json_file)

            # if the tweet is not Canadian or the field doesn't exist for any reason,
            # skip this user
            line = json_file.readline()
            i += 1
    print(f"Found {canadian_cnt} tweets by a Canadian or mentioning a Canadian out of {i} total tweets")

if __name__ == "__main__":
    args = parser.parse_args()

    my_path = os.path.join(os.getcwd(), args.input_path)

    out_dir = os.path.join(os.getcwd(), args.output_path)

    # extract Canadian IDs
    # note we expect ground truth has no header
    with open("ground_truth.tsv", "r") as f:
        reader = csv.reader(f, delimiter='\t')
        canadian_ids = set([i[0] for i in reader])

    if os.path.isdir(my_path):
        # extract the subdirectory
        inp = my_path.split("/")
        if inp[-1]:
            inp = inp[-1]
        else:
            inp = inp[-2]
        out_file = os.path.join(out_dir, inp + ".jsonl")
        print(out_file)
        out_obj = open(out_file, "w")
        for f in sorted(os.listdir(my_path)):
            fpath = os.path.join(my_path, f)
            process_tweet_file(fpath, out_obj)
    else:
        out_path = os.path.join(out_dir, args.input_path.split('/')[-1])
        out_obj = open(out_path, "w")
        process_tweet_file(fpath, out_obj)

    out_obj.close()
