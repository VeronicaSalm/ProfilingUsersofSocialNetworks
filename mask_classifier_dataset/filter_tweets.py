"""
Generates a list of 50 tweets containing conditional language from the provided files.
"""

import os, sys, json
import csv
import pandas as pd
import argparse
from collections import defaultdict
from math import isnan

parser = argparse.ArgumentParser(description="Filters only tweets with conditional language.")
parser.add_argument("src", help="Path to the input directory containing folders of tweet files", type=str)
parser.add_argument("dest", help="Path to the destination file (csv) where the output should be stored", type=str)

ID = "Tweet ID"
TEXT = "Full Text"
MASK = "Mask Sentiment"
LANG = "Language"
NOTES = "Notes"


def is_mask_related(text):
    # the keywords to prioritize
    criteria = {"mask", "#mask", "#masks", "#wearamask", "masks", "wear", "mask-wearing"}
    phrase_criteria = {"face covering", "face-mask", "mask wearing"}

    # check if this tweet satisfies the criteria
    satisfying = False
    for c in criteria:
        # check for masks, mask, or wear
        if c in text.lower().split():
            satisfying = True
            break

    for p in phrase_criteria:
        # for these, just do a simple pattern match
        if p in text.lower():
            satisfying = True
            break

    return satisfying

if __name__ == "__main__":
    args = parser.parse_args()

    # maps each fname to the two paths where it is from
    files = defaultdict(list)

    for dr in sorted(os.listdir(args.src)):
        dr_path = os.path.join(args.src, dr)
        if not os.path.isdir(dr_path):
            print(f"Error! Encountered non-directory in source: {dr_path}")
            raise NotADirectoryError

        # construct the files dictionary
        for fname in sorted(os.listdir(dr_path)):
            fpath = os.path.join(dr_path, fname)
            files[fname].append(fpath)

    # find conditional tweets
    cond_lang = ["if", "unless"]
    cnt = 0
    with open(args.dest, "w") as out_fobj:
        out_writer = csv.writer(out_fobj)
        for fname, paths in files.items():
            fpath = paths[0] # only process one file, since tweet texts are identical
            df1 = pd.read_excel(fpath, engine="openpyxl", converters={ID:str})

            for row in df1.values:
                text = row[1]
                if pd.isnull(text):
                    continue
                ID = row[0]

                # make sure the tweet is mask-related first
                if not is_mask_related(text):
                    continue

                words = [t.lower() for t in text.split()]

                # determine if the tweet contains conditional language
                is_conditional = False
                for cl in cond_lang:
                    if cl in words:
                        is_conditional = True
                        break

                if "not" in words and "necessarily" in words:
                    is_conditional = True

                if is_conditional:
                    cnt += 1
                    out_writer.writerow([int(ID), fname.split(".")[0], text])
                    if cnt == 50:
                        print("Found 50 conditional tweets.")
                        sys.exit()


