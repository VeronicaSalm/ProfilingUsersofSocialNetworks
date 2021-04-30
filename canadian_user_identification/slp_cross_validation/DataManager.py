import csv, random
import settings

class DataManagerCrossValidation:
    def __init__(self):
        self.__data = []

        # There are no folds until self.divide_into_folds(k) is called
        self.__folds = None
        self.__num_folds = None
        self.__validation = None

        with open("canadian_users.tsv", "r") as fobj:
            csv_reader = csv.reader(fobj, delimiter="\t")

            for row in csv_reader:
                self.__data.append([row[0], [row[1], row[2]]])

        print(len(self.__data))
        print(self.__data[0])

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


    def divide_into_folds(self, k, mode=settings.ROUND_ROBIN):
        """
        Divide the training data into k folds.

        Arguments:
            k (int): k >= 2, the number of folds to create
            mode (int): one of three possible modes,
                ROUND_ROBIN (0): assign points to folds in round-robin order
                RANDOM (1): randomly assign training points to folds
                EVEN_SPLIT (2): divide the training data into partitions using the
                                existing order of the training data to create the
                                split points
                All three modes attempt to divide the datapoints as evenly as possible.
        """
        if mode not in {settings.ROUND_ROBIN, settings.RANDOM, settings.EVEN_SPLIT}:
            exception_msg = "Invalid mode value provided for division of training data into folds for cross validation.\n"
            exception_msg += f"Please use one of ROUND_ROBIN={settings.ROUND_ROBIN}, RANDOM={settings.RANDOM}, or EVEN_SPLIT={settings.EVEN_SPLIT}."
            raise Exception(exception_msg)

        # we have k folds, and currently the first fold is our validation set
        self.__num_folds = k
        self.__validation = 0

        # folds are stored as a list of lists
        # the ith fold is a list of indices to training elements
        # this is done rather than shuffling the documents themselves, as it's likely faster
        # not to store and pass around copies of long documents
        if mode == settings.ROUND_ROBIN:
            # assign the ith datapoint to fold i%k
            self.__folds = [[] for i in range(k)]
            for i in range(len(self.__data)):
                self.__folds[i%k].append(i)
        elif mode == settings.RANDOM:
            # First shuffle the list randomly, then partition
            indices = list(range(len(self.__data)))
            random.shuffle(indices)
            self.__folds = self.__partition(indices, k)
        elif mode == settings.EVEN_SPLIT:
            # simply partition the list without shuffling
            indices = list(range(len(self.__data)))
            self.__folds = self.__partition(indices, k)


if __name__ == "__main__":
    dm = DataManagerCrossValidation()
    dm.divide_into_folds(5, mode=settings.RANDOM)

    for i in range(dm.get_num_folds()):
        print(i)
        dm.set_validation(i)
        print(len(dm.get_train_data()), len(dm.get_validation_data()))
        print(dm.get_validation_data()[0])

        train = dm.get_train_data()

        with open("folds/users_fold{}.tsv".format(i), "w") as fobj:
            writer = csv.writer(fobj, delimiter="\t")
            for row in train:
                ID = row[0]
                lon = row[1][0]
                lat = row[1][1]

                writer.writerow([ID, lon, lat])


