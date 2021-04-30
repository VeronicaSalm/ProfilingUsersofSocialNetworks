# KNN: Mask Sentiment Classifier

## Code Structure 

```
data/
data_unprocessed/
knn/
naive_bayes/
README.md
clean_data.py
```

* `data/` contains the files `train.csv` (training data) and `test.csv` (held-out test set), which form the direct input for both classifiers. Currently, `test.csv` contains the 125 tweets used for the test set, and `train.csv` contains the hand-crafted examples.    
* `data_unprocessed/` contains the Google sheets (downloaded as .csv files directly from Google drive) which contain the manual classifications from myself (Veronica) and the psychology students involved in the project. These files may not be complete (i.e., may contain rows without classifications) so they cannot be used as direct input for the classifiers.
* `knn/` contains the code needed to run the KNN classifier with the Universal Sentence encoder. There are also nested folders (`tmp`, `test`) which store the pickled vectors produced by the Universal Sentence Encoder to prevent recomputation and memory errors (see below). The .pickle files are included in the repo for convenience, but should be removed if different input data is used.
* `naive_bayes/` contains the code for the Naive Bayes classifier. The main file is `nb_classifier.py`. It is included here because some of the base files (e.g., the DataManager class) are shared by KNN as well.

## Running instructions

### KNN
The KNN classifier uses the Universal Sentence Encoder to create vector representations, hashtag segmentation as a preprocessing step, and hand-crafted examples as training data.     
Note that on my machine, the script crashed several times due to out of memory errors, so I've set it up to store the vectors in files (.pickle files, those generated from the training dataset are in the folder called `tmp/`, while the ones generated from the test set are in the folder called `test/`) so they don't need to be generated on subsequent runs. You can just restart the script if it fails.     

The KNN classifier can be run from this directory using:
```
python3 -m knn.knn_classifier data/train.csv data/test.csv -k=1
```
where:
* `data/train.csv` is the path to the training data,
* `data/test.csv`is the path to the test file, in csv format,
*  `-k=1` is the number of nearest neighbours to consider.

This script requires that the train and test file be specified. The value of `k` can be changed to any positive integer. 

#### Hashtag Master
The code also depends on the nested HashtagMaster folder, which is a modified version of the HashtagMaster repository (https://github.com/mounicam/hashtag_master). Hashtag segmentation is added as a preprocessing step.

#### Hand-Crafted Examples

The hand-crafted training examples can be found in `data/train.csv`.

#### Errors

Currently, the KNN classifier will also produce a script called `errors.csv`, in which each row is a misclassified example in the form:
```
Text,True Class,Guessed Class
```
where `Text` is the tweet text, `True Class` is the correct class assigned manually, and `Guessed Class` is the class chosen by the KNN classifier.     

## Clean Data
I've created a script to extract valid rows of files from the unprocessed_data folder. Currently, running this script will overwrite test.csv, so please use with caution.
