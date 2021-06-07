##
#  Copyright (c) 2015, David Jurgens
#
#  All rights reserved. See LICENSE file for details
##

"""
A geoinference dataset is stored on disk in a directory with the following format:

    ds_root/
        dataset.json - metadata about the dataset
        posts.json.gz - all posts in the dataset in arbitrary order
        users.json.gz - all posts in the dataset grouped by user

This module provides a class for managing and accessing this directory as well
as helper functions for building new datasets.

**File formats**:

All three core files in the dataset directory contain data in JSON format.

  - `posts.json.gz` contains one post per line.  Each post is a JSON dictionary,
    the contents of git@drgitlab.cs.mcgill.ca:druths/sysconfig.gitwhich is specific to the platform the post was taken from.

  - `users.json.gz` contains one user per line.  Each user is a JSON dictionary
    with at least the following keys:
      - `user_id` is a string identifier for the user that flags them as unique
        among all other users in the dataset.
      - `posts` is a JSON list which contains all the posts belonging to that user.
        These posts should have identical format and data to those in the
        `posts.json.gz` file.  Moreover, every post present in the `posts.json` file
        must be present in `users.json` and visa versa.
"""
# workaround for not having tkinter installed
import matplotlib
matplotlib.use("agg")

import simplejson
import json
import os, os.path
from graph_tool.all import *
import gzip
import subprocess

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
