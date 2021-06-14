##
#  Copyright (c) 2015, Derek Ruths, David Jurgens
#  Modified by Veronica Salm, 2021
#
#  All rights reserved. See LICENSE file for details
##

"""
This file contains code for building the dataset.

A geoinference dataset is stored on disk in a directory with the following format:
    ds_root/
        saved_graph.gt
"""
import json
import os, os.path
import gzip
from graph_tool.all import *

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
        print('Creating directory %s' % dataset_dir)
        os.mkdir(dataset_dir)

    # now make the mention network
    print('Building the mention network...')
    # TODO: update this function to work for follows
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
    cnt = 0
    # maps vertex descriptor --> user id
    G.vp.user_id = G.new_vertex_property("string")
    # maps edge descriptor --> weight
    G.ep.weight = G.new_edge_property("int64_t") # track edge weights

    # maps user id --> vertex descriptor
    vertices = dict()
    # maps a tuple of user ids to their edge descriptor in the graph
    edges = dict()
    user_set = set()
    for posts_fname in os.listdir(posts_dir):
        fh = gzip.open(os.path.join(posts_dir, posts_fname),'r')
        for line in fh:
            cnt += 1
            post = json.loads(line)
            uid = str(extract_user_id(post))
            mentions = extract_mentions(post)

            # vertex for this user
            if uid not in vertices:
                v = G.add_vertex()
                G.vp.user_id[v] = uid
                vertices[uid] = v

            for m in mentions:
                m = str(m)
                if m not in vertices:
                    v = G.add_vertex()
                    G.vp.user_id[v] = m
                    vertices[m] = v
                    # print("Added new vertex:", m)
                uv = vertices[uid]
                mv = vertices[m]

                # determine if the edge uid->m already exists
                # fun fact: if you pass a string into G.iter_in_edges,
                #           you get a segmentation fault :)
                is_target_of_uid = [G.vp.user_id[edge[1]] for edge in list(G.iter_out_edges(uv))]
                if uid == m and "retweeted_status" in post:
                    # this is a retweet. Retweets automatically mention the retweeting
                    # user, for some reason?
                    continue
                if m in is_target_of_uid:
                    # if m is already a target of this user, this is not the
                    # first time uid has mentioned m
                    # find the existing edge and simply increase its weight
                    e = edges[(uid, m)]
                    G.ep.weight[e] += 1
                else:
                    # this is the first time uid has mentioned m
                    e = G.add_edge(uv,mv)
                    G.ep.weight[e] = 1
                    edges[(uid, m)] = e

    print("User set:", len(user_set))
    print(cnt, "total tweets")
    print(f"Found {len(vertices)} vertices and {len(edges)} edges.")

    # iterate over all edges (source, target)
    # if both (source, target) and (target, source) are edges,
    # then keep the edges
    # otherwise, remove them
    for source, target in list(edges.keys()):
      if (target, source) not in edges or target == source:
          G.remove_edge(edges[(source, target)])
          del edges[(source, target)]
    print(f"Found {len(vertices)} vertices and {len(edges)} bidirectional edges.")


    # Remove any vertices with degree 0 from the final graph
    to_remove = []
    for vstr, v in list(vertices.items()):
      if len(list(G.iter_all_edges(v))) == 0:
          to_remove.append(v)
          del vertices[vstr]

    G.remove_vertex(to_remove)
    print(f"Found {len(vertices)} vertices with degree > 0 and {len(edges)} bidirectional edges.")

    # save an image of the resulting graph
    # omitted: doesn't work well for large graphs
    #graph_draw(G, vertex_text=G.vertex_index, output=os.path.join(working_dir, "graph_visualization.pdf"))

    # save the graph to file
    print("Writing network...", end=" ")
    dest = os.path.join(working_dir,'saved_graph.gt')
    G.save(dest)
    print("Done!")

    # done
    return
