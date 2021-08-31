import os, sys, json
import csv
import pandas as pd
import argparse
from collections import defaultdict
from math import isnan
import numpy as np

parser = argparse.ArgumentParser(description="Finds rows with the same ID in different files that have a mismatched classification.")
parser.add_argument("src", help="Path to the input directory containing folders of tweet files", type=str)
parser.add_argument("mismatch_filename", help="Path to the already-existing mismatch file", type=str)

ID = "Tweet ID"
TEXT = "Full Text"
MASK = "Mask Sentiment"
LANG = "Language"
NOTES = "Notes"
NUM_ROWS_TO_COMPLETE = 200

if __name__ == "__main__":
    args = parser.parse_args()

    # maps each fname to the two paths where it is from
    files = defaultdict(list)

    # open the mismatches file and find all that have already been checked
    # if the mismatch file doesn't exist, skip this step
    mismatch_dict = dict()
    old_mismatches = None
    if os.path.exists(args.mismatch_filename):
        old_mismatches = pd.read_excel(args.mismatch_filename, engine="openpyxl", converters={ID:str})
        for m in old_mismatches.values:
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
    mismatches = []
    mms, bmms = 0, 0
    blanks = defaultdict(list)
    for fname, paths in files.items():
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

                #  print(xtxt, xtxt in mismatch_dict)

                # check if the row is blank
                if pd.isnull(xid) or pd.isnull(yid):
                    continue

                xid = int(float(xid))
                yid = int(float(yid))

                # if the tweet texts mismatch, something went wrong
                if xtxt != ytxt and xid != yid:
                    print("Unexpected tweet text and ID mismatch!")
                    print(x)
                    print(y)
                    print(paths)
                    sys.exit()

                # otherwise, ignore anything where both raters haven't rated yet
                if pd.isnull(xmask) and pd.isnull(ymask) and pd.isnull(xlang) and pd.isnull(ylang):
                    if i < NUM_ROWS_TO_COMPLETE:
                        blanks[paths[1]].append(i+2)
                        blanks[paths[0]].append(i+2)
                    continue

                # mask and language comparison
                if xmask != ymask or xlang != ylang:

                    if pd.isnull(xmask) or pd.isnull(xlang):
                        # the first person left something blank
                        # get the row number where the blank cell occurred
                        # +2 = +1 for header, +1 for to start at 1 instead of 0
                        blanks[paths[0]].append(i+2)


                    elif pd.isnull(ymask) or pd.isnull(ylang):
                        blanks[paths[1]].append(i+2)

                    elif xtxt+paths[0]+paths[1] not in mismatch_dict:
                        mismatches.append([xid, xtxt, paths[0], paths[1], xmask, ymask, "", xlang, ylang, "", xnotes, ynotes, xtags, ytags])

    print(len(mismatches))

    with open("Mismatches.csv", "w") as f:
        writer = csv.writer(f)
        if len(mismatch_dict.items()):
            print(len(old_mismatches.values))
            old_mismatches2 = old_mismatches.replace(np.nan, '', regex=True)
            writer.writerow(old_mismatches2.columns)
            for m in old_mismatches2.values:
                mid = m[0]
                if not mid:
                    continue
                writer.writerow(m)
        else:
            writer.writerow(["Tweet ID", "Full Text", "Rater 1", "Rater 2", "R1: Mask", "R2: Mask", "Mask Sentiment", "R1: Lang", "R2: Lang", "Language", "R1: Notes", "R2: Notes", "R1: Tags", "R2: Tags"])

        for m in mismatches:
            m2 = []
            for mi in m:
                if mi == "nan":
                    m2.append("")
                else:
                    m2.append(mi)
            writer.writerow(m2)


    # give a list of blank matches
    with open("blanks.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["File Path", "Rows With Blanks"])
        for fpath, ids in blanks.items():
            writer.writerow([fpath, ",".join([str(i) for i in ids])])
