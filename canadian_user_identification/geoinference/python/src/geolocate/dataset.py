##
#  Copyright (c) 2015, Derek Ruths, David Jurgens
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

import json
import os, os.path
import logging
from graph_tool.all import *
import gzip
import sys

logger = logging.getLogger(os.path.basename(__file__))

class Dataset(object):
    """
    This class encapsulates access to datasets.
    """

    def __init__(self,dataset_dir, users_file=None):
            settings_fname = os.path.join(dataset_dir,'dataset.json')
            if os.path.exists(settings_fname):
                self._settings = jsonlib.load(open(settings_fname,'r'))
            else:
                self._settings = {}

            # prepare for all data
            self._posts_fname = os.path.join(dataset_dir,'posts.json.gz')
            if users_file is None:
                self._users_fname = os.path.join(dataset_dir,'users.json.gz')
            else:
                # NOTE: We should probably do some format verification here
                self._users_fname = users_file
            self._mention_network_fname = os.path.join(dataset_dir,'mention_network.elist')

    def post_iter(self):
        """
        Return an iterator over all the posts in the dataset. The ordering
        of the posts follows the order of posts in the dataset file.
        """
        fh = gzip.open(self._posts_fname,'r')

        for line in fh:
            post = json.loads(line)

            yield post

    def __iter__(self):
        """
        Return an iterator over all the posts in the dataset.
        """
        return self.post_iter()

    def user_iter(self):
        """
        Return an iterator over all posts in the dataset grouped by user. Each
        user is represented by a list of their posts - so any metadata about the
        user must be aggregated from the posts it produced.
        """
        fh = gzip.open(self._users_fname,'r')

        for line in fh:
            user = json.loads(line)

            yield user

    def mention_network(self):
        """
        Return the mention network for the dataset.
        """
        G = zen.edgelist.read(self._mention_network_fname,directed=True,weighted=True)

        return G
import sys
def extract_user_mentions(obj):
    user_mentions = obj["entities"]["user_mentions"]
    mention_ids = []
    for u in user_mentions:
        mention_ids.append(u["id"])
    return mention_ids

def posts2dataset(dataset_dir,posts_dir,extract_user_id,extract_mentions,**kwargs):
    """
    This method builds a complete dataset directory and contents from the raw
    posts data in file `posts_fname`.  If the posts file is not in `dataset_dir`,
    then the file will be first copied into the directory.

    The dataset directory, `dataset_dir`, is assumed to not exist.  If an existing
    directory should be accomodated, then set force=True.

    If this function completes successfully, the directory will contain the posts,
    users, and mention network files.
    """
    force = kwargs.pop('force',False)

    if len(kwargs) > 0:
        raise Exception('unknown named argument: %s' % ','.join(kwargs.keys()))

    # handle the dataset directory existence issue
    if os.path.exists(dataset_dir):
        if not force:
            question = "Would you like to remove the existing dataset directory %s?" % dataset_dir
            if input(question+' (y/n): ').lower().strip() == "y":
                print("Removing existing dataset directory...")
                os.system("rm -r %s" % dataset_dir)
            else:
                raise Exception('dataset directory %s exists' % dataset_dir)
        logger.info('creating directory %s' % dataset_dir)
        os.mkdir(dataset_dir)

        # if the post_fname isn't in the dataset_dir,
        # copy it there.
    if os.path.dirname(posts_dir) != dataset_dir:
        logger.info('copying posts dir %s' % posts_dir)
        os.system('cp -r %s %s' % (posts_dir, dataset_dir))
        posts_dir = os.path.join(dataset_dir, posts_dir)

    # now make the users file
    logger.info('building the users.json.gz file')
    posts2users(posts_dir, extract_user_id, working_dir=dataset_dir)

    # now make the mention network
    logger.info('building the mention network')
        # NOTE: overwrote this to use my user mention function
    posts2mention_network(posts_dir, extract_user_id,extract_user_mentions, working_dir=dataset_dir)

    # done!
    return

def posts2mention_network(posts_dir,extract_user_id,
                          extract_mentions,working_dir=None):
    """
    This method builds a valid `mention_network.elist` file from the
    `posts.json.gz` file specified. Unless indicated otherwise, the
    directory containing the posts file will be used as the working
    and output directory for the construction process.

    `extract_user_id` is a function that accepts a post and returns a string
    user_id.

    `extract_mentions` is a function that accepts a post and returns a list of
    string user_ids mentioned in the post.
    """
    G = Graph()

    # figure out the working dir
    if not working_dir:
        working_dir = os.path.dirname(posts_dir)

    # bin the user data
    logging.info('building the network')
    cnt = 0
    # maps vertex descriptor --> user id
    vprop = G.new_vertex_property("string")
    # maps edge descriptor --> weight
    weight_prop = G.new_edge_property("int") # track edge weights
    # maps user id --> vertex descriptor
    vertices = dict()
    # maps a tuple of user ids to their edge descriptor in the graph
    edges = dict()
    for posts_fname in os.listdir(posts_dir):
        fh = gzip.open(os.path.join(posts_dir, posts_fname),'r')
        for line in fh:
            cnt += 1
            post = json.loads(line)
            uid = extract_user_id(post)
            uid = str(uid)
            mentions = extract_mentions(post)

            # vertex for this user
            if uid not in vertices:
                v = G.add_vertex()
                vprop[v] = uid
                vertices[uid] = v
                # print("Added new vertex:", uid)

            for m in mentions:
                #if G.has_edge(uid,m):
                #        G.set_weight(uid,m,G.weight(uid,m)+1)
                #else:
                m = str(m)
                if m not in vertices:
                    v = G.add_vertex()
                    vprop[v] = m
                    vertices[m] = v
                    # print("Added new vertex:", m)
                uv = vertices[uid]
                mv = vertices[m]

                # determine if the edge uid->m already exists
                # fun fact: if you pass a string into G.iter_in_edges,
                #           you get a segmentation fault :)
                is_target_of_uid = [vprop[edge[1]] for edge in list(G.iter_out_edges(uv))]
                if m in is_target_of_uid:
                    # if m is already a target of this user, this is not the
                    # first time uid has mentioned m
                    # find the existing edge and simply increase its weight
                    e = edges[(uid, m)]
                    weight_prop[e] += 1
                    # print(f"Incremented edge weight from {uid} to {m} to {weight_prop[e]}")
                else:
                    # this is the first time uid has mentioned m
                    if uid == m:
                        if "retweeted_status" in post:
                            # this is a retweet. Retweets automatically mention the retweeting
                            # user, for some reason?
                            continue
                    e = G.add_edge(uv,mv)
                    weight_prop[e] = 1
                    edges[(uid, m)] = e
                    # print(f"Added edge from {uid} to {m}")


        print(cnt, "total tweets")
        print(f"Found {len(vertices)} vertices and {len(edges)} edges.")

        # iterate over all pairs of vertices
        # if both (source, target) and (target, source) are edges,
        # then keep the edges
        # otherwise, remove them

        for source, target in list(edges.keys()):
            if (target, source) not in edges or target == source:
                G.remove_edge(edges[(source, target)])
                del edges[(source, target)]
        print(f"Found {len(vertices)} vertices and {len(edges)} bidirectional edges.")


        nodes = set(vertices.values())
        nodes_list = list(vertices.values())
        to_remove = []
        for vstr, v in list(vertices.items()):
            if len(list(G.iter_all_edges(v))) == 0:
                to_remove.append(v)
                del vertices[vstr]

        G.remove_vertex(to_remove)
        print("Vertices:", len(list(G.iter_vertices())), len(vertices))
        print("Edges:", len(list(G.iter_edges())), len(edges))
        print(f"Found {len(vertices)} vertices with degree > 0 and {len(edges)} bidirectional edges.")

        graph_draw(G, vertex_text=G.vertex_index, output="test_graph.pdf")
        sys.exit()


    #      edges = G.edges()
    #      bi, cnt, total = 0, 0, 0
    #      edge_counts = dict()
    #      for n in G.nodes():
    #          edge_counts[n] = 0
    #
    #      for edge in edges:
    #          # print(edge)
    #          u1, u2 = edge
    #          w = G.weight(u1, u2)
    #          total += 1
    #
    #          if w > 1:
    #              cnt += 1
    #              # print("weight >= 1", w)
    #              edge_counts[u1] += 1
    #              edge_counts[u2] += 1
    #          elif G.has_edge(u2, u1):
    #              print("G has both edges! Next line should be True, True")
    #              print(G.has_edge(u1, u2), G.has_edge(u2, u1))
    #              bi += 1
    #          else:
    #              G.rm_edge(u1, u2)
    #              continue
    #
    #
    #          # if G.has_edge(u1, u2):
    #          #     print("This edge exists in the graph, test successful")
    #          #if not G.has_edge(u2, u1):
    #              # G.rm_edge(u1, u2)
    #           #   total += 1
    #              #print("Deleting edge:", edge)
    #          #else:
    #           #   print("G has both edges (next line should be True, True):")
    #            #  print(G.has_edge(u1, u2), G.has_edge(u2, u1))
    #             # bi += 1
    #              #total += 1
    #
    #      print("cnt =", cnt, "bi =", bi, "total = ", total)
    #      print("nodes =", len(G.nodes()), "edges =", len(G.edges()))
    #
    #      #for n, c in edge_counts.items():
    #      #    if c == 0:
    #      #        G.rm_node(n)
    #
    #      print("nodes =", len(G.nodes()), "edges =", len(G.edges()))
    #
    #      # save the graph
    #  logging.info('writing network')
    #  # TODO: Add compression to this...
    #  zen.io.edgelist.write(G,os.path.join(working_dir,'mention_network.elist'),use_weights=True)

    # TODO: save the graph to file

    # done
    return


def posts2users(posts_dir,extract_user_id,
                working_dir=None,max_open_temp_files=256):
    """
    This method builds a valid `users.json.gz` file from the `posts.json.gz` file
    specified.  Unless indicated otherwise, the directory containing the posts
    file will be used as the working and output directory for the construction
    process.

    `extract_user_id` is a function that accepts a post and returns a string
    user_id.
    """

    # figure out the working dir
    if not working_dir:
        working_dir = os.path.dirname(posts_dir)

    # bin the user data
    logger.info('binning user posts')

    curr_temp_file_idx = -1

    # A dict from a user-id to the file handle-id
    user_assignments = {}
    # A dict from the file handle-id to the actual file handle
    file_handles = {}

    # Sanity check methods for ensuring we're reading and writing
    # all the data.
    posts_seen = 0
    user_posts_written = 0

    for posts_fname in os.listdir(posts_dir):
        fh = gzip.open(os.path.join(posts_dir, posts_fname),'r')
        for line in fh:
                post = json.loads(line)
                uid = extract_user_id(post)
                posts_seen += 1

                if uid not in user_assignments:

                        # Get the temp file this user should be in.
                        # Assume that user-ids are randomly distribued
                        # in some range such that the last three
                        # digits of the id serve as a uniformly
                        # distributed hash
                        tmp_file_assignment = int(uid) % max_open_temp_files
                        if not tmp_file_assignment in file_handles:
                                # Write the temp file as gzipped files
                                # because this splitting process gets
                                # very expensive when processing large
                                # datasets
                                tmp_fname = os.path.join(working_dir,'tmp-%03d.json.gz'
                                                         % tmp_file_assignment)
                                logger.debug('creating temp file %s' % tmp_fname)

                                tmp_fh = gzip.open(tmp_fname,'w')

                                file_handles[tmp_file_assignment] = tmp_fh
                        user_assignments[uid] = tmp_file_assignment

                file_handles[user_assignments[uid]].write(line)

        for idx,tmp_fh in file_handles.items():
                tmp_fh.close()

    # aggregate the users
    logger.info('aggregating user data')

    user_fh = gzip.open(os.path.join(working_dir,'users.json.gz'),'w')
    for i in range(max_open_temp_files):
        logging.debug('processing file %d' % i)

        tmp_fname = os.path.join(working_dir,'tmp-%03d.json.gz' % i)
        tmp_fh = gzip.open(tmp_fname,'r')

        # aggregate data by tweets
        user_posts = {}
        for line in tmp_fh:
            post = json.loads(line)
            uid = extract_user_id(post)

            if uid not in user_posts:
                user_posts[uid] = []

            user_posts[uid].append(post)

        # write out the tweets by user
        for uid,posts in user_posts.items():
            post = "{}\n".format(json.dumps({'user_id':uid,'posts':posts}))
            user_fh.write(bytes(post, 'utf-8'))
            user_posts_written += len(posts)

        # delete the temporary file
        tmp_fh.close();
        os.remove(tmp_fname)

    # done
    user_fh.close()
    logger.debug("Read %s posts, wrote %s posts to users.json.gz"
            % (posts_seen, user_posts_written))

