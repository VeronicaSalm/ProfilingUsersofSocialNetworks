import csv

dirname = "results/"

fname = "canadians_april.tsv"

output = []
with open("all_canadians_from_filter.csv", "r") as fobj:
    reader = csv.reader(fobj, delimiter=",")
    canadian_users = set([row[0] for row in reader])
    print(len(canadian_users))

with open(dirname+fname, "r") as fobj:
    csv_reader = csv.reader(fobj, delimiter="\t")

    for row in csv_reader:
        if row[0] in canadian_users:
            output.append(row)

with open(dirname+"cleaned_"+fname, "w") as fobj:
    csv_writer = csv.writer(fobj)

    for row in output:
        csv_writer.writerow(row)

