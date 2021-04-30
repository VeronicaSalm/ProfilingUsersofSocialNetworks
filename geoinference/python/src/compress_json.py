# Used to compress all tweet files, since the canadian tweets are given
# in uncompressed jsonl format.
# Assumes the tweets are in a folder called "canadians_april"
import os

for f in os.listdir("canadians_april"):
    path = os.path.join("canadians_april", f)
    os.system("gzip {}".format(path))

