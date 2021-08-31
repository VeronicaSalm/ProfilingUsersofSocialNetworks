# This script
#   - Iterates over all pairs of CSV files and creates output with a single rating for each tweet
#   - Changes all ratings for French tweets to "Not Sure"
#   - Removes any tweets with <5 tokens
#   - Counts and prints stats on the tweet classes
#   - Updates mismatched ratings using the input Mismatches spreadsheet

import os, sys, json
import csv
import pandas as pd
import argparse
from collections import defaultdict
from math import isnan
import numpy as np
from tabulate import tabulate

parser = argparse.ArgumentParser(description="Finds rows with the same ID in different files that have a mismatched classification.")
parser.add_argument("src", help="Path to the input directory containing folders of tweet files", type=str)
parser.add_argument("mismatch_filename", help="Path to the already-existing mismatch file", type=str)
parser.add_argument("dest", help="Path to the csv file where the output should be stored", type=str)

ID = "Tweet ID"
TEXT = "Full Text"
MASK = "Mask Sentiment"
LANG = "Language"
NOTES = "Notes"
NUM_ROWS_TO_COMPLETE = 200



stats = dict()
general_stats = dict()
mask_related_stats = dict()

FRENCH = "French"
NOT_SURE = "Not Sure"
MIN_TOKENS = 5
FLAG = False

def resolve(writer, tid, text, mask, lang, filename):
    """
    Either writes the (possibly modified) row to the output file or discards it.
    """
    # if the language is French, set the mask class to "Not Sure"
    if lang == FRENCH:
        mask = NOT_SURE

    # if the tweet is too short, ignore it
    # TODO: remove neutral check to leave Neutral tweets in
    if len(text.split()) < MIN_TOKENS:
        return
    #  global FLAG
    #  if mask == "Neutral":
    #      if FLAG == True:
    #          return
    #      FLAG = True


    # store the result in the stats dictionary
    if mask not in stats:
        stats[mask] = defaultdict(int)
    if mask not in general_stats:
        general_stats[mask] = defaultdict(int)
    if mask not in mask_related_stats:
        mask_related_stats[mask] = defaultdict(int)

    if "general" in filename:
        general_stats[mask][lang] += 1
    elif "mask" in filename:
        mask_related_stats[mask][lang] += 1
    else:
        raise Exception("Filename expected to be either 'mask_related' or 'general'! Got: {}".format(filename))
    stats[mask][lang] += 1

    row = [tid, text,  mask, lang, filename]
    writer.writerow(row)

def display_stats(s, title):
    """
    Prints the statistics dictionary and title provided.
    """
    mask_headers = ["Pro-Mask", "Anti-Mask", "Neutral", "Unrelated", "Not Sure"]
    lang_headers = ["English", "French", "English+French", "Multiple", "Other"]
    print(title)

    L = []
    for m in mask_headers:
        r = [m]
        if m not in s:
            s[m] = defaultdict(int)
        for l in lang_headers:
            r.append(s[m][l])
        L.append(r)
    print(tabulate(L, headers=lang_headers))
    print()

    languages = dict()
    for l in lang_headers:
        languages[l] = 0
    mask_counts = dict()
    for m in mask_headers:
        mask_counts[m] = 0
    for c in s.keys():
        mask_counts[c] = sum([v for v in s[c].values()])

        for l,v in s[c].items():
            languages[l] += v

    print(tabulate([list(l) for l in languages.items()], headers=["Language", "Count"]))
    print()
    print(tabulate([list(m) for m in mask_counts.items()], headers=["Mask Classification", "Count"]))
    print()

    print("TOTAL:", sum([v for v in languages.values()]))
    print("\n")



if __name__ == "__main__":
    args = parser.parse_args()

    # maps each fname to the two paths where it is from
    files = defaultdict(list)

    # open the mismatches file and gather all mismatches
    mismatches = pd.read_excel(args.mismatch_filename, engine="openpyxl", converters={ID:str})
    mismatch_dict = dict()
    for m in mismatches.values:
        # skip blank rows
        if pd.isnull(m[0]):
            continue
        text = m[1]
        r1 = m[2]
        r2 = m[3]
        mid = int(m[0])
        # check for duplicates
        key = text + m[2] + m[3]
        if key in mismatch_dict:
            print(m[0])
            print(mismatch_dict[text][0])
            print("Error! Found duplicate text!")
            print(m)
            print(text, mismatch_dict[text])
            sys.exit()
        mismatch_dict[key] = m


    for dr in sorted(os.listdir(args.src)):
        dr_path = os.path.join(args.src, dr)
        if not os.path.isdir(dr_path):
            print(f"Error! Encountered non-directory in source: {dr_path}")
            raise NotADirectoryError

        # construct the files dictionary
        for fname in sorted(os.listdir(dr_path)):
            fpath = os.path.join(dr_path, fname)
            files[fname].append(fpath)

    # find mismatches
    mms, bmms = 0, 0
    f = open(args.dest, "w")
    writer = csv.writer(f)
    writer.writerow([ID, TEXT, MASK, LANG, "Source File"])
    for fname, paths in sorted(files.items()):
        if len(paths) != 2:
            print(f"Skipping {fname}, found {len(paths)} paths when 2 were expected.")
            continue
        else:
            print(fname)
            # dropna will remove any cells whose mask column is blank
            df1 = pd.read_excel(paths[0], engine="openpyxl", converters={ID:str})
            df1_nb = df1.dropna(subset=[MASK])
            df2 = pd.read_excel(paths[1], engine="openpyxl", converters={ID:str})
            df2_nb = df2.dropna(subset=[MASK])

            # otherwise, create two output files:
            #  1. The first is for mismatches where both raters have filled them in.
            #  2. The second is for mismatches where one cell is blank.
            #      - ideally, this second file should be a list of files + tweet IDs to check
            #        for each person who had a blank

            for i, (x, y) in enumerate(zip(df1.values, df2.values)):
                # variables for sanity
                xid, xtxt, xmask, xlang, xtags, xnotes = x
                yid, ytxt, ymask, ylang, ytags, ynotes = y

                # check if the row is blank
                if pd.isnull(xid) or pd.isnull(yid):
                    continue

                xid = int(float(xid))
                yid = int(float(yid))

                # if the tweet texts AND ids both mismatch, something went wrong
                if xtxt != ytxt and xid != yid:
                    print("Unexpected tweet text and ID mismatch!")
                    print(x)
                    print(y)
                    print(paths)
                    sys.exit()

                # otherwise, ignore anything where both raters haven't rated yet
                if pd.isnull(xmask) and pd.isnull(ymask) and pd.isnull(xlang) and pd.isnull(ylang):
                    if i < NUM_ROWS_TO_COMPLETE:
                        raise Exception("Found an incomplete row for at least one rater!")
                    continue

                # extracts the filename from the path without the extension,
                # e.g. "data/James/2020-01_general.xlsx" -> "2020-01_general"
                filename = paths[0].split("/")[-1].split(".")[0]

                # mask and language comparison
                if xmask != ymask or xlang != ylang:
                    key = xtxt+paths[0]+paths[1]

                    if pd.isnull(xmask) or pd.isnull(xlang) or \
                            pd.isnull(ymask) or pd.isnull(ylang):
                        # Something is blank - should not happen when producing final output!
                        raise Exception("Found an unexpected blank row!")

                    elif key not in mismatch_dict:
                        raise Exception("Found mismatched rows that do not exist in Mismatches dict!")
                    else:
                        # use the mismatch value, since the raters disagreed
                        row = mismatch_dict[key]
                        mask, lang = row[6], row[9]
                        if pd.isnull(mask) or pd.isnull(lang):
                            print(row)
                            raise Exception("Error! Found blank mismatch row!")
                        resolve(writer, xid, xtxt,  mask, lang, filename)
                else:
                    # here we can just use the values from the first rater,
                    # since both raters agreed
                    resolve(writer, xid, xtxt,  xmask, xlang, filename)
    f.close()

    display_stats(stats, "Overall Statistics")
    display_stats(general_stats, "General Sample File Statistics")
    display_stats(mask_related_stats, "Mask Related File Statistics")

    #  print(json.dumps(mask_related_stats, indent=4))
    #  print(json.dumps(general_stats, indent=4))
