# Extracts a random sample of tweets of size N following specific criteria,
# evenly extracted from all tweet files with no duplicates.

import csv,  os, sys, random, json


R1, R2, R3, R4 = "1", "2", "3", "4"

def extract_tweets(fpath):
    """
    Extract all non-retweet tweets from this file, separating into groups
    that do or do not satisfy the criteria.
    """
    mask = dict()
    general = dict()

    # the keywords to prioritize
    criteria = {"mask", "#mask", "#masks", "#wearamask", "masks", "wear", "mask-wearing"}
    phrase_criteria = {"face covering", "face-mask", "mask wearing"}

    with open(fpath, "r") as json_file:
        line = json_file.readline()
        i = 0

        while line:
            d = json.loads(line)
            tweetID = d["id"]
            text = d["full_text"]
            
            # ignore retweets, look only at original content
            if "retweeted_status" in d:
                # read the next line
                line = json_file.readline()
                continue


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
            
            # try to sample longer tweets, avoid wasting manual labour classifying
            # a tweet that is just an emoji and a link
            if len(text.lower().split()) >= 5:
                if satisfying:
                    mask[tweetID] = text
                general[tweetID] = text
            
            # read the next line
            line = json_file.readline()
        
        # print an update of the size of the dictionaries
        return mask, general


if __name__ == "__main__":
    # the first dictionary has only mask-related tweets, the other is all tweets
    mask_tweets = dict()
    all_tweets = dict()

    N_SAMPLE = 100
    N_TWEETS_PER_FILE = 2000
    
    """
    paths = ["2020-01", "2020-02", "2020-03", "2020-04", 
             "2020-05", "2020-06", "2020-07", "2020-08",
             "2020-09", "2020-10", "2020-11", "2020-12",
             "2021-01", "2021-02", "2021-03", "2021-04", 
             "2021-05", "2021-06", "2021-07"]
    """
    paths = ["2021-07"]

    dest_paths = dict()
    # update this to indicate where the copies should go for the tweets
    # currently, all files will be put into R1's folder, since it turned out that
    # with the manual preprocessing required to set up each file in Google Drive,
    # it wasn't worth it to increase the number of copies until after uploading
    for p in paths:
        if p <= "2020-04":
            dest_paths[p] = {R1, R3}
        elif p <= "2020-06":
            dest_paths[p] = {R1, R2}
        else:
            dest_paths[p] = {R1}
    
    
    dest = "data_for_annotation_2021-04_2021-07"
    if os.path.exists(f"{dest}"):
        r = input(f"{dest} already exists! Would you like to remove it (y/n)?: ")
        if r.lower().startswith("y"):
            print("Removing...", end=" ")
            os.system(f"rm -r {dest}")
            print("Done!")
        else:
            print("Okay. Quitting...")
            sys.exit()

    os.system(f"mkdir {dest}")
    dest_dirs = [R1, R2, R3, R4]
    for dest_dir in dest_dirs:
        os.system(f"mkdir {dest}/{dest_dir}")

    for my_path in paths:
        print("Currently processing:", my_path)
        if os.path.isdir(my_path):
            tmp_masks, tmp_general = dict(), dict()
            for f in sorted(os.listdir(my_path)):
                fpath = os.path.join(my_path, f)
                print("Getting tweets from {}...".format(fpath))
                mask, general = extract_tweets(fpath)
                tmp_masks.update(mask)
                tmp_general.update(general)

                # Once all tweets from one month have been processed, do the random sample.
                print("    Found {} new ({} in tmp) mask tweets and {} new ({} in tmp) general tweets.".format(len(mask), len(tmp_masks), len(general), len(tmp_general)))
                if len(tmp_masks) < N_SAMPLE or len(tmp_general) < N_SAMPLE:
                    continue
                # subsample from all tweets in this file 
                A = random.sample(list(tmp_general.items()), N_SAMPLE)
                all_tweets.update(A)
                
                # subsample from the mask tweets in this file
                tmp_masks = dict(set(tmp_masks.items()) - set(all_tweets.items()))
                mask_sample_count = N_SAMPLE if len(tmp_masks) >= N_SAMPLE else len(tmp_masks)
                print("    Sampling {} mask tweets and {} general tweets randomly...".format(mask_sample_count, N_SAMPLE))
                M = random.sample(list(tmp_masks.items()), mask_sample_count)
                mask_tweets.update(M)

                # reset the temp dictionaries
                tmp_masks, tmp_general = dict(), dict()
                
            # we have now processed an entire folder (one month of tweets)
            # sample N_SAMPLE general tweets and N_SAMPLE mask tweets,
            # then save to two files.
            print(f"TOTAL FOR {my_path}: SAMPLED {len(all_tweets)} TWEETS, WITH {len(mask_tweets)} MASK-RELATED.")
            A = random.sample(list(all_tweets.items()), N_TWEETS_PER_FILE)
            M = random.sample(list(mask_tweets.items()), N_TWEETS_PER_FILE)

            dests = dest_paths[my_path]
            for d in dests:
                d = os.path.join(dest, d)
                with open(os.path.join(d, f"{my_path}_mask_related.csv"), "w") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Tweet ID", "Full Text"])
                    for m in M:
                        writer.writerow(m)
                with open(os.path.join(d, f"{my_path}_general.csv"), "w") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Tweet ID", "Full Text"])
                    for a in A:
                        writer.writerow(a)
            
            print("Resetting tweet dicts...")
            all_tweets, mask_tweets = dict(), dict()
            tmp_masks, tmp_general = dict(), dict()
