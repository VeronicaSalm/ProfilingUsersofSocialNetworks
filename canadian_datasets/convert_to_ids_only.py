import sys, os, json, csv
import argparse

parser = argparse.ArgumentParser(description="Converts a tweet dataset of jsonl objects to a dataset (with the same structure) containing only tweet IDs.")
parser.add_argument("src", help="Path to the input directory containing folders of tweet files", type=str)
parser.add_argument("dest", help="Path to the destination directory where the output should be stored", type=str)

PRINT_VAL = 10000
def extract_tweet_ids(fpath):
    """
    Reads all tweets in a file and returns a list of their IDs, in order.
    """
    tweets = []
    with open(fpath, "r") as json_file:
        line = json_file.readline()
        i = 0

        while line:
            if i and i % PRINT_VAL == 0:
                print(f"    {i}")
            d = json.loads(line)
            tweets.append(d["id"])
            
            # read the next line
            line = json_file.readline()
            i += 1

    return tweets

if __name__ == "__main__":
    args = parser.parse_args()
    if os.path.exists(args.dest):
        a = input(f"The destination directory '{args.dest}' already exists. Would you like to remove it? (y/n): ")
        if a.lower().startswith("y"):
            print("Removing directory...")
            os.system(f"rm -r {args.dest}")
        else:
            print("Okay, quitting...")
            sys.exit()
    
    # create the destination directory
    os.system(f"mkdir {args.dest}")
    for d in sorted(os.listdir(args.src)):
        print(d)
        dir_path = os.path.join(args.src, d)
        dest_dir_path = os.path.join(args.dest, d)
        os.system(f"mkdir {dest_dir_path}")
        for fname in sorted(os.listdir(dir_path)):
            print(f"Processing {fname}...")
            fpath = os.path.join(dir_path, fname)
            out_fpath = os.path.join(dest_dir_path, fname.split(".")[0] + ".tsv")

            tweets = extract_tweet_ids(fpath)

            print(f"    Found {len(tweets)} tweets.")

            with open(out_fpath, "w") as f:
                writer = csv.writer(f, delimiter="\t")
                for tweetID in tweets:
                    writer.writerow([str(tweetID)])



