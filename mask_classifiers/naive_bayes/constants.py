# -----------------------------------------------------------------------
# Name: Veronica Salm
# CCID: vsalm
# File: constants.py
#
# Description: Contains constants representing terms in the training
#              and test datasets.
#--------------------------------------------------------------------

PRO_MASK = "Pro-Mask"
NEUTRAL= "Neutral"
NOT_SURE = "Not Sure"
ANTI_MASK = "Anti-Mask"
UNRELATED = "Unrelated"
CLASSES = {PRO_MASK, NEUTRAL, NOT_SURE, ANTI_MASK, UNRELATED}
TP = "tp"
FP = "fp"
FN = "fn"
TN = "tn"
HEADERS = ['Class', 'Precision', 'Recall', 'Accuracy', 'F1']
