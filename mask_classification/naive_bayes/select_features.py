# -----------------------------------------------------------------------
# Name: Veronica Salm
# CCID: vsalm
# File: select_features.py
#
# Description: Called by nb_classifier.py to perform feature selection
#------------------------------------------------------------------------
import heapq
import json

from naive_bayes.constants import CLASSES
from naive_bayes.train import train, get_zeros_entry
from naive_bayes.evaluate_nb import get_accuracy


def mutual_information(data, class_name, t, p=None):
    """ Computes the mutual information score for a term and class.
    Also takes the current fold to consider only documents currently
    used for training. """
    return data.mutual_information(t, class_name, p)

def chi_square(data, class_name, t, p=None):
    """ Computes the chi square score for a term and class. """
    return data.chi_square_score(t, class_name, p)

def select_features(data, utility, p=None):
    """ Returns a dictionary mapping each class to all terms
    according to the given utility measure. """
    V = data.get_vocabulary()
    scores = dict()

    for c in CLASSES:
        scores[c] = []

        for t in V:
            # print_debug("\tClass {}, Term '{}'".format(c, t))
            score = utility(data, c, t, p)
            scores[c].append((score, t))

    return scores

def get_scores(data, utility, filename):
    """ Retrieve the scores for a given utility measure. This is only done if the
    file has not already been generated. """
    partition_scores = []

    # for each partition
    for p in range(data.num_partitions()):
        print("Partition {}...".format(p))

        scores = select_features(data, utility, p)

        partition_scores.append(scores)

    # get overall scores
    scores = select_features(data, utility, p=None)
    partition_scores.append(scores)

    with open(filename, "w") as f:
        # writes the index nicely formatted for viewing
        f.write(json.dumps(partition_scores, indent=2, sort_keys=True))

    return partition_scores

def feature_selection_MI(data, parameters):
    """ Iterative feature selection using mutual information as the
    utility measure. Returns the best k and best k features found. """
    #  try:
    #      # attempt to extract previously computed scores
    #      print("Checking for score file... ", end="")
    #      score_file = open("mutual_info_scores.json")
    #      partition_scores = json.load(score_file)
    #      print("score file loaded.")
    #
    #  except FileNotFoundError:
    #      # no file available, compute and store scores
    #      print("Score file not found. Creating scores...")
    partition_scores = get_scores(data, mutual_information, "mutual_info_scores.json")

    return iterative_feature_selection(data, parameters, partition_scores)

def feature_selection_freq(data, parameters):
    """ Runs feature selection on the given dataset using the given parameters,
    using frequency based scoring. """
    try:
        # attempt to extract previously computed scores
        print("Checking for score file... ", end="")
        score_file = open("frequency_scores.json")
        partition_scores = json.load(score_file)
        print("score file loaded.")

    except FileNotFoundError:
        # no file available, compute and store scores
        print("Score file not found. Creating scores...")
        partition_scores = []

        for p in range(data.num_partitions()):
            print("Partition {}...".format(p))

            scores = dict()

            for c in CLASSES:
                scores[c] = data.frequency_scores(c, p)

            partition_scores.append(scores)

        # compute frequency scores for full dataset
        scores = dict()
        for c in CLASSES:
            scores[c] = data.frequency_scores(c, None)
        partition_scores.append(scores)


        with open("frequency_scores.json", "w") as f:
            # writes the index nicely formatted for viewing
            f.write(json.dumps(partition_scores, indent=2, sort_keys=True))

    return iterative_feature_selection(data, parameters, partition_scores)

def feature_selection_chi_square(data, parameters):
    """ Runs feature selection on the given dataset using the given parameters,
    using chi square based scoring. """
    try:
        # attempt to extract previously computed scores
        print("Checking for score file... ", end="")
        score_file = open("chi_square_scores.json")
        partition_scores = json.load(score_file)
        print("score file loaded.")

    except FileNotFoundError:
        # no file available, compute and store scores
        print("Score file not found. Creating scores...")
        partition_scores = get_scores(data, chi_square, "chi_square_scores.json")

    return iterative_feature_selection(data, parameters, partition_scores)

def iterative_feature_selection(data, parameters, partition_scores):
    """ Iterates from the start to end value of k and decreases each time
    by step, all of which are specified in the given parameters.

    Also takes the scores for each partition (including the training set
    overall) and an instance of the training data manager class.

    Returns the best k from the range of k values considered, along
    with the features (terms) extracted using that best k.
    """
    best_k = -1
    best_features = dict()
    best_overall_accuracy = -1

    print("Selecting features...")
    for k in range(parameters[0], parameters[1], parameters[2]):

        print("\nTrying k = {}:".format(k))

        avg_overall_accuracy = 0

        all_features = []

        for p in range(data.num_partitions()):
            # get best k scores

            partition_features = dict()

            for c in CLASSES:
                partition_features[c] = set()
                scores = heapq.nlargest(k, partition_scores[p][c])

                # extract the tokens corresponding to the best scores
                for s in scores:
                    partition_features[c].add(s[1])

            # train classifier on only this partition, get the accuracy
            training_results = train(data, p, partition_features)

            all_features.append(partition_features)

            # get the indices of documents in the validation set for testing
            validation_set = data.get_shuffled_indices(p)

            # print the accuracy on the left-over validation set
            print("Testing on fold {} with k={}...".format(p, k))
            class_accuracies, total_accuracy, totals = get_accuracy(data, validation_set, training_results)

            avg_overall_accuracy += total_accuracy[2]

        avg_overall_accuracy /= data.num_partitions()

        print("Average overall accuracy with k={}: {}".format(k, avg_overall_accuracy))

        if avg_overall_accuracy > best_overall_accuracy:
            best_k = k
            # add the overall features in addition to the others given
            features = dict()
            for c in CLASSES:
                features[c] = set()
                scores = heapq.nlargest(k, partition_scores[data.num_partitions()][c])

                # extract the tokens corresponding to the best scores
                for s in scores:
                    features[c].add(s[1])
            all_features.append(features)

            best_features = all_features
            best_overall_accuracy = avg_overall_accuracy
            print("New overall best!")

    return best_k, best_features
