"""
File: OutputManager.py
Name: Veronica Salm
CCID: vsalm

Manages writing results to the output file.
"""
import os, sys, csv

class OutputFileManager:
    def __init__(self, test_path, out_dir):
        """
        out_path (string): the path to the output .txt file
        """
        # Construct the output filename using the test path
        self.out_fname = "output_" + test_path.split("/")[-1]

        # create the path by joining with the output directory
        self.out_path = os.path.join(out_dir, self.out_fname)

        self.out_file = open(self.out_path, "w")

    def close_output(self):
        """
        Ensure that the CSV file is flushed properly.
        """
        self.out_file.close()

    def write(self, true_label, my_label, row_id):
        """
        Writes a result to the output file.
        Arguments:
            true_label: the original label
            my_label: the label assigned by the classifier
            row_id: the id of the testcase
        """
        self.out_file.write([true_label, my_label, row_id])
