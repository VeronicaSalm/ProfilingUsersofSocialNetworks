# Mask Sentiment Classifier

## Code Structure 

```
data/
data_unprocessed/
knn/
naive_bayes/
README.md
clean_data.py
universal_sentence_encoder_example.py
```

* `data/` contains the files `train.csv` (training data) and `test.csv` (held-out test set), which form the direct input for both classifiers. Currently, `test.csv` contains the 125 tweets used for the test set in my final paper.    
* `data_unprocessed/` contains the Google sheets (downloaded as .csv files directly from Google drive) which contain the manual classifications from myself (Veronica) and the psychology students involved in the project. These files may not be complete (i.e., may contain rows without classifications) so they cannot be used as direct input for the classifiers.
* `knn/` contains the code needed to run the KNN classifier with the Universal Sentence encoder. There are also nested folders (`tmp`, `test`) which store the pickled vectors produced by the Universal Sentence Encoder to prevent recomputation and memory errors (see below). The .pickle files are included in the repo for convenience, but should be removed if different input data is used.
* `naive_bayes/` contains the code for the Naive Bayes classifier. The main file is `nb_classifier.py`.

## Running instructions

### Naive Bayes

Simple answer, just run this:
```
python3 -m naive_bayes.nb_classifier --select mi 7500
```
Runs NB classifier with mutual info feature selection with 7500 features.     

More complete instructions:
```
python3 -m naive_bayes.nb_classifier [--train_path <train_path>] [--test_path <test_path>] [--select [mi|chi|freq] start (end step)]
```
* where `train_path`, `test_path` are optional command-line arguments allowing the user to change the paths used for the training and test sets.
* `train_path` is the path to the input training file, defaults to `data/train.csv`
* `eval_path` is the path to the output test file, defaults to `data/test.csv`
* `--select [mi|chi|freq] start (end step)`: If present, feature selection will be performed to generate the feature file `features.json` in the main directory. The feature selection utility function to use must be specified as either 'mi' (mutual information), 'chi' (chi square), or 'freq' (count based selection). Finally, an integer start value must be specified to indicate the value of k to test. The user may optionally specify an `end` value (integer second bound at which to stop running feature selection. Note that `end` is not included!) and a `step` value (the integer amount by which to decrease k at each iteration of feature selection). Integers `start` and `end` must be non-negative. The value of the `step` can be negative if the `start` is greater than `end`, although this is automatically corrected for the user if needed.

### KNN

```
python3 -m knn.knn_classifier data/train.csv data/test.csv -k=1
```

(Note, this script requires that the train and test file be specified, but allows changing the value of k above).    

Runs the KNN classifier with the universal sentence encoder to create the vectors. You can change k=1 to any value for k.
Note that on my machine, the script crashed several times due to out of memory errors, so I've set it up to store the vectors in files (.pickle files, those generated from the training dataset are in the folder called `tmp/`, while the ones generated from the test set are in the folder called `test/`) so they don't need to be generated on subsequent runs. You can just restart the script if it fails. 

## Clean Data
I've created a script to extract valid rows of files from the unprocessed_data folder. Currently, running this script will overwrite test.csv, which may not be ideal. Planning to update it soon to keep the test file constant.
