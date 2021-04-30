import os, sys, csv, random
from collections import defaultdict

if __name__ == "__main__":
    in_dir = "data_unprocessed"

    # cnt counts the number of total documents, tr_cnt is the number
    # of training documents
    cnt = 0
    tr_cnt = 0
    sent = defaultdict(int)
    lang = defaultdict(int)
    rows = dict()
    for f in os.listdir(in_dir):
        fpath = os.path.join(in_dir, f)
        print("Reading {}...".format(f))
        with open(fpath, "r") as fobj:
            reader = csv.reader(fobj, delimiter=",")
            try:
                reader.__next__() # skip headers
            except StopIteration:
                continue
            for row in reader:
                if len(row) < 4:
                    print("Invalid number of columns!")
                    print(row)
                    sys.exit()
                # check that all relevant values are filled
                if len(row[1]) and len(row[2]) and len(row[3]) and len(row[0]):
                    sent[row[2]] += 1
                    lang[row[3]] += 1
                    if row[2] not in rows:
                        rows[row[2]] = {tuple(row)}
                    else:
                        rows[row[2]].add(tuple(row))

    # The destination files (and csv writers) for the train and test data.
    dest = "data/train.csv"
    fdest = open(dest, "w")
    train_writer = csv.writer(fdest)

    # Note, to change the test data, this code would need to be replaced
    # with a writer to the test file.
    test = "data/test.csv"
    ftest = open(test, "r")
    test_reader = csv.reader(ftest, delimiter=",")

    test = set()

    # Get the test IDs from the test file - don't overwrite them
    try:
        test_reader.__next__() # skip headers
    except StopIteration:
        print("Unable to read headers!")
        sys.exit()
    for row in test_reader:
        test.add(row[0])
        cnt += 1

    ### Code to randomly sample test ids... commented out as we
    ### have fixed test data.
    #  n = 25
    #  for k in rows.keys():
    #      sample = random.sample(rows[k], n)
    #      for s in sample:
    #          # id
    #          test.add(s[0])
    #  test_writer.writerow(["Tweet ID","Full Text","Mask Sentiment","Language"])
    train_writer.writerow(["Tweet ID","Full Text","Mask Sentiment","Language"])
    for k in rows.keys():
        for row in rows[k]:
            if row[0] not in test:
                train_writer.writerow(row)
                tr_cnt += 1
            #  else:
            #      test_writer.writerow(row)
    print("Total Docs: {}".format(cnt+tr_cnt))
    print("Train:", tr_cnt)
    print("Test:", cnt)
    print("Stats:")
    print(lang)
    print(sent)

    print(rows.keys())
