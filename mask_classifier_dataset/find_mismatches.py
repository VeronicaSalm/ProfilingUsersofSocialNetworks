import os, sys, json
import csv
import pandas as pd
import argparse
from collections import defaultdict
from math import isnan

parser = argparse.ArgumentParser(description="Finds rows with the same ID in different files that have a mismatched classification.")
parser.add_argument("src", help="Path to the input directory containing folders of tweet files", type=str)
parser.add_argument("dest", help="Path to the destination file (csv) where the output should be stored", type=str)

ID = "Tweet ID"
TEXT = "Full Text"
MASK = "Mask Sentiment"
LANG = "Language"
NOTES = "Notes"

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

            if len(df1_nb) == 0 or len(df2_nb) == 0:
                # skip any files that one person or the other hasn't started yet
                continue

            # otherwise, create two output files:
            #  1. The first is for mismatches where both raters have filled them in.
            #  2. The second is for mismatches where one cell is blank.
            #      - ideally, this second file should be a list of files + tweet IDs to check
            #        for each person who had a blank

            for i, (x, y) in enumerate(zip(df1.values, df2.values)):
                # variables for sanity
                xid, xtxt, xmask, xlang, xnotes = x
                yid, ytxt, ymask, ylang, ynotes = y

                # check if the row is blank
                if pd.isnull(xid) or pd.isnull(yid):
                    continue


                # if the tweet texts mismatch, something went wrong
                if xtxt != ytxt:
                    print("Unexpected tweet text mismatch!")
                    print(x)
                    print(y)
                    print(paths)
                    sys.exit()

                # otherwise, ignore anything where both raters haven't rated yet
                if pd.isnull(xmask) and pd.isnull(ymask) and pd.isnull(xlang) and pd.isnull(ylang):
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

                    else:
                        mismatches.append([xid, xtxt, paths[0], paths[1], xmask, ymask, xlang, ylang, xnotes, ynotes])

    with open(args.dest, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["Tweet ID", "Full Text", "Rater 1", "Rater 2", "R1: Mask", "R2: Mask", "R1: Lang", "R2: Lang", "R1: Notes",  "R2: Notes"])
        for m in mismatches:
            writer.writerow(m)

    # give a list of blank matches
    with open("blanks.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["File Path", "Rows With Blanks"])
        for fpath, ids in blanks.items():
            writer.writerow([fpath, ",".join([str(i) for i in ids])])
