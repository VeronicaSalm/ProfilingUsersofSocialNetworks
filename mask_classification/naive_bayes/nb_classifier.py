# -----------------------------------------------------------------------
# Name: Veronica Salm
# CCID: vsalm
# File: nb_classifier.py
#
# Description: Trains a Naive-Bayes classifier on the provided training
#              data using feature selection and 10-fold cross validation.
#------------------------------------------------------------------------
import argparse, json, sys

from naive_bayes.DataManager import DataManager
from naive_bayes.TrainingDataManager import TrainingDataManager
from naive_bayes.OutputManager import OutputFileManager
from naive_bayes.select_features import feature_selection_MI, feature_selection_freq, feature_selection_chi_square
from naive_bayes.evaluate_nb import get_accuracy, print_accuracy, print_confusion_matrix, average_results
from naive_bayes.train import train
from naive_bayes.constants import CLASSES


# Set up for commandline argument parsing
parser = argparse.ArgumentParser(
    description='Performs document classification using Naive Bayes and prints the resulting accuracy.'
    )

parser.add_argument('--train_path', type=str, nargs='?', default = "data/train.csv",
                    help='the path to the training file, defaults to data/train.csv')
parser.add_argument('--test_path', type=str, nargs='?', default ="data/test.csv",
                    help='the path to the test data file, defaults to data/test.csv')
parser.add_argument('--dev_path', type=str, nargs='?', default ="data/dev.csv",
                    help='the path to the development data file, defaults to data/dev.csv')
parser.add_argument('--out_dir', type=str, nargs='?', default="output/",
                    help='the path to the directory where the output should be stored, defaults to output/')

parser.add_argument("--skip", "--skip_validation",
                    help="if present, the program will not do 10-fold cross validation and will only generate the full classifier",
                    action="store_true")

parser.add_argument("--select", "--select_features",
                    nargs="+",
                    help="""If present, feature selection will be performed.
                    Usage: "--select [mi|freq|chi] start end step",
                    where start, end, and step are integers. To run feature selection
                    with only one value of k, end and step can be omitted.""")

def k_fold_cross_validation(data, k, features=None):
    """ Perform k-fold cross validation on the provided dataset. This
    function will train the NB classifier on k-1 folds and print the
    accuracy on the remaining fold.

    features: a list of terms previously selected by feature selection.
              Only these terms will be included for training.
    """
    results = []

    for v in range(k):
        print("Training using fold {} for validation...".format(v))
        # each time, train using all partitions but v
        training_results = train(data, validation=v, features=features[v])

        # get the indices of documents in the validation set for testing
        validation_set = data.get_shuffled_indices(v)

        # print the accuracy on the left-over validation set
        print("Testing on fold {}...".format(v))
        class_accuracies, overall_accuracy, totals = get_accuracy(data, validation_set, training_results)
        print_accuracy(class_accuracies, overall_accuracy)
        print_confusion_matrix(totals)
        print()

        # store the results for averaging later
        results.append((class_accuracies, overall_accuracy))

    # print the average accuracies at the end
    avg_class_results, avg_overall_results = average_results(results)
    print("Average Results (over all folds):")
    print_accuracy(avg_class_results, avg_overall_results)
    print()

def error_handle(select):
    """ Handles errors when setting up feature selection arguments.

    There must be either:
        - One integer, the single k value (number of features) to
        test using feature selection.
        - Three integers: first bound, second bound, and step,
        where feature selection will iterate from the first bound to
        the second using the value of step. This error handling
        function automatically adjusts the sign of the step value if
        needed. For example, if first bound > second bound, step will be
        made negative if needed.
    """
    selection_type = select[0].lower()

    if selection_type not in ["mi", "freq", "chi"]:
        print("Error: You must specify a valid feature selection utility type. This must be one of")
        print("\t'mi': mutual information")
        print("\t'freq': frequency based")
        print("\t'chi': chi squared")
        sys.exit()
    # one parameter
    if len(select) == 2:
        try:
            # convert to integer
            select[1] = int(select[1])
        except ValueError:
            print("Error: the feature selection parameter must be an integer.")
            sys.exit()

        if select[1] < 0:
            print("Error: start and end parameters must be non-negative integers.")
            sys.exit()

        # artificially add extra parameters so that the selection
        # will only happen with one value of k = select[1]
        # ie, for k in range(select[1], 0, -select[1])
        parameters = [select[1]]
        parameters.append(0)
        parameters.append(-select[1])

    else:
        if len(select) != 4:
            print("Error: You must specify either one or three additional parameters for feature selection,")
            print("\t1. first bound: the number at which to begin feature selection")
            print("\t(2.) second bound: the number at which to stop (NOT included)")
            print("\t(3.) step: the interval by which to increment or decrement k")
            sys.exit()

        try:
            # convert to integer
            for i in range(1, len(select)):
                select[i] = int(select[i])

        except ValueError:
            print("Error: all feature selection parameters must be integers.")
            sys.exit()

        if select[1] < 0 or select[2] < 0:
            print("Error: start and end parameters must be non-negative integers.")
            sys.exit()

        # adjust sign if needed
        parameters = select[1:]
        if parameters[0] > parameters[1] and parameters[2] > 0:
            parameters[2] = -parameters[2]
        elif parameters[0] < parameters[1] and parameters[2] < 0:
            parameters[2] = - parameters[2]

    return selection_type, parameters

if __name__ == "__main__":
    #------------------------------------------------------
    # PARSE COMMAND LINE ARGS
    #------------------------------------------------------
    args = parser.parse_args()
    # number of folds for cross validation
    num_partitions = 5

    if args.select:
        # error handling on feature selection parameters
        selection_type, args.select = error_handle(args.select)

    #------------------------------------------------------
    # PARSE TRAIN AND TEST FILES
    #------------------------------------------------------
    # set up the data manager for the training and test sets
    training_data = TrainingDataManager(args.train_path, num_partitions, args.select != None)
    test_data = DataManager(args.test_path)

    #  print(training_data.vocab_size)
    #  sys.exit()

    #------------------------------------------------------
    # FEATURE SELECTION
    #------------------------------------------------------
    if args.select:
        # run feature selection using the selected algorithm
        if selection_type == "mi":
            k, features = feature_selection_MI(training_data, args.select)
            name = "mutual information"
        elif selection_type == "freq":
            k, features = feature_selection_freq(training_data, args.select)
            name = "frequency"
        else:
            k, features = feature_selection_chi_square(training_data, args.select)
            name = "chi square"

        print("\nBest k features found using the {} utility measure: {}\n".format(name, k))

        # store the best features found for later
        # note: final "partition" is actually the entire training set
        for p in range(num_partitions+1):
            for c in CLASSES:
                features[p][c] = list(features[p][c])
        with open("features.json", "w") as f:
            # writes the index nicely formatted for viewing
            f.write(json.dumps(features, indent=2, sort_keys=True))

    #------------------------------------------------------
    # RETRIEVE BEST FEATURES
    #------------------------------------------------------
    try:
        # try to extract best features from the feature file
        print("Attempting to load best features...", end=" ")
        feature_file = open("features.json")
        features = json.load(feature_file)

        print("Loaded from 'features.json'.\n")

        # prep the feature map for each class
        for p in range(num_partitions+1):
            for c in CLASSES:
                features[p][c] = set(features[p][c])
    except FileNotFoundError:
        # if no feature file is found, set features to None
        # this means all features will be included for classification
        print("No features found, proceeding without feature selection.\n")
        features = None

    #------------------------------------------------------
    # TRAIN CLASSIFIER ON TRAINING SET
    #------------------------------------------------------
    vocab, prior, cond_prob = train(training_data, features=features[training_data.num_partitions()])
    training_results = [vocab, prior, cond_prob]

    #------------------------------------------------------
    # K FOLD CROSS VALIDATION
    #------------------------------------------------------
    if not args.skip:
        # perform 3-fold cross validation
        print("Performing {}-fold cross validation...".format(num_partitions))
        k_fold_cross_validation(training_data, num_partitions, features)

    #------------------------------------------------------
    # EVALUATE CLASSIFIER ON TEST SET
    #------------------------------------------------------
    print("Test Set Accuracy:")
    indices = [i for i in range(test_data.num_docs_in_corpus())]
    class_accuracies, overall_accuracies, totals = get_accuracy(test_data, indices, training_results)
    print_accuracy(class_accuracies, overall_accuracies)
    print_confusion_matrix(totals)

    print("\nBest number of features found using the {} utility measure: {}\n".format(name, k))
