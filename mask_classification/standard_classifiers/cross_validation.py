import csv, random, sys

ROUND_ROBIN = 0
RANDOM = 1
SPLIT = 2
EVEN_CLASS_SPLIT = 3

class DataManagerCV:
    def __init__(self, data_paths):
        """
        Arguments:
            data_paths (list): a list of all paths in which relevant data is stored.
                               Data from all paths will be concatenated and used to
                               generate folds.
        """
        self.__data = []

        self.data_paths = data_paths

        for data_path in self.data_paths:
            try:
                data_file = open(data_path, encoding='utf-8')
            except FileNotFoundError:
                # if we get here, print an error message and quit
                print("Error: Could not find data file '{}'.".format(data_path))
                sys.exit();

            data_reader = csv.reader(data_file, delimiter=",")
            header = next(data_reader)
            cnt = 0
            while True:
                try:
                    r = next(data_reader)
                    self.__data.append(r)
                    cnt += 1
                except StopIteration:
                    break
            print(f"Loaded {cnt} documents from {data_path}.")

        # There are no folds until self.divide_into_folds(k) is called
        self.__folds = None
        self.__num_folds = None
        self.__validation = None

        print(f"Loaded {len(self.__data)} total documents.")

    def get_train_data(self):
        """
        Get all data (text and labels) from the num_folds-1 folds that
        represent the training data. Excludes the validation set.

        Returns:
            (list): the list of training data points from all folds except validation.
        """
        if self.__num_folds == None:
            raise Exception(self.__no_folds_exception_msg)
        data = []
        for f in range(self.__num_folds):
            if f == self.__validation:
                # skip the validation set
                continue
            # if this is not the validation fold, extract all its training data
            data.extend([self.__data[self.__folds[f][i]] for i in range(len(self.__folds[f]))])
        return data


    def get_validation_data(self):
        """
        Get all data (text and labels) from the validation fold.

        Returns:
            (list): the list of training data points from the validation fold.
        """
        if self.__num_folds == None:
            raise Exception(self.__no_folds_exception_msg)

        f = self.__validation
        return [self.__data[self.__folds[f][i]] for i in range(len(self.__folds[f]))]


    def set_validation(self, idx):
        """
        Set the validation set to the fold indicated by idx.

        Arguments:
            - idx (int): 0 <= idx < self.__num_folds, the index of the new validation fold
        """
        if self.__num_folds == None:
            raise Exception(self.__no_folds_exception_msg)
        if not (0 <= idx < self.__num_folds):
            raise ValueError("The validation set index must be in the range [0, k), where k is the number of folds.")
        self.__validation = idx


    def get_num_folds(self):
        """
        Returns the number of folds.
        """
        if self.__num_folds == None:
            raise Exception(self.__no_folds_exception_msg)
        return self.__num_folds


    def __partition(self, lst, n):
        """
        Partition the list lst into n roughly equal parts.

        Arguments:
            lst (list): the list to partition
            n (int): n >= 2, the number of parts to divide lst into

        Returns:
            (list): the list of lists representing the partitions
        """
        # Ensure that the number of parts is at least 2
        assert(n >= 2)
        # From: https://stackoverflow.com/questions/3352737/how-to-randomly-partition-a-list-into-n-nearly-equal-parts
        division = len(lst) / float(n)
        return [ lst[int(round(division * i)): int(round(division * (i + 1)))] for i in range(n) ]

    def seed(self, s):
        """
        Seed the manager using s, so that the results of the random fold
        division mode can be reproduced.
        """
        random.seed(s)


    def divide_into_folds(self, k, mode=RANDOM):
        """
        Divide the training data into k folds.

        Arguments:
            k (int): k >= 2, the number of folds to create
            mode (int): one of three possible modes,
                ROUND_ROBIN (0): assign points to folds in round-robin order
                RANDOM (1): randomly assign training points to folds
                SPLIT (2): divide the training data into partitions using the
                                existing order of the training data to create the
                                split points
                EVEN_CLASS_SPLIT (3): divide the data into folds, ensuring an even distribution
                                      of classes in each fold.
                All three modes attempt to divide the datapoints as evenly as possible.
        """
        if mode not in {ROUND_ROBIN, RANDOM, SPLIT}:
            exception_msg = "Invalid mode value provided for division of training data into folds for cross validation.\n"
            exception_msg += f"Please use one of ROUND_ROBIN={ROUND_ROBIN}, RANDOM={RANDOM}, SPLIT={SPLIT}, EVEN_CLASS_SPLIT={EVEN_CLASS_SPLIT}."
            raise Exception(exception_msg)

        # we have k folds, and currently the first fold is our validation set
        self.__num_folds = k
        self.__validation = 0

        # folds are stored as a list of lists
        # the ith fold is a list of indices to training elements
        # this is done rather than shuffling the documents themselves, as it's likely faster
        # not to store and pass around copies of long documents
        if mode == ROUND_ROBIN:
            # assign the ith datapoint to fold i%k
            self.__folds = [[] for i in range(k)]
            for i in range(len(self.__data)):
                self.__folds[i%k].append(i)
        elif mode == RANDOM:
            # First shuffle the list randomly, then partition
            indices = list(range(len(self.__data)))
            random.shuffle(indices)
            self.__folds = self.__partition(indices, k)
        elif mode == SPLIT:
            # simply partition the list without shuffling
            indices = list(range(len(self.__data)))
            self.__folds = self.__partition(indices, k)
        elif mode == EVEN_CLASS_SPLIT:
            pass


if __name__ == "__main__":
    dm = DataManagerCV(["data/train.csv", "data/test.csv"])
    dm.seed(42)
    dm.divide_into_folds(10)
    print(len(dm.get_train_data()))
    print(len(dm.get_validation_data()))


