# -----------------------------------------------------------------------
# Name: Veronica Salm
# CCID: vsalm
# File: test_hashtag_master.py
#
# A demo of the hashtag master as used in my code. Reads from an 
# input txt file of hashtags and writes the results to an output csv.
#--------------------------------------------------------------------

import string
import nltk
import re
import sys
import csv
import kenlm
from nltk.stem import PorterStemmer, SnowballStemmer
from hashtag_master.word_breaker.main import segment_word
from hashtag_master.neural_ranker.main import create_neural_ranking_model
from hashtag_master.neural_ranker.rerank import rerank

# For Hashtag Master
model_type = "mse_multi"
print("Loading language model.")
language_model = kenlm.LanguageModel("hashtag_master/data/small_gt.bin")
print("Done.")

print("Training Neural Ranking Model.")
neural_ranking_model, feature_extractor = create_neural_ranking_model(model_type)
print("Done")

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

def hashtag_demo(hashtag):
    """
    Runs the hashtag master model on the input hashtag (which does not start with
    a hashtag symbol).
    """
    # try replacing every instance of "covid" with "coronavirus"
    # these next three lines didn't help the classification accuracy
    #print(f"ORIGINAL HASHTAG: {t}")
    #insensitive_covid = re.compile(re.escape('covid'), re.IGNORECASE)
    #t = insensitive_covid.sub("Coronavirus", t)
    global language_model
    global neural_ranking_model
    top_k = 5
    candidates = segment_word(hashtag.lstrip("#"), 5, language_model)
    if len(candidates) > 1:
        # there are multiple candidates, run the reranking algorithm
        feats = get_features(candidates)
        # print(feats)
        reranked_segs = rerank(candidates, feats, neural_ranking_model, model_type)
        best = reranked_segs[0].split()
    elif len(candidates) == 1:
        best = candidates[0].split()
    else:
        print(t, candidates)
        raise Exception("Error, not enough candidates for hashtag '{}'!".format(hashtag))

    print(f"HASHTAG: {hashtag}", f"BEST: {best}")
    return best
        

if __name__ == "__main__":
    
    hashtags = []
    with open("hashtags.csv", "r") as fobj:
        reader = csv.reader(fobj)
    
        for row in reader:
            hashtags.append(row[0])
    
    with open("hashtag_master_results.csv", "w") as fobj:
        writer = csv.writer(fobj)

        for hashtag in hashtags:
            segmentation = hashtag_demo(hashtag)
            writer.writerow([hashtag, " ".join(segmentation)])

    print("Done processing all hashtags.")
            
