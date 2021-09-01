# Canadian Datasets

## Code Structure

```
ground_truth.tsv
```
This file contains the IDs of the 22k Twitter users found to be Canadian by both the Canadian filter and spatial label propagation, along with their location (given as a pair of lat/lon coordinates).

```
canadian_ids_from_filter.tsv
```
This file is a list of IDs of Twitter users found to be Canadian by the Canadian filter only.

```
canadian_tweets_22k_dataset.zip
```
This file is a compressed version of the dataset consisting of all tweets IDs of tweets written by the 22k Canadian users.




## Running Instructions

#### convert_to_ids_only.py

This script copies the Canadian tweets dataset (a directory consisting of one directory of tweets (.jsonl files) for each month of data: each directory contains one tweet file for each hour in that month) into a new directory with the same structure, but keeps only the ID of each tweet. Each tweet file is converted from jsonl to tsv (a single tweet on each line). It can be run as follows:
```
python3 convert_to_ids_only.py src dest
```
* `src` is the path to the source directory
* `dest` is the path to the destination folder where the result should be stored, expected to not exist (if it already exists, you will be prompted to remove it)
