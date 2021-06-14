# Used to compress all tweet files, useful if the tweets are given
# in uncompressed jsonl format.
import os
import argparse

parser = argparse.ArgumentParser(description="Compresses tweet files in jsonl format to jsonl.gz format using gzip. Note that this is done in place.")

parser.add_argument("input_path",
                    help="The path to the input folder containing .jsonl files",
                    type = str)

if __name__ == "__main__":
    args = parser.parse_args()

    for f in os.listdir(args.input_path):
        path = os.path.join(args.input_path, f)
        os.system("gzip {}".format(path))

