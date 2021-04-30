# iterates over all the tweets and groups them by user


import argparse
import json
import os
import sys
from collections import defaultdict

# Argparse for input json file, must be unzipped!
parser = argparse.ArgumentParser(description="Groups the tweets in the input folder by user ID.")

parser.add_argument("input_path",
                    help="The input .jsonl file containing hydrated tweet data or folder containing such files",
                    type = str)

parser.add_argument("output_path",
                    help="The output jsonl file where the output should be stored.",
                    type = str)

# Variables for index fields
MEDIA = "media"
RT_STATUS = "retweeted_status"
ENTITIES = "entities"
EXT_ENTITIES = "extended_entities"

users = defaultdict(list)

def process_tweet_file(inpath):
    """
    Arguments: 
        inpath: path to .jsonl file to process

    Returns:
        None, but stores the tweets in the user dictionary
    """
    global users
    with open(inpath, "r") as json_file:
        print("Processing '{}'...".format(inpath))
        line = json_file.readline()

        while line:
            d = json.loads(line)
            # get the user ID
            user_id = d["user"]["id"]
            
            # add to our map
            users[user_id].append(d)

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
    
    
    counts = defaultdict(int)
    for user_id, tweets in users.items():
        if len(tweets) >= 10:
            counts[10] += 1
        else:
            counts[len(tweets)] += 1
    print(counts)

    
    for user_id, tweets in users.items():
        output = { "user" : user_id,
                   "tweets" : tweets}
        print(json.dumps(output), file=out_obj)
    out_obj.close()
