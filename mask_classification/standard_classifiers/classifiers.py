"""
Load in the data for use in classifiers that require sparse matrices.
"""
import csv
import sys
import numpy as np
from tabulate import tabulate
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import *
from sklearn.neighbors import KNeighborsClassifier
from sklearn.semi_supervised import LabelSpreading
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sentence_transformers import SentenceTransformer
from standard_classifiers.normalize import normalize_text
from standard_classifiers.cross_validation import DataManagerCV

# for indexing into each row using the appropriate column
ID = 0      # tweet ID
TEXT = 1        # text of the tweet
LABEL = 2       # class, e.g. Anti-Mask
LANGUAGE = 3    # language, e.g., English

class DataManager():
    def __init__(self):
        self.saved_vectors = {}

    def add_data(self, train_rows, test_rows):
        """
        Initialize data directly, rather than loading from file.
        Also called from load_from_files()
        """
        self.train_rows = train_rows
        self.test_rows = test_rows

        self.train_data = [row[TEXT] for row in self.train_rows]
        self.num_train = len(self.train_data)
        self.train_labels = [row[LABEL] for row in self.train_rows]
        self.train_classes = sorted(list(set(self.train_labels)))

        self.test_data = [row[TEXT] for row in self.test_rows]
        self.num_test = len(self.test_data)
        self.test_labels = [row[LABEL] for row in self.test_rows]
        self.test_classes = sorted(list(set(self.test_labels)))

        self.X_train = []
        self.X_test = []

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
        NORMALIZE TEXT
        """
        self.train_data_normal, self.test_data_normal = [], []
        for d in self.train_data:
            self.train_data_normal.append(normalize_text(d))
        for d in self.test_data:
            self.test_data_normal.append(normalize_text(d))

        self.has_results = False
        self.NUMBER_LABELS = False

    def load_from_files(self, train_path, test_path):
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

        self.add_data(self.train_rows, self.test_rows)

    def accuracy(self):
        """
        Display the classification report for the current results, and return the accuracy.
        """
        if self.has_results == False:
            raise Exception("No results are available, cannot generate confusion matrix.")
        N = 18
        print("\n" + "-"*N + " CLASSIFICATION REPORT " + "-"*N)
        if self.NUMBER_LABELS:
            test_labels = [self.classes.index(i) for i in self.test_labels]
            a = accuracy_score(test_labels, self.y_pred)
            print(classification_report(test_labels, self.y_pred, digits=4))
        else:
            print(classification_report(self.test_labels, self.y_pred, target_names=self.classes, digits=4))
            a = accuracy_score(self.test_labels, self.y_pred)
        return a

    def confusion_matrix(self):
        """
        Display the confusion matrix of the current results.
        """
        if self.has_results == False:
            raise Exception("No results are available, cannot generate confusion matrix.")
        if self.NUMBER_LABELS:
            test_labels = [self.classes.index(i) for i in self.test_labels]
            cm = confusion_matrix(test_labels, self.y_pred)
        else:
            cm = confusion_matrix(self.test_labels, self.y_pred, labels=self.classes)

        # display the confusion matrix
        cm = np.ndarray.tolist(cm)
        for i in range(len(cm)):
            cm[i].insert(0, self.classes[i])
        N = 18
        print("\n" + "-"*N + " CONFUSION MATRIX " + "-"*N)
        print(tabulate(cm, headers=["Class"] + self.classes, floatfmt=".4f"))

    def count_embedding(self):
        vectorizer = CountVectorizer(lowercase=True, stop_words=None,
                                     max_df=1.0, min_df=1, max_features=None)

        X = vectorizer.fit_transform(self.train_data_normal + self.test_data_normal).toarray()
        self.X_train = X[0:self.num_train, :]
        self.X_test = X[self.num_train:, :]


    def naive_bayes(self):
        """
        Naive Bayes

        Also sets self.has_results to true, allowing result display methods to be
        called.
        """
        if len(self.X_train) == 0:
            self.count_embedding()
        print("Running Multinomial Naive Bayes...")
        clf = MultinomialNB(fit_prior=False, alpha=0.1)
        #  self.clf = ComplementNB(fit_prior=False)
        clf.fit(self.X_train, self.train_labels)
        self.y_pred = clf.predict(self.X_test)
        self.has_results = True

    def bert_embedding(self):
        """
        Uses the Bert Sentence Transformer to embed the training and
        test texts as vector representations. Stores the vectors in the
        lists X_train and X_test.
        """
        print("Using the Bert Sentence Transformer to embed the text...")
        model = SentenceTransformer('bert-base-nli-mean-tokens')
        self.X_train = []
        self.X_test = []
        for i, text in enumerate(self.train_data):
            idx = self.train_rows[i][ID]
            if idx in self.saved_vectors:
                encoding = self.saved_vectors[idx]
            else:
                encoding = model.encode(text)
                self.saved_vectors[idx] = encoding
            self.X_train.append(encoding)
        for i, text in enumerate(self.test_data):
            idx = self.test_rows[i][ID]
            if idx in self.saved_vectors:
                encoding = self.saved_vectors[idx]
            else:
                encoding = model.encode(text)
                self.saved_vectors[idx] = encoding
            self.X_test.append(encoding)

    def knn(self):
        """
        K-Nearest Neighbours

        Also sets self.has_results to true, allowing result display methods to be
        called.
        """
        if not len(self.X_train):
            self.bert_embedding()
        print("Running KNN...")
        self.neigh = KNeighborsClassifier(n_neighbors=1)
        self.neigh.fit(self.X_train, self.train_labels)
        self.y_pred = self.neigh.predict(self.X_test)
        self.has_results = True

    def label_propagation(self):
        """
        Discrete label propagation
        """
        if not len(self.X_train):
            # self.count_embedding()
            self.bert_embedding()
        self.label_prop = LabelSpreading()
        labels = [self.classes.index(t) for t in self.train_labels] + [-1 for t in self.test_labels]
        X = np.concatenate((self.X_train, self.X_test), axis=0)
        self.label_prop.fit(X, labels)
        self.y_pred = self.label_prop.transduction_[len(self.X_train)::]
        self.has_results = True
        self.NUMBER_LABELS = True

if __name__ == "__main__":
    cv = DataManagerCV(["data/train.csv", "data/test.csv"])
    dm = DataManager()

    folds = 10
    cv.divide_into_folds(folds)
    accuracies = []
    for i in range(folds):
        cv.set_validation(i)
        train = cv.get_train_data()
        test = cv.get_validation_data()
        print(f"\nFOLD {i}: Running classifier with {len(train)} train and {len(test)} test documents...")
        dm.add_data(train, test)
        # dm.naive_bayes()
        # dm.label_propagation()
        dm.knn()
        a = dm.accuracy()
        accuracies.append(a)
        dm.confusion_matrix()

    print("Accuracies:", accuracies)
    print(f"Average Accuracy over all {folds} folds:", sum(accuracies)/len(accuracies))
