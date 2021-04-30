# -----------------------------------------------------------------------
# Name: Veronica Salm
# CCID: vsalm
# File: TrainingDataManager.py
#
# Description: Inherits from DataManager and contains functions specific
#              to the training data. Used specifically for NB
#              classification.
#--------------------------------------------------------------------
import sys, random, math

from naive_bayes.DataManager import DataManager
from naive_bayes.normalizer import normalize, tokenize
from naive_bayes.constants import CLASSES

class TrainingDataManager(DataManager):
    def __init__(self, filename, k, feature_selection=False):
        super(TrainingDataManager, self).__init__(filename)
        self.num_docs = len(self.data)
        # set the number of partitions to the k value passed in
        self.partitions = k

        # class frequencies for each partition
        self.class_freq = dict()

        # class frequencies for all documents together
        self.class_freq_all = dict()

        # will contain a randomized list of document indices
        self.shuffled_docs = []

        self.vocab_size = None
        self.vocabulary = None
        #  self._compute_vocabulary()

        # contains the start index, validation set size, and partition size of the given partition
        # each entry holds an index (the start position in the shuffled list)
        # and two counts (the number of documents in this partition and in the left out validation set)
        # the last partition may have slightly more documents, but not more
        # than self.partitions
        self.folds = [{"start_index": 0, "validation_set_size": 0, "training_set_size": 0} for i in range(self.partitions)]

        self.divide_into_folds()

        self._compute_class_frequencies()

        # only prepare term counts if we are performing feature selection
        if feature_selection:
            self.mutual_info = dict()
            self.term_counts()

    def _compute_class_frequencies(self):
        """ Called on startup, this function computes P(c) for every class c
        in the data. This is done both for all documents (ie, including the full
        training set) and for each partition separately. """

        # initialize the frequencies for
        # class_freq_all: all documents in all partitions
        # class_freq: separate frequencies for each partition
        for p in range(self.partitions):
            self.class_freq[p] = dict()
            for c in CLASSES:
                self.class_freq[p][c] = 0
                self.class_freq_all[c] = 0

        for i in range(self.num_docs):
            # get the real index from the shuffled list
            true_index = self.shuffled_docs[i]
            # get the true label
            c = self.get_relation(true_index)

            for p in range(self.partitions):
                # if the given index is within the fold for p
                if i < self.folds[p]["start_index"] or (p < self.partitions-1 and i >= self.folds[p+1]["start_index"]):
                    self.class_freq[p][c] += 1

            self.class_freq_all[c] += 1

    def prior_class_frequency(self, class_name, p=None):
        """ Determines the frequency with which a class appears in the data.
        Essentially, this estimates the prior probability of the class, P(c)

        Note that if present, p is the partition that has been left out
        in this phase of cross validation. """

        if p != None:
            if class_name not in self.class_freq[p]:
                print("Error: Class '{}'' does not exist in corpus.".format(class_name))
                sys.exit()

            return self.class_freq[p][class_name] / self.folds[p]["count"]

        else:
            # return the class frequency for all documents
            if class_name not in self.class_freq_all:
                print("Error: Class '{}'' does not exist in corpus.".format(class_name))
                sys.exit()

            return self.class_freq_all[class_name] / self.num_docs

    def _compute_vocabulary(self):
        """ Called on startup, this function finds the number of unique tokens
        in the corpus. """
        words = set()
        for i in range(len(self.data)):
            text = normalize(tokenize(self.get_tokens(i)))
            for t in text:
                words.add(t)

        self.vocab_size = len(words)
        self.vocabulary = words

    def get_vocab_size(self):
        """ Returns the number of unique tokens in the corpus. """
        if self.vocab_size == None:
            self._compute_vocabulary()

        return self.vocab_size

    def get_vocabulary(self):
        """ Returns a list of the unique tokens in the corpus."""
        if self.vocabulary == None:
            self._compute_vocabulary()

        return self.vocabulary

    def all_text_in_class(self, class_name, p=None):
        """ Returns a list of all tokens in the class, normalized. """

        text = []

        # if there are no partitions specified, get text from all documents
        # in the class given by class_name
        if p == None:

            for i in range(self.num_docs):
                if self.get_relation(i) == class_name:
                    # this document is in the given class
                    text.append(normalize(tokenize(self.get_tokens(i))))
        else:
            # get all text from documents in this class, excluding those
            # from the validation fold represented by p
            for i in range(self.num_docs):
                # if this index is not allocated to our validation set
                if i < self.folds[p]["start_index"] or (p < self.partitions-1 and i >= self.folds[p+1]["start_index"]):
                    true_index = self.shuffled_docs[i]
                    if self.get_relation(true_index) == class_name:
                        # this document is in the given class and not in the validation set
                        text.append(normalize(tokenize(self.get_tokens(true_index))))
        return text

    def frequency_scores(self, c, p=None):
        """ Returns a list of frequency tuples in the form (frequency, term)
        indicating the number of times each term appears in the given class. """
        scores = dict()
        for line in self.all_text_in_class(c, p):
            for t in line:
                if t in scores:
                    scores[t] += 1
                else:
                    scores[t] = 1

        for t in self.get_vocabulary():
            # set the counts of all terms not in the class to 0
            if t not in scores:
                scores[t] = 0


        ret = []
        for k, v in scores.items():
            ret.append((v, k))

        return ret


    def divide_into_folds(self):
        """ Randomly divides the training set into k partitions for
        cross validation.

        Creates:
            self.shuffled_docs: a list of indices of documents into
                                self.data, but shuffled for randomness
            self.folds: a list of the starting index and size of each
                        fold.
        """

        # get a list of document ids
        docs = [i for i in range(0, self.num_docs)]

        random.shuffle(docs)
        self.shuffled_docs = docs

        # this will give a lower bound on the number of documents
        validation_set_size = self.num_docs // self.partitions

        idx = 0
        for i in range(self.partitions):

            self.folds[i]["start_index"] = idx

            if i == self.partitions-1:
                # use all remaning documents for the last fold
                self.folds[i]["validation_set_size"] = self.num_docs-idx
            else:
                self.folds[i]["validation_set_size"] = validation_set_size

            self.folds[i]["count"] = self.num_docs - self.folds[i]["validation_set_size"]
            idx += validation_set_size

    def get_shuffled_indices(self, p):
        """ Get the true indices of all documents in the validation set
        represented by p. """
        start_idx = self.folds[p]["start_index"]
        end_idx = start_idx + self.folds[p]["validation_set_size"] -1
        return self.shuffled_docs[start_idx:end_idx+1]


    def term_counts(self):
        """ Computes the counts of each term in each class for the given
        partition and for the whole training dataset. """
        self.term_counts = dict()

        for i in range(self.num_docs):
            # set to remove duplicates

            true_idx = self.shuffled_docs[i]
            text = set(normalize(tokenize(self.get_tokens(true_idx))))
            c = self.get_relation(true_idx)
            for p in range(self.partitions):
                if i < self.folds[p]["start_index"] or (p < self.partitions-1 and i >= self.folds[p+1]["start_index"]):
                    for t in text:
                        if t not in self.term_counts:
                            self.term_counts[t] = dict()
                            for cl in CLASSES:
                                for par in range(self.partitions):
                                    self.term_counts[t][(cl, par)] = 0
                                self.term_counts[t][cl] = 0
                        self.term_counts[t][(c, p)] += 1

            # compute for whole training dataset in addition to each partition
            for t in text:
                if t not in self.term_counts:
                    self.term_counts[t] = dict()
                    for cl in CLASSES:
                        self.term_counts[t][(cl, par)] = 0
                    self.term_counts[t][cl] = 0

                self.term_counts[t][c] += 1




    def mutual_information(self, t, c, p):
        """ Returns the mutual information score for the given term and
        class in the given partition.

        Computes all of the following info for a term t, a class
        c and a partition (fold) p:

        N11 = the number of docs in c that contain t
        N10 = the number of docs not in c that contain t
        N01 = the number of docs in c that do not contain t
        N00 = the number of docs not in c that do not contain t

        Assumption: any term passed to this function has already been normalized.
        """

        if p == None:
            # if no partition is specified, compute the score for the whole
            # training data set
            N11 = self.term_counts[t][c]
            N01 = self.class_freq_all[c] - N11

            N10 = 0
            for other in CLASSES:
                if other != c:
                    N10 += self.term_counts[t][other]

            N = self.num_docs
            N00 = N - N01 - N10 - N11

        else:
            # assumes the term passed in is already normalized?
            N11 = self.term_counts[t][(c, p)]

            # class but not term = all docs in class - docs where term appears
            N01 = self.class_freq[p][c] - N11

            # docs where term appears but not in class
            N10 = 0
            for other in CLASSES:
                if other != c:
                    N10 += self.term_counts[t][(other, p)]

            N = self.folds[p]["count"]
            N00 = N - N01 - N10 - N11

        epsilon = 0.05

        m = (N11 / N) * math.log((epsilon + N * N11) / (epsilon + (N10 + N11)*(N11 + N01)), 2) \
            + (N01 / N) * math.log((epsilon + N * N01) / (epsilon + (N00 + N01)*(N11 + N01)), 2) \
            + (N10 / N) * math.log((epsilon + N * N10) / (epsilon + (N10 + N11)*(N10 + N00)), 2)\
            + (N00 / N) * math.log((epsilon + N * N00) / (epsilon + (N00 + N01)*(N00 + N10)), 2)

        return m

    def chi_square_score(self, t, c, p):
        """ Returns the chi square score for the given term and class
        in a given partition.

        Computes all of the following info for a term t, a class
        c and a partition (fold) p:

        N11 = the number of docs in c that contain t
        N10 = the number of docs not in c that contain t
        N01 = the number of docs in c that do not contain t
        N00 = the number of docs not in c that do not contain t

        Assumption: any term passed to this function has already been normalized.
        """
        if p == None:
            # if no partition is specified, compute the score for the whole
            # training data set
            N11 = self.term_counts[t][c]
            N01 = self.class_freq_all[c] - N11

            N10 = 0
            for other in CLASSES:
                if other != c:
                    N10 += self.term_counts[t][other]

            N = self.num_docs
            N00 = N - N01 - N10 - N11

        else:
            N11 = self.term_counts[t][(c, p)]

            # class but not term = all docs in class - docs where term appears
            N01 = self.class_freq[p][c] - N11

            # docs where term appears but not in class
            N10 = 0
            for other in CLASSES:
                if other != c:
                    N10 += self.term_counts[t][(other, p)]

            N = self.folds[p]["count"]
            N00 = N - N01 - N10 - N11

        epsilon = 0.05

        X = ((N11 + N10 + N01 + N00 + epsilon)*(N11*N00 - N10*N01 + epsilon)**2) / \
            ((N11 + N01 + epsilon)*(N11 + N10 + epsilon)*(N10 + N00 + epsilon)*(N01 + N00 + epsilon))

        return X

    def num_partitions(self):
        """ Returns the number of partitions in the training dataset. """
        return self.partitions
