# -----------------------------------------------------------------------
# Name: Veronica Salm
# CCID: vsalm
# File: evaluate_nb.py
#
# Description: Contains functions to report accuracy, precision, and
#              recall of the nb classifier.
#------------------------------------------------------------------------
import math, sys
from tabulate import tabulate

from naive_bayes.constants import CLASSES, TP, TN, FP, FN, HEADERS
from naive_bayes.train import get_zeros_entry

def accuracy(doc_idx, data, guess):
    """ Prints the classifier's guess and the correct answer
    to the terminal. """
    return data.get_relation(doc_idx) == guess


def get_class_scores(doc_idx, data, training_results):
    """
    Returns a dictionary mapping class names to their scores for
    the given document.
    """
    text = data.get_document_tokens(doc_idx)
    scores = dict()
    for c in CLASSES:
        scores[c] = 0

    # extract the vocabulary, prior probabilities, and conditional
    # probabilities from the training results
    vocab = training_results[0]
    prior = training_results[1]
    cond_prob = training_results[2]

    for c in CLASSES:
        # here, the base used is 2
        score = math.log(prior[c], 2)
        for t in text:
            # if this is a brand new term, do not add anything to the score, just the prior
            if t in cond_prob:
                score += math.log(cond_prob[t][c], 2)

        scores[c] = math.exp(score)

    # normalize the scores
    denom = sum([v for v in scores.values()])
    sorted_scores = []
    for c in sorted(CLASSES):
        scores[c] = scores[c]/denom
        sorted_scores.append(scores[c])

    # return the scores dictionary
    return scores, sorted_scores

def classify(doc_idx, data, training_results):
    """ Given an index into the list of documents, attempt
    to return the best class for the document.
    """
    text = data.get_document_tokens(doc_idx)

    # extract the vocabulary, prior probabilities, and conditional
    # probabilities from the training results
    vocab = training_results[0]
    prior = training_results[1]
    cond_prob = training_results[2]

    best_class = None
    best_score = -float('inf')
    for c in CLASSES:
        # here, the base used is 2
        score = math.log(prior[c], 2)
        for t in text:
            # compute the best possible matching class
            # if this is a brand new term, do not add anything to the score, just the prior
            if t in cond_prob:
                score += math.log(cond_prob[t][c], 2)

        # find the class that gives the best score
        if (score > best_score):
            best_score = score
            best_class = c

    # return the class that gave the best score overall
    return best_class

def get_accuracy(data, index_list, training_results):
    """ Given a DataManager object, a list of document indices,
    and the results of training the NB classifier, gathers and
    returns the accuracy of the model on the test dataset
    represented by index_list. """
    results = dict()
    # conf is the confusion matrix
    conf = dict()
    for c in CLASSES:
        results[c] = {TP: 0, TN: 0, FP: 0, FN: 0}
        conf[c] = dict()
        for c2 in CLASSES:
            conf[c][c2] = 0

    for i in index_list:
        # the true class of the document we are looking at
        true_class = data.get_relation(i)

        # let the classifier make a guess
        guess = classify(i, data, training_results)

        conf[true_class][guess] += 1

        # if classified correctly, should add one to tp
        for c in CLASSES:
            if c == true_class:
                if c == guess:
                    # increment tp for this class
                    results[c][TP] += 1

                else:
                    # c is the true class, but was not correctly guessed
                    # this is a false negative
                    results[c][FN] += 1

            else:
                if c == guess:
                    # guessed c but c is not the true class
                    results[c][FP] += 1

                else:
                    results[c][TN] += 1

    totals = {TP: 0, TN: 0, FP: 0, FN: 0}
    class_accuracies = dict()

    for c in CLASSES:
        # precision is defined as tp / (tp + fp)
        try:
            precision = results[c][TP] / (results[c][TP] + results[c][FP])
        except ZeroDivisionError:
            precision = None
        conf[c]["Precision"] = precision

        # recall is defined as tp / (tp + fn)
        try:
            recall = results[c][TP] / (results[c][TP] + results[c][FN])
        except ZeroDivisionError:
            recall = None
        conf[c]["Recall"] = recall

        # accuracy is defined as (tp + tn) / (tp + tn + fp + fn)
        accuracy = (results[c][TP] + results[c][TN]) / (results[c][TP] + results[c][TN] + results[c][FP]  + results[c][FN])

        # f1 is defined as (2 * precision * recall) / (precision + recall)
        try:
            f1 = (2 * precision * recall) / (precision + recall)
        except ZeroDivisionError:
            f1 = None
        except TypeError:
            f1 = None

        # store results in the entry for this class
        class_accuracies[c] = [precision, recall, accuracy, f1]

        totals[TP] += results[c][TP]
        totals[TN] += results[c][TN]
        totals[FP] += results[c][FP]
        totals[FN] += results[c][FN]

    # number of classes
    N = len(CLASSES)
    # compute overall (macroaveraged) precision, recall, and f1 values
    precision = 0
    recall = 0
    for c in CLASSES:
        if (results[c][TP] + results[c][FP]) > 0:
            precision += (results[c][TP] / (results[c][TP] + results[c][FP]))
        if (results[c][TP] + results[c][FN]) > 0:
            recall += (results[c][TP] / (results[c][TP] + results[c][FN]))

    recall /= N
    precision /= N
    f1 = (2 * precision * recall) / (precision + recall)

    # compute accuracy
    accuracy =  (totals[TP] + totals[TN]) / (totals[TP] + totals[TN] + totals[FP]  + totals[FN])
    overall = [precision, recall, accuracy, f1]

    return class_accuracies, overall, conf



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



def print_accuracy(class_accuracies, overall_accuracies):
    """ Outputs a table of accuracies for the NB classifier.

    For each class, the follwing is printed on a single line:
        c: the name of the class
        recall: tp / (tp + fn)
        precision: tp / (tp + fp)
        accuracy: (tp + tn) / (tp + tn + fp + fn)
        f1: (2 * precision * recall) / (precision + recall)

    Finally, the overall results are printed on the last line,
    with the class name replaced by the word "Overall".

    NOTE: If any of recall, precision, or f1 would result in
    a ZeroDivisionError, they are set to None, resulting in a
    blank space being printed instead of that value.
    """
    summaries = []
    for c in sorted(CLASSES):
        entry = [c]
        entry.extend(class_accuracies[c])
        summaries.append(entry)

    # overall recall, precision, accuracy, f1
    overall = ["OVERALL"]
    overall.extend(overall_accuracies)

    summaries.append(overall)

    print(tabulate(summaries, headers=HEADERS, floatfmt=".4f"))


def average_results(results):
    """ Takes a list of class and overall results for each partition
    and returns the average of each. """
    avg_class_results = dict()
    avg_overall = [0,0,0,0]

    for c in CLASSES:
        # each class will have precision, recall, accuracy, f1
        avg_class_results[c] = [0,0,0,0]

    # sum the results from all partitions
    for r in results:
        class_results = r[0]
        overall = r[1]

        for i in range(4):

            for c in CLASSES:

                try:
                    avg_class_results[c][i] += class_results[c][i]
                except TypeError:
                    # error because one of the operands was None
                    # ie, because of a 0/0 error for recall or precision
                    avg_class_results[c][i] = None

            try:
                avg_overall[i] += overall[i]
            except TypeError:
                avg_overall[i] = None

    # compute the average overall results by dividing by
    # the number of total partitions
    num_partitions = len(results)

    for i in range(4):
        for c in CLASSES:
            if avg_class_results[c][i] != None:
                avg_class_results[c][i] /= num_partitions

        if avg_overall != None:
            avg_overall[i] /= num_partitions

    # return the average results
    return avg_class_results, avg_overall
