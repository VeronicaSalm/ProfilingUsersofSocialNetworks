# Mask Classifier Dataset

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
unzip.py
```
Scripts to assist in constructing the dataset, see below for running instructions and explanations.
```
final_output.csv
final_output_IDs_only.csv
```
The final, consolidated output dataset. `final_output.csv` contains the tweet text, while `final_output_IDs_only.csv` is identical but with the "Full Text" column removed.

## Running Instructions

In general, the flow is as follows:
1. Download `.zip` archives, one for each rater containing the tweets they have classified so far.
2. Run `unzip.py` to extract the archives to a data folder.
3. Run `find_mismatches.py` to produce a Mismatch csv.
4. After resolving all mismatches manually with other raters, run `consolidate_ratings.py` to produce a single output file.
5. Finally, run `check_tweet_ids.py` to produce the final output, ensuring that the ID and text for each tweet still matches the original.

The file `filter_tweets.py` was not involved in the construction of the dataset, but does filter for tweets containing conditional language and is included in case it is useful.

#### unzip.py 
Run this script using:
```
python3 unzip.py src dest
```
where
* `src` is the source directory containing one `.zip` file per rater.
* `dest` is the destination directory (expected to exist but be empty) where the files should be extracted to.

Note that it is okay for there to be other files in the `src` directory; non-`.zip` files will be ignored. 

#### find_mismatches.py

This script creates two CSVs in the same directory where this script is run. The first `Mismatches.csv` is a spreadsheet of rows representing tweets where the two raters disagreed either on the mask class or language class. The second, `blanks.csv` is a spreadsheet indicating any blank rows that are missing either a mask classification, language classification, or both. Currently, only the first 200 rows are expected to be complete. This can be adjusted by changing `NUM_ROWS_TO_COMPLETE` on line 18 to a larger value. These two output csvs are intended to be uploaded to Google Drive and resolved manually (by a committee of raters for the mismatch csv and by each individual rater for the blanks csv).:w
```
python3 find_mismatches.py data_with_ratings Mismatches.xlsx
```
where
* `data_with_ratings` is the file containing one extracted folder per rater (this is the `dest` dir as produced by `unzip.py`)
* `Mismatches.xlsx` is an excel spreadsheet containing existing ratings.

Note that the input file `Mismatches.xslx` is expected to be `.xlsx` as downloaded from Google Drive and must have exactly the following columns:
```
["Tweet ID", "Full Text", "Rater 1", "Rater 2", "R1: Mask", "R2: Mask", "Mask Sentiment", "R1: Lang", "R2: Lang", "Language", "R1: Notes", "R2: Notes", "R1: Tags", "R2: Tags"]
```
* "Tweet ID": ID of the tweet
* "Full Text": text of the tweet
* "Rater 1": the file path to the first rater for this tweet
* "Rater 2": the file path to the second rater for this tweet
* "R1: Mask": the mask class chosen by the first rater
* "R2: Mask": the mask class chosen by the second rater
* "Mask Sentiment": the mask class chosen by the rater committee after resolving the mismatch
* "R1: Lang": the language chosen by the first rater
* "R2: Lang": the language chosen by the second rater
* "Language": the language chosen by the rater committee after resolving the mismatch
* "R1: Notes": notes/comments from the first rater
* "R2: Notes": notes/comments from the second rater
* "R1: Tags", "R2: Tags": Both currently unused columns, but could be used for tweet tags in the future.

Also, the input rater files are expected to obey the following restrictions:
* Each file must be named `YYYY_MM_general.xslx` or `YYYY_MM_mask_related.xslx`, where `YYYY` is the year, `MM` is the month.
* There must be two copies of each file, in two different directories (these are expected to be identical).
* Each file must have the columns (which are analogous to those described above): 
```
["Tweet ID", "Full Text", "Mask Sentiment", "Language", "Tags", "Notes"]
```

#### consolidate_ratings.py
#### check_tweet_ids.py
#### filter_tweets.py

