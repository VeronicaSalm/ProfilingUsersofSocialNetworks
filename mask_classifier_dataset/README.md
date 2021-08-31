## Mask Classifier Dataset

## Code Structure 

```
data_with_ratings/
```
contains one folder for each of four raters involved in the project (names reduced to a single letter). 
```
original_data_unannotated/
```
Contains the original generated CSV files (two per month) with tweet ID and text.
```
check_tweet_ids.py
consolidate_ratings.py
filter_tweets.py
find_mismatches.py
find_mismatches_additive.py
unzip.py
```
Scripts to assist in constructing the dataset, see below for running instructions and explanations.
```
final_output.csv
final_output_IDs_only.csv
```
The final, consolidated output dataset. `final_output.csv` contains the tweet text, while `final_output_IDs_only.csv` is identical but with the "Full Text" column removed.

### Running Instructions

In general, the flow is as follows:
1. Download `.zip` archives, one for each rater containing the tweets they have classified so far.
2. Run `unzip.py` to extract the archives to a data folder.
3. Run `find_mismatches.py` to produce a Mismatch spreadsheet.
4. After resolving all mismatches manually with other raters, run `consolidate_ratings.py` to produce a single output file.
5. Finally, run `check_tweet_ids.py` to produce the final output, ensuring that the ID and text for each tweet still matches the original.

The file `filter_tweets.py` was not involved in the construction of the dataset, but does filter for tweets containing conditional language and is included in case it is useful.
 
#### check_tweet_ids.py
#### consolidate_ratings.py
#### filter_tweets.py
#### find_mismatches.py
#### find_mismatches_additive.py
#### unzip.py
