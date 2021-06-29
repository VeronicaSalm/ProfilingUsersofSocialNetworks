# --------------------------------------------------------------------
# File: knn_classifier.py
#
# Description:
#
# Authors: Cole Mackenzie, Veronica Salm
# --------------------------------------------------------------------
import argparse, sys, os, csv
import logging
from collections import Counter, defaultdict

import numpy as np
from nltk.text import TextCollection
from tabulate import tabulate

from naive_bayes.DataManager import DataManager
from naive_bayes.constants import CLASSES,  HEADERS
from knn.knn_normalizer import normalize_text, normalize, tokenize
from naive_bayes.nb_classifier import k_fold_cross_validation
from naive_bayes.TrainingDataManager import TrainingDataManager
from naive_bayes.select_features import feature_selection_MI, feature_selection_freq, feature_selection_chi_square
from naive_bayes.evaluate_nb import get_accuracy, print_accuracy, print_confusion_matrix, average_results, get_class_scores
from naive_bayes.train import train

logging.basicConfig(level=logging.INFO)
logger = logging

import tensorflow_hub as hub
import tensorflow as tf
import numpy as np
from sentence_transformers import SentenceTransformer

import pickle
# TODO: Uncomment next line to revert to USE
embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
# Reduce logging output.
tf.logging.set_verbosity(tf.logging.ERROR)

session = tf.Session()
session.run([tf.global_variables_initializer(), tf.tables_initializer()])


def determine_class(neighbours, data_manager):
    """
    Uses simple voting majority to determine the class
    :param neighbours: a list neighbour tuples (sim, doc_id)
    :param data_manager: the truth data manager
    :return: str of the predicted class
    """
    neighbours_classes = []
    for neighbour in neighbours:
        index = neighbour[1]
        neighbours_classes.append(data_manager.get_relation(index))
    count = Counter(neighbours_classes)
    return max(count, key=count.get)


model = SentenceTransformer('bert-base-nli-mean-tokens')
def st_vectorize(text):
    embedding = model.encode(text)
    return embedding


def use_vectorize(text):
    """
    Creates a Bag of Words vector
    :param text: the input text
    :return: a dictionary mapping term: count in text
    """
    messages = [text]
    message_embeddings = session.run(embed(messages))
    for i, message_embedding in enumerate(np.array(message_embeddings).tolist()):
        return message_embedding

def tfidf_vectorizer(corpus):
    """
    Create tfidf vectors as a dictionary of term: tfidf value
    :param corpus: the corpus of all the training input
    :return:
    """
    corpus = [normalize(tokenize(doc)) for doc in corpus]
    collection = TextCollection(corpus)
    for doc in corpus:
        yield {term: collection.tf_idf(term, doc) for term in doc}


def sim(a_scores, target_scores):
    """
    Calculate the distance from a to target.
    :param a: dictionary mapping term: value
    :param target: dictionary mapping term: value
    :return: the distance from a to target
    """
    a_scores = np.array(a_scores, dtype=np.float64)
    target_scores = np.array(target_scores)
    return np.dot(a_scores, target_scores)  # / (np.linalg.norm(a_scores) * np.linalg.norm(target_scores))


def dist(a, target):
    """
    Return the distance using cosine similarity
    :param a: the input vector
    :param target: the target vector
    :return: the cosine distance
    """
    return 1.0 - sim(a, target)


def count_classes(data_manager):
    return Counter([data_manager.get_type(i) for i in range(len(data_manager))])


def confusion_matrix(results):
    """
    Create and return a confusion matrix and its labels.
    Rows are expected, columns are predicted
    https://en.wikipedia.org/wiki/Confusion_matrix
    :param results:
    :return:
    """
    classes = sorted(list(CLASSES))
    cm = np.zeros((len(classes), len(classes)))
    for expected, predicted in results:
        expected_index = classes.index(expected)
        predicted_index = classes.index(predicted)
        cm[predicted_index][expected_index] += 1
    return classes, cm


def reduce_cm(index, cm):
    """
    Reduce a confusion matrix on a specific index to the following
    https://en.wikipedia.org/wiki/Confusion_matrix
    +===============================+
    =            Class  | Not Class =
    +===============================+
    = Class     |  TP   |    FP     =
    = Not Class |  FN   |    TN     =
    +===============================+
    :param index:
    :return:
    """
    total = np.sum(cm)
    tp = cm[index][index]
    fp = np.sum(cm[:, index]) - cm[index][index]
    fn = np.sum(cm[index, :]) - cm[index][index]
    tn = total - (tp + fp + fn)
    result = {
        "tp": tp,
        "fp": fp,  # sum row minus self
        "fn": fn,  # sum column minus self
        "tn": tn,
        "total": total
    }
    return result

def print_results(results):
    """ Outputs the result table with precision, recall, f1, and
    accuracy for each class and overall.

    Note that f1 is the harmonic (balanced) measure of precision
    and recall. """
    labels, cm = confusion_matrix(results)
    summaries = []

    # tracked for computing overall precision, accuracy, recall, and f1
    totals = {"tp": 0, "tn": 0, "fn": 0, "fp": 0}

    # compute the accuracy measures for each class separately
    for index, cls in enumerate(labels):
        confusion_table = reduce_cm(index, cm)
        tp = confusion_table['tp']
        tn = confusion_table['tn']
        fp = confusion_table['fp']
        fn = confusion_table['fn']

        # also increment the overall counts
        totals["tp"] += tp
        totals["tn"] += tn
        totals["fn"] += fn
        totals["fp"] += fp

        # compute and add the row to the result table
        precision = tp / (tp + fp)
        recall = tp / (tp + fn)
        f1 = (2 * precision * recall) / (precision + recall)
        accuracy = (tp + tn) / (tp + tn + fp + fn)
        summaries.append([cls, precision, recall, accuracy, f1])

    # compute the overall measures and append the resulting row tp the table
    tp = totals["tp"]
    tn = totals["tn"]
    fn = totals["fn"]
    fp = totals["fp"]

    # number of classes
    N = len(CLASSES)
    # compute overall (macroaveraged) precision, recall, and f1 values
    precision = 0
    recall = 0
    for s in summaries:
        precision += s[1]
        recall += s[2]
    recall /= N
    precision /= N
    f1 = (2 * precision * recall) / (precision + recall)
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    summaries.append(["OVERALL", precision, recall, accuracy, f1])

    # print the result table
    print(tabulate(summaries, headers=HEADERS, floatfmt=".4f"))
    print()

def print_confusion_matrix(results):
    """
    Outputs a table of system output and gold labels.
    """
    classes = sorted(CLASSES)
    summaries = []
    for c in sorted(CLASSES):
        entry = [c]
        for c2 in sorted(CLASSES):
            entry.append(results[c][c2])
        summaries.append(entry)
    print(tabulate(summaries, headers=["Class"] + classes, floatfmt=".4f"))

def train_naive_bayes(train_path):
    # trains the NB classifier for hashtags
    num_partitions = 5
    select = [300, 0, -300] # num features
    training_data = TrainingDataManager(train_path, num_partitions, select != None)

    # do MI based feature selection
    k, features = feature_selection_MI(training_data, select)

    vocab, prior, cond_prob = train(training_data, features=features[training_data.num_partitions()])
    training_results = [vocab, prior, cond_prob]

    #  k_fold_cross_validation(training_data, num_partitions, features)
    return training_results

def main():
    # Set up for commandline argument parsing

    parser = argparse.ArgumentParser(
        description='Performs document classification using k-nearest neighbours and prints the resulting accuracy.'
    )

    parser.add_argument("training_set",
                        help="the json file containing the training data",
                        type=str)

    parser.add_argument("test_set",
                        help="the json file containing the test data",
                        type=str)

    parser.add_argument("-k",
                        required=False,
                        default=3,
                        type=int,
                        help="Use specified k instead of default")

    args = parser.parse_args()

    # set up the data manager for the training and test sets
    training = DataManager(args.training_set)
    test = DataManager(args.test_set)

    #  nb_training_results = train_naive_bayes(args.training_set)

    # Create a list of texts from the training data
    corpus = [normalize_text(training.get_tokens(i)) for i in range(len(training))]

    print("Word Embeddings")
    # For every text in the corpus, generate a BoW vector
    vectors = []

    for i, t in enumerate(corpus):
        tweet_id = training.get_id(i)
        print("Tweet #{}: {}".format(i, tweet_id))
        fname = "knn/tmp/{}.pickle".format(tweet_id)
        if not os.path.exists(fname):
            with open(fname, "wb") as f:
                pickle.dump(use_vectorize(t), f)
        vectors.append(fname)
    correct = 0.0
    total = len(test)
    results = []
    # get the confusion matrix results
    conf = dict()
    for c in CLASSES:
        conf[c] = dict()
        for c2 in CLASSES:
            conf[c][c2] = 0
    errors_obj = open("errors.csv", "w")
    err_writer = csv.writer(errors_obj)
    err_writer.writerow(["Text", "True Class", "Guessed Class"])
    for i in range(len(test)):
        tweet_id = test.get_id(i)
        print("Evaluating test file {} with tweet {}".format(i, tweet_id))
        expected_class = test.get_relation(i)
        out_name = "knn/test/{}.pickle".format(tweet_id)
        if not os.path.exists(out_name):
            # pickle the object and store it
            v = use_vectorize(normalize_text(test.get_tokens(i)))
            with open(out_name, "wb") as f:
                pickle.dump(v, f)
        else:
            # read the picked vector instead of recomputing it
            with open(out_name, "rb") as f:
                v = pickle.load(f)

        # Add info to vector from NB
        #  scores, sorted_scores = get_class_scores(i, test, nb_training_results)
        #  v.extend(sorted_scores)

        neighbours = []
        for index, fname in enumerate(vectors):  # go over every document and calculate sim
            with open(fname, "rb") as f:
                vector = pickle.load(f)
            neighbours.append((sim(v, vector), index))
        top_k = sorted(neighbours, key=lambda x: x[0], reverse=True)[:args.k]
        predicted_class = determine_class(top_k, training)
        if predicted_class == expected_class:
            correct += 1.0
        else:
            text = test.get_tokens(i)
            print(text)
            err_writer.writerow([text, expected_class, predicted_class])

        results.append((expected_class, predicted_class))
        conf[expected_class][predicted_class] += 1

    print_results(results)
    print_confusion_matrix(conf)
    errors_obj.close()


    #  # build vectors from training data
    #  text_collection = TextCollection(corpus)
    #  vectors = []
    #  for doc in corpus:
    #      tokens = normalize(tokenize(doc))
    #      vectors.append({term: text_collection.tf_idf(term, doc) for term in tokens})
    #
    #  # Compare against neighbours
    #  correct = 0.0
    #  total = len(test)
    #  results = []
    #  for i in range(len(test)):
    #      expected_class = test.get_relation(i)
    #      doc = test.get_tokens(i)
    #      v = {term: text_collection.tf_idf(term, doc) for term in test.get_document_tokens(i)}
    #      neighbours = []
    #      for index, vector in enumerate(vectors):  # go over every document and calculate sim
    #          neighbours.append((sim(v, vector), index))
    #      top_k = sorted(neighbours, key=lambda x: x[0], reverse=True)[:args.k]
    #      predicted_class = determine_class(top_k, training)
    #      if predicted_class == expected_class:
    #          correct += 1.0
    #      results.append((expected_class, predicted_class))
    #
    #  print_results(results)


if __name__ == "__main__":
    main()
