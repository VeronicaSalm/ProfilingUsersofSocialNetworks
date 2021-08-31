"""
Produces new output files with correct tweet IDs, using the original CSVs as reference.
This accounts for some truncating issues caused by reading Excel files.

WARNING: The file provided for the command line arg "consolidated_ratings" will be overwritten. Please ensure it is backed up first! Note that the overwrite simply ensures that the tweet IDs are correct and match those from the original files.
"""
import os, sys, json
import csv
import argparse
from collections import defaultdict


parser = argparse.ArgumentParser(description="Produces new output files with IDs guaranteed to be correct.")
parser.add_argument("consolidated_ratings", help="Path to the input csv where the consolidated ratings can be found. WARNING: this file will be overwritten by this script, please make sure it is backed up first!", type=str)
parser.add_argument("data", help="Path to the data folder containing original CSVs", type=str)
parser.add_argument("dest", help="Path to the csv file where the output should be stored", type=str)

if __name__ == "__main__":
    args = parser.parse_args()

    print("Reading original data...")
    og_data = defaultdict(list)
    for fname in os.listdir(args.data):
        with open(os.path.join(args.data, fname), "r") as f:
            reader = csv.reader(f)
            reader.__next__() # skip headers
            for row in reader:
                og_data[fname.split(".")[0]].append(row)

    print("Finding correct tweet IDs and original text...")
    cr_rows = []
    with open(args.consolidated_ratings, "r") as f:
        reader = csv.reader(f)
        cr_header = reader.__next__() # skip headers
        for row in reader:
            ID = row[0]
            text = row[1]
            fname = row[-1]

            NUM_DIGITS = 4
            found_row = None
            for og_row in og_data[fname]:
                oid, otext = og_row
                if otext == text and ID[0:-NUM_DIGITS] == oid[0:-NUM_DIGITS]:
                    if found_row:
                        print(ID, oid)
                        print(ID[0:-1], oid[0:-1])
                        print(ID[0:-1] == oid[0:-1])
                        print(text)
                        raise Exception("Duplicate!")
                    found_row = og_row
                elif ID[0:-NUM_DIGITS] == oid[0:-NUM_DIGITS]:
                    # ID matched, but text didn't (these are cases where a single
                    # punctuation mark was mistakenly removed)
                    found_row = og_row

            if not found_row:
                print(ID)
                print(text)
                print(fname)
                raise Exception("Did not find match for tweet!")

            new_row = [found_row[0], found_row[1], *row[2:]]
            cr_rows.append(new_row)

    print("Found", len(cr_rows), "total tweets.")
    print(f"Overwriting {args.consolidated_ratings} with new data...")
    with open(args.consolidated_ratings, "w") as f:
        writer = csv.writer(f)
        writer.writerow(cr_header)
        for row in cr_rows:
            writer.writerow(row)

    print(f"Writing ID-only output to {args.dest}...")
    with open(args.dest, "w") as f:
        writer = csv.writer(f)
        writer.writerow([cr_header[0], *cr_header[2:]])
        for row in cr_rows:
            writer.writerow([row[0], *row[2:]])

    print("Done!")
