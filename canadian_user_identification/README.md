## Spatial Label Propagation

## Extracting Ground Truth Canadians 

The script `extract_canadian_tweets.py` is used to extract all tweets geotagged in Canada. It can be run as follows:
```
python3 extract_canadian_tweets.py INPUT_PATH OUTPUT_PATH
```
where:
* `INPUT_PATH` is the path to a folder containing tweet files (.jsonl) to analyze 
* `OUTPUT_PATH` is the path to an existing folder where the output tweets should be stored.

## Group Tweets by User

The script `group_tweets_by_user.py` iterates over all the Canadian tweets and groups them by user. It can be run as follows:
```
python3 extract_ground_truth_tweets.py INPUT_PATH OUTPUT_PATH
```
* `INPUT_PATH` is the path to a folder containing tweet files (.jsonl) to analyze 
* `OUTPUT_PATH` is the path to an existing folder where the output jsonl object mapping each user ID to tweets from that user should be stored.

## Extracting Ground Truth Canadian Tweets

The script `extract_ground_truth_tweets.py` is used to extract all tweets written by Canadian users in the ground truth set, along with any tweets that mention those users. The script assumes that the file `ground_truth.tsv` is present in the same directory and contains a list of ground-truth Canadian users. It can be run as follows:
```
python3 extract_ground_truth_tweets.py INPUT_PATH OUTPUT_PATH
```
where:
* `INPUT_PATH` is the path to a folder containing tweet files (.jsonl) to analyze 
* `OUTPUT_PATH` is the path to an existing folder where the output tweets should be stored.

### geoinference

### slp_cross_validation
