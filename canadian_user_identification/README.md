## Spatial Label Propagation

## Extracting Ground Truth Canadians 


## Extracting Ground Truth Canadian Tweets

The script `extract_ground_truth_tweets.py` is used to extract all tweets written by Canadian users in the ground truth set, along with any tweets that mention those users. The script assumes that the file `ground_truth.tsv` is present in the same directory and contains a list of ground-truth Canadian users.
```
python3 extract_ground_truth_tweets.py INPUT_PATH OUTPUT_PATH
```
where:
* `INPUT_PATH` is the path to a folder containing tweet files (.jsonl) to analyze 
* `OUTPUT_PATH` is the path to an existing folder where the output tweets should be stored.

### geoinference

### slp_cross_validation
