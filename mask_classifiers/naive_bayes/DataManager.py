# -----------------------------------------------------------------------
# Name: Veronica Salm
# CCID: vsalm
# File: DataManager.py
#
# Description: Reads and parses a json file, and manages the resulting
# 			   object.
#--------------------------------------------------------------------
import os, sys, csv

from naive_bayes.normalizer import normalize, tokenize

ROW_ID = 0
TOKENS = 1
RELATION = 2
LANGUAGE = 3

class DataManager():

    def __init__(self, input_path):
        #""" Read the index file from the current directory. Returns the index file object if successful. """

        # try to open the index file in the given directory
        try:
            file = open(input_path, encoding='utf-8')
        except FileNotFoundError:
            # if we get here, print an error message and quit
            print("Error: Could not find data file '{}'.".format(input_path))
            sys.exit();

        self.in_file = open(input_path, "r")
        self.in_reader = csv.reader(self.in_file, delimiter=",")

        # skip header
        self.header = next(self.in_reader)

        self.input_path = input_path
        self.data = []

        while True:
            try:
                r = next(self.in_reader)
                self.data.append(r)
            except StopIteration:
                break
        self._all_docs = None

    def _check_index(self, idx):
        """ Check that the given index is within a valid range,
        0 <= idx <= len(self.data) """
        if idx < 0 or idx >= len(self.data):
            print("Error: Attempted to index into '{}' out of bounds using index {}.".format(self.input_path, idx))
            sys.exit()

    def get_tokens(self, idx):
        """ Given an index 0 <= idx < len(data), return the text (tokens)
        of the data at that position. """
        self._check_index(idx)
        print(self.data[idx][TOKENS])
        return self.data[idx][TOKENS]

    def get_language(self, idx):
        """ Given an index 0 <= idx < len(data), return the language
        of the tweet at that position. """
        self._check_index(idx)
        return self.data[idx][LANGUAGE]

    def get_id(self, idx):
        """ Given an index 0 <= idx < len(data), return the id
        of the data at that position. """
        self._check_index(idx)
        return self.data[idx][ROW_ID]

    def get_relation(self, idx):
        """ Given an index 0 <= idx < len(data), return the relation (label)
        of the data at that position. """
        self._check_index(idx)
        return self.data[idx][RELATION]

    def get_document_tokens(self, idx, p=None):
        """ Return all normalized tokens from the document represented by the given
        index. """
        return normalize(tokenize(self.get_tokens(idx)))

    def num_docs_in_corpus(self):
        """ Returns the number of documents in the data set."""
        return len(self.data)

    def all_tokens(self):
        tokens = []
        for i in range(self.num_docs_in_corpus()):
            tokens += self.get_document_tokens(i)
        return tokens

    def all_docs(self):
        if self._all_docs:
            return self._all_docs
        else:
            docs = []
            for i in range(self.num_docs_in_corpus()):
                docs.append(self.get_document_tokens(i))
            self._all_docs = docs
            return self.all_docs()

    def __len__(self):
        return self.num_docs_in_corpus()
