# -----------------------------------------------------------------------
# Name: Veronica Salm
# CCID: vsalm
# File: normalize.py
#
# Contains methods to normalize and tokenize Twitter text.
#--------------------------------------------------------------------

import string
import nltk
import re
import sys
import kenlm
from nltk.stem import PorterStemmer, SnowballStemmer
from hashtag_master.word_breaker.main import segment_word
from hashtag_master.neural_ranker.main import create_neural_ranking_model
from hashtag_master.neural_ranker.rerank import rerank

stopwords = set(nltk.corpus.stopwords.words('english')) - {"no", "not", "doesn"}


# For Hashtag Master
#  model_type = "mse_multi"
#  print("Loading language model.")
#  language_model = kenlm.LanguageModel("hashtag_master/data/small_gt.bin")
#  print("Done.")
#
#  print("Training Neural Ranking Model.")
#  neural_ranking_model, feature_extractor = create_neural_ranking_model(model_type)
#  print("Done")

def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]

def get_features(candidates):
    """
    Extracts the feature vector for the candidate segmentations.
    """
    global feature_extractor
    best_cand = candidates[0]
    feats = []
    for seg in candidates:
        fv = feature_extractor._get_features_for_segmentation(seg, best_cand)
        feats.append(fv)
    return feats

def normalize_text(text):
    """
    Normalizes the string represented by text, and returns another string.
    """
    tokens = tokenize(text)

    cleaned = []
    for t in tokens:
        if t.startswith("#") and len(t) > 1:
            continue
            # try replacing every instance of "covid" with "coronavirus"
            words = camel_case_split(t.lstrip("#"))
            global language_model
            global neural_ranking_model
            candidates = segment_word(t.lstrip("#"), 5, language_model)
            if len(candidates) > 1:
                # there are multiple candidates, run the reranking algorithm
                feats = get_features(candidates)
                reranked_segs = rerank(candidates, feats, neural_ranking_model, model_type)
                best = reranked_segs[0].split()
            elif len(candidates) == 1:
                best = candidates[0].split()
            else:
                print(t, candidates)
                raise Exception("Error, not enough candidates for hashtag '{}'!".format(t))

            # print(f"HASHTAG: {t}", f"BEST: {best}", f"CAMELCASE SPLIT: {words}")
            cleaned.extend(best)
        else:
            cleaned.append(t)
    cleaned = normalize(cleaned)
    text = " ".join(cleaned)
    return text

def tokenize(text):
    """
    Return a list of tokens for the given input using NLTK word_tokenize
    Arguments:
        text: the input text
    Returns:
        tokens: a list of the tokens parsed from the text input
    """
    # remove urls
    text = text + " www.helloworld.com"
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    # remove user mentions
    # text = text.replace(r'@\S+', '')
    tokens = text.split()
    return tokens


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
    del punctuation_table[ord("#")]

    for t in tokens:
        t = t.lower()
        # remove punctuation and convert token to lowercase
        t = t.translate(punctuation_table)
        if not t:
            continue
        else:
            if t not in stopwords:
                #  t = stemmer.stem(t)
                result.append(t)

    return result
