## Spatial Label Propagation

## Packages

Run the following commands to install necessary packages:
```
pip install reverse_geocoder
pip install vaderSentiment
pip3 install geopy
```
You will also need to install graph-tool if using Spatial Label Propagation. Follow the instructions here: [graph-tool installation instructions](https://git.skewed.de/count0/graph-tool/-/wikis/installation-instructions#debian-ubuntu).

## Canadian Filter 

The script `canadian_filter.py` can be found in the directory `canadian_filter/` and extracts all tweets geotagged in Canada from a source directory. It can be run as follows:
```
cd canadian_filter
python3 canadian_filter.py INPUT_PATH OUTPUT_PATH
```
where:
* `INPUT_PATH` is the path to a folder containing tweet files (.jsonl) to analyze 
* `OUTPUT_PATH` is the path to an existing folder where the output tweets should be stored.

## Extracting Tweets Geotagged in Canada

The script `extract_canadian_tweets.py` is used to extract all tweets geotagged in Canada. It can be run as follows:
```
python3 extract_canadian_tweets.py INPUT_PATH OUTPUT_PATH
```
where:
* `INPUT_PATH` is the path to a folder containing tweet files (.jsonl) to analyze 
* `OUTPUT_PATH` is the path to an existing folder where the output tweets should be stored.

### Group Geotagged Tweets by User

The script `group_tweets_by_user.py` iterates over all the Canadian tweets and groups them by user. It can be run as follows:
```
python3 group_tweets_by_user.py INPUT_PATH OUTPUT_PATH
```
* `INPUT_PATH` is the path to a folder containing tweet files (.jsonl) to analyze 
* `OUTPUT_PATH` is the path to an existing folder where the output jsonl object mapping each user ID to tweets from that user should be stored.

### Compute Ground Truth Locations

The script `geolocate_users.py` reads all users from a `.jsonl` file that maps user IDs to geolocated tweets (the output of the previous script, `group_tweets_by_user.py`). For any user with at least 3 geotagged tweets, it computes a ground truth location using the geometric median. The geopy library needs to be installed before running this script:
```
pip3 install geopy
```
It can then be run as follows:
```
python3 geolocate_users.py INPUT_PATH OUTPUT_PATH
```
where:
* `INPUT_PATH` is the path to the `.jsonl` file mapping user IDs to geotagged tweets written by that user
* `OUTPUT_PATH` is the path to the output `.tsv` file where the results should be stored. Each row in the `.tsv` file has the form:
```
USER_ID \t LAT \t LON
```
This file can then be used as the input to the spatial label propagation algorithm.

## Extracting Tweet Datasets for Graph Construction

We created several different datasets:
1. all tweets on April 1, 2020 from 10 am to 8 pm
2. all tweets by the ground-truth Canadian users
3. all tweets by likely Canadians during April, 2020

For (1), I extracted the 10 relevant .jsonl files manually using `cp`. I then moved them into a folder and used gzip to compress them. For (2), I used the `extract_ground_truth_tweets.py` script below, and then modified this script slightly to include only tweets by ground-truth Canadians. The modified version can be found in the `slp_cross_validation` folder. For (3) 

### Extracting Ground Truth Canadian Tweets

The script `extract_ground_truth_tweets.py` is used to extract all tweets written by Canadian users in the ground truth set, along with any tweets that mention those users. The script assumes that the file `ground_truth.tsv` is present in the same directory and contains a list of ground-truth Canadian users. It can be run as follows:
```
python3 extract_ground_truth_tweets.py INPUT_PATH OUTPUT_PATH
```
where:
* `INPUT_PATH` is the path to a folder containing tweet files (.jsonl) to analyze 
* `OUTPUT_PATH` is the path to an existing folder where the output tweets should be stored.

### Extracting Canadian Tweets and Tweets Mentioning Canadians

The script `extract_tweets_by_or_mentioning_canadians.py` is used to extract all tweets written by likely-Canadian users (those considered Canadian by the Canadian filter) and those that mention such users. It expects that there exists a file called `canadian_ids_no_dups.txt`, which contains a list of all Canadian user IDs found by the Canadian filter. It also runs VADER on the resulting tweets (this is an artifact from an earlier script, but I left it in as I thought it might be useful). It can then be run as follows:
```
python3 extract_tweets_by_or_mentioning_canadians.py INPUT_PATH OUTPUT_PATH
```
where:
* `INPUT_PATH` is the path to a folder containing tweet files (.jsonl) to analyze, or to a single .jsonl file
* `OUTPUT_PATH` is the path to an existing folder where the output tweets should be stored.

## Spatial Label Propagation

For SLP, we use a heavily modified version of the Python code in the Geoinference repository (https://github.com/networkdynamics/geoinference). Among other things:
* I added some error handling to avoid crashes, and made expected file names more consistent. 
* I updated the code to run in Python 3 rather than 2.
* All modules other than SLP are removed, and the file structure is changed.
* The code can now construct both follow and mention graphs, and keeps only bidirectional edges.

### geoinference

A demo of the SLP code can be run on the server using all of the following lines. Note that the script assumes that the file of ground-truth user IDs and locations is a gzipped tsv file called `users.home-locations.geo-median.tsv.gz`. This file is already included in the repository. First ensure you are located in the `spatial_label_propagation` directory, and then run the following lines:

#### Construct Mention Network
```
python3 -m slp.app build_dataset dataset tweets "user.id" "entities.user_mentions.id"
```
where:
* `build_dataset`: indicates that the mode is dataset construction
* `dataset`: the path to a directory where the resulting dataset should be stored, must not exist!
* `tweets`: the path to a directory containing one or more tweet files (gzipped json files) where each line is a tweet object
* `“user.id”`: sets the field where the user id can be found
* `“entities.user_mentions.id”`: sets the field where the list of user mentions can be found

#### Construct Follow Network
If, instead, you want to construct a network of follow relationships, use:
```
python3 -m slp.app build_dataset dataset follows_test "id" "friends" "followers"
```
where:
* `build_dataset`: indicates that the mode is dataset construction
* `dataset`: the path to a directory where the resulting dataset should be stored, must not exist!
* `follows_test`: the path to a directory containing one or more follow files (gzipped jsonl files) containing on each line the follow data for a given user
* `“id”`: sets the field where the user id can be found
* `“friends”`: sets the field where the list of followed users can be found
* `“followers”`: sets the field where the list of following users can be found

#### Run SLP
Once the dataset is constructed, SLP can be run using:
```
python3 -m slp.app train SpatialLabelPropagation settings.json dataset model_dir
```
where:
* `train SpatialLabelPropagation`: indicates that the SLP algorithm should be run
* `settings.json`: the path to a settings file
* `dataset`: the path to the folder containing the dataset constructed above
* `model_dir`: the path to an output directory where the result should be stored, must not exist!

The output is stored in `model_dir` and is a `.tsv` file where each line is a user ID followed by a pair of lat/lon coordinates, the found location for that user. Note that all the ground truth users are written to this file as well (so this file contains all located users, not just new ones).

#### Changing the Settings

There is a file called `settings.json` in the `spatial_label_propagation` directory that allows changing the path to the ground-truth location file (by default, `users.home-locations.geo-median.tsv.gz`) and the number of iterations of SLP to execute (by default, 4).

### Cross Validation: slp_cross_validation

This folder contains several files involved in the cross validation:
* `DataManager.py` contains the code to divide the ground-truth Canadian users into folds. It can be run simply using `python3 DataManager.py` and expects the file `canadian_users.tsv` to be present in the same directory and contain all the ground truth user IDs (included in the repo).
* `convert_results.py` can be run to remove all non-ground-truth-Canadian users from the output of SLP. This script is used to clean the results of SLP for each fold of CV. It takes no command-line arguments, but the source directory and folder can be modified inside the code itself.
* The folder `folds` contains each of the five sets of training folds containing 80% of the ground truth labelled data.
* The folder `results` contains the results of each run of SLP, along with a "cleaned" version that only contains located Canadian users.
* `all_canadians_from_filter.csv` contains Canadian IDs found by the Canadian filter.
* `canadian_user_tweets` contains a gzipped file for the tweets by ground-truth Canadian users for each month from January to August, 2020.
