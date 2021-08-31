"""
Utility script, will unzip all .zip files in the source directory and place the
output into the destination directory.

Used to extract each folder from a given rater.
"""

import os, sys
import argparse

parser = argparse.ArgumentParser(description="Unzip all zip files in the src directory, and put the result in the dest directory.")
parser.add_argument("src", help="Path to the input directory", type=str)
parser.add_argument("dest", help="Path to the destination directory", type=str)


if __name__ == "__main__":
    args = parser.parse_args()

    print(f"Unzipping all zip files in directory {args.src}...")
    for fname in os.listdir(args.src):
        if fname.endswith(".zip"):
            fpath = os.path.join(args.src, fname)
            os.system(f"unzip {fpath} -d {args.dest}")

    print("Done!")
