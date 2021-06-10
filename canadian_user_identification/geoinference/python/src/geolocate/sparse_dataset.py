##
#  Copyright (c) 2015, David Jurgens
#
#  All rights reserved. See LICENSE file for details
##
"""
A geoinference dataset is stored on disk in a directory with the following format:
    ds_root/
        saved_graph.gt
"""

import json
import os, os.path
from graph_tool.all import *
import gzip

class SparseDataset(object):
    """
    This class encapsulates access to datasets.
    """

    def __init__(self, dataset_dir, default_location_source='geo-median'):

        settings_fname = os.path.join(dataset_dir,'dataset.json')
        if os.path.exists(settings_fname):
            self._settings = json.load(open(settings_fname,'r'))
        else:
            self._settings = {}

        # prepare for all data
        self._dataset_dir = dataset_dir
        self._users_with_locations_fname = os.path.join(dataset_dir, 'users.home-locations.' + default_location_source + '.tsv.gz')
        self._network_fname = os.path.join(dataset_dir, 'saved_graph.gt')


    def post_iter(self):
        """
        Return an iterator over all the posts in the dataset. The ordering
        of the posts follows the order of users in the dataset file.
        """
        fh = gzip.open(self._users_fname,'r')

        for line in fh:
            user = self.load_user(line)
            for post in user["posts"]:
                yield post
        fh.close()

    def __iter__(self):
        """
        Return an iterator over all the posts in the dataset.
        """
        return self.post_iter()

    def user_home_location_iter(self):
            """
            Returns an iterator over all the users whose home location has
            been already identified.
            """
            location_file = self._users_with_locations_fname
            print('Loading home locations from %s'
                         % (self._users_with_locations_fname))
            fh = gzip.open(location_file)
            for line in fh:
                user_id, lat, lon = line.decode().split('\t')
                yield (user_id, (float(lat), float(lon)))
            fh.close()


    def known_user_locations(self):
        """
        Return dictionary of users to their locations, containing only
        users who have already self-reported their own location.
        """
        fh = gzip.open(self._users_fname,'r')

        for line in fh:
            user = self.load_user(line)
            yield user
        fh.close()

    def build_graph(self):
        fname = os.path.join(self._dataset_dir, 'saved_graph.gt')
        print("Loading graph from:", fname)
        G = load_graph(fname)
        print("successfully loaded graph")
        return G
