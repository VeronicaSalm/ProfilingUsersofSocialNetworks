# -----------------------------------------------------------------------
# Name: Veronica Salm
# CCID: vsalm
# File: normalizer.py
#
# Description: Contains functions for tokenizing and normalizing the
#              document text.
#--------------------------------------------------------------------

import string
import nltk
from nltk.stem import PorterStemmer, SnowballStemmer

stopwords = set(nltk.corpus.stopwords.words('english'))

def tokenize(text):
    """
    Return a list of tokens for the given input using NLTK word_tokenize
    Arguments:
        text: the input text
    Returns:
        tokens: a list of the tokens parsed from the text input
    """
    # from https://medium.com/@Intellica.AI/aspect-based-sentiment-analysis-everything-you-wanted-to-know-1be41572e238
    # remove urls
    text = text.replace(r'(https|http)?:\/(\w|\.|\/|\?|\=|\&|\%)*\b','')
    text = text.replace(r'www\.\S+\.com','')
    # remove user mentions
    text = text.replace(r'@\S+', '')
    tokens = nltk.word_tokenize(text)
    return tokens
    #  tokens = text.split()
    #  result = []
    #  for t in tokens:
    #      if t.startswith("#"):
    #          result.append(t)
    #  return result


def normalize(tokens):
    """
    Ensure all tokens are normalized.
    Our normalization consists of:
        - Case folding
        - Split on '|'
        - Remove all punctuation

    Arguments:
        tokens: a list of tokens

    Returns:
        result: a list of normalized tokens
    """
    stemmer = PorterStemmer()

    result = []
    punctuation_table = str.maketrans('', '', string.punctuation + "–—−—”“’‘,")  # https://stackoverflow.com/a/34294398

    # make hashtags special
    #  del punctuation_table[ord("#")]

    for t in tokens:
        t = t.lower()
        # remove punctuation and convert token to lowercase
        t = t.translate(punctuation_table)
        if not t:
            continue
        else:
            if t not in stopwords:
                t = stemmer.stem(t)
                result.append(t)


    # turn the tokens into bigrams before returning
    #  bigrams = []
    #
    #  for i in range(0, len(result)-1):
    #      bigrams.append(result[i] + " " + result[i+1])

    #  print(tokens)
    #  print(bigrams)
    #  import sys
    #  sys.exit()

    return result
    #  return bigrams
