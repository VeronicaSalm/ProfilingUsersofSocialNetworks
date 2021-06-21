"""
Load in the data for use in classifiers that require sparse matrices.
"""
import sklearn
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, confusion_matrix
from tabulate import tabulate
import numpy as np
import csv
import sys

# for indexing into each row using the appropriate column
ROW_ID = 0      # tweet ID
TEXT = 1        # text of the tweet
LABEL = 2       # class, e.g. Anti-Mask
LANGUAGE = 3    # language, e.g., English

class DataManager():

    def __init__(self, train_path, test_path):
        """
        Load the training or test data from its respective path.
        """
        self.train_path = train_path
        self.test_path = test_path

        try:
            self.train_file = open(self.train_path, encoding='utf-8')
        except FileNotFoundError:
            # if we get here, print an error message and quit
            print("Error: Could not find training file '{}'.".format(train_path))
            sys.exit();

        try:
            self.test_file = open(self.test_path, encoding='utf-8')
        except FileNotFoundError:
            # if we get here, print an error message and quit
            print("Error: Could not find test file '{}'.".format(test_path))
            sys.exit();

        """
        TRAIN
        """
        self.train_reader = csv.reader(self.train_file, delimiter=",")
        self.train_header = next(self.train_reader)
        self.train_rows = []
        while True:
            try:
                r = next(self.train_reader)
                self.train_rows.append(r)
            except StopIteration:
                break
        print(f"Loaded {len(self.train_rows)} train documents from {self.train_path}.")

        self.train_data = [row[TEXT] for row in self.train_rows]
        self.num_train = len(self.train_data)
        self.train_labels = [row[LABEL] for row in self.train_rows]
        self.train_classes = sorted(list(set(self.train_labels)))

        """
        TEST
        """
        self.test_reader = csv.reader(self.test_file, delimiter=",")
        self.test_header = next(self.test_reader)
        self.test_rows = []
        while True:
            try:
                r = next(self.test_reader)
                self.test_rows.append(r)
            except StopIteration:
                break
        print(f"Loaded {len(self.test_rows)} test documents from {self.test_path}.")

        self.test_data = [row[TEXT] for row in self.test_rows]
        self.num_test = len(self.test_data)
        self.test_labels = [row[LABEL] for row in self.test_rows]
        self.test_classes = sorted(list(set(self.test_labels)))

        """
        CLASS LABELS
        """
        if self.train_classes != self.test_classes:
            print("Error: expected training and test sets to contain the same set of labels:")
            print(f"Train: {self.train_classes}")
            print(f"Test: {self.test_classes}")
            sys.exit()

        self.classes = self.train_classes

        """
        CREATE VECTORIZER
        """
        self.vectorizer = CountVectorizer(lowercase=True, stop_words=None,
                                     max_df=1.0, min_df=1, max_features=None)

        self.X = self.vectorizer.fit_transform(self.train_data + self.test_data).toarray()
        self.X_train = self.X[0:self.num_train, :]
        self.X_test = self.X[self.num_train:, :]
        self.feature_names = self.vectorizer.get_feature_names()

        """
        Multinomial Naive Bayes
        """
        clf = MultinomialNB()
        clf.fit(self.X_train, self.train_labels)
        y_pred = clf.predict(self.X_test)
        print(f"Accuracy = {accuracy_score(self.test_labels, y_pred)}")

        cm = confusion_matrix(self.test_labels, y_pred, labels=self.classes)
        cm = np.ndarray.tolist(cm)
        for i in range(len(cm)):
            cm[i].insert(0, self.classes[i])
        print(tabulate(cm, headers=["Class"] + self.classes, floatfmt=".4f"))

if __name__ == "__main__":
    dm = DataManager("data/train.csv", "data/test.csv")
