"""Paths to all the resources needed to calculate features.

"""

LM_KN = [
    "hashtag_master/data/small_kn.bin"
]

LM_GT = [
    "hashtag_master/data/small_gt.bin" 
]

RESOURCES = {
    "lm_gt": LM_GT,
    "lm_kn": LM_KN,
    "wiki": "hashtag_master/data/wiki_titles.txt",
    "urban": "hashtag_master/data/urban_dict_words_A_Z.txt",
    "twitter": "hashtag_master/data/twitter_counts.tsv",
    "google":  "hashtag_master/data/google_counts.tsv",
}


def get_resources():
    return RESOURCES
