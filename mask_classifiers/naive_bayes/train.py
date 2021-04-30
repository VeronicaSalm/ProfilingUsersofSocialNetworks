# -----------------------------------------------------------------------
# Name: Veronica Salm
# CCID: vsalm
# File: train.py
#
# Description: Contains communal functions needed for training.
#------------------------------------------------------------------------

from naive_bayes.constants import CLASSES

def get_ones_entry():
	""" Initialize an empty dictionary with the count for each class
	set to 1. """
	entry = dict()
	for c in CLASSES:
		# note that we start all counts at 1 to perform
		# "add one" or Laplace smoothing
		entry[c] = 1
	return entry

def get_zeros_entry():
	""" Initialize an empty dictionary with the count for each class
	set to 0. """
	entry = dict()
	for c in CLASSES:
		# note that we start all counts at 1 to perform
		# "add one" or Laplace smoothing
		entry[c] = 0
	return entry

def print_counts(terms, c):
	""" Print the count of each term in the dictionary for a given
	class, for testing. """
	for t in terms:
		print("{}: {}".format(t, terms[t][c]))

def sum_entry(entry):
	""" Count the number of occurrences of this term across all
	documents. """
	res = 0
	for c, count in entry:
		res += count
	return res


def train(data, validation=None, features=None):
	""" Trains the NB classifier on the training data set data.

	If validation is present, it indicates which partition to leave
	out for k-fold cross-validation. """
	# maps each term to a count of how many times it occurs in each class
	terms = dict()

	# a dictionary of prior probabilities of class c
	prior = dict()

	# for each class, will track the number of term occurrences in the class
	# (ie, total number of tokens)
	# starts as an empty entry with a 1 for each class
	terms_in_class = get_zeros_entry()
	for c in CLASSES:
		prior[c] = data.prior_class_frequency(c, validation)
		text = data.all_text_in_class(c, validation)
		for doc in text:
			for t in doc:

				# skip terms we are excluding by feature selection
				if features != None:
					if t not in features[c]:
						continue


				if t not in terms:
					terms[t] = get_ones_entry()

				# increment the count of this term for this class
				terms[t][c] += 1

				# increment the count of all terms in the class
				terms_in_class[c] += 1


	# add the vocabulary size to each entry to avoid zeros (smoothing)
	vocab_size = len(terms)
	for c, val in terms_in_class.items():
		terms_in_class[c] += vocab_size

	# compute conditional probabilities
	cond_prob = dict()
	for t, entry in terms.items():
		cond_prob[t] = get_ones_entry()

		for c in CLASSES:
			cond_prob[t][c] = entry[c] / terms_in_class[c]

	# extract only the words of the vocabulary (no longer need terms)
	vocab = [t for t in terms]
	return vocab, prior, cond_prob
