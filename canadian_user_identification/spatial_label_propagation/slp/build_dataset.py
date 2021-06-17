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
import sys

def index_json(idx_string, obj):
    """
    A recursive method to index into a json object (dictionary)
    using a string index containing dots. It also handles list objects,
    treating the string slice as a key for each item in the list, which
    is assumed to be a dict.
        e.g.)
            [user["id"] for user in post["entities"]["user_mentions"]]
            is equivalent to
            index_json("entities.user_mentions.id", post)

    Arguments:
        idx_string:
        obj: the dict or list

    Returns:
        result: the result of indexing into the object
    """
    indices = idx_string.split(".")
    idx = indices[0]
    if type(obj) == list:
        result = []
        for sub_obj in obj:
            result.append(sub_obj[idx])
    elif type(obj) == dict:
        result = obj[idx]
    else:
        # Raise an exception if a non-dict, non-list object is passed to this method
        print("Object:", obj)
        print("Index String:", idx_string)
        raise Exception("Attempted to index into an object that was neither a dict nor list.")

    # if we only have one index step left, this must be the final result
    if len(indices) == 1:
        return result
    else:
        # otherwise, our string is at least X.Y so we need to recurse
        return index_json(".".join(indices[1::]), result)

def posts2dataset(dataset_dir,posts_dir,extract_user_id,extract_mentions, extract_incoming=None):
    """
    """
    # handle the dataset directory existence issue
    if os.path.exists(dataset_dir):
        question = "Would you like to remove the existing dataset directory %s?" % dataset_dir
        if input(question+' (y/n): ').lower().strip() == "y":
            print("Removing existing dataset directory...")
            os.system("rm -r %s" % dataset_dir)
        else:
            raise Exception('dataset directory %s exists' % dataset_dir)
    print('Creating directory %s' % dataset_dir)
    os.mkdir(dataset_dir)

    # now make the mention network
    print('Building the network...')
    posts2mention_network(posts_dir, extract_user_id,extract_mentions, working_dir=dataset_dir, extract_incoming_edges=extract_incoming)

    # done!
    return

def posts2mention_network(posts_dir,extract_user_id,
                          extract_mentions,working_dir=None, extract_incoming_edges=None):
    """
    This method builds a valid `mention_network.elist` file from the
    `posts.json.gz` file specified. Unless indicated otherwise, the
    directory containing the posts file will be used as the working
    and output directory for the construction process.

    extract_incoming_edges: is None if there are no incoming edges for a given object,
                    or is a string like extract_mentions if there are incoming edges
                    (e.g., None for mention graphs, but a string for followers)

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
        print(f"Processing {posts_fname}...")
        for line in fh:
            cnt += 1
            post = json.loads(line)
            # NOTE: this works for follow relations too, even if this variable
            # is called "mentions"
            mentions = index_json(extract_mentions, post)
            uid = str(index_json(extract_user_id, post))

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

            if extract_incoming_edges:
                followers = index_json(extract_incoming_edges, post)
                for m in followers:
                    m = str(m)
                    if m not in vertices:
                        v = G.add_vertex()
                        G.vp.user_id[v] = m
                        vertices[m] = v
                        # print("Added new vertex:", m)
                    uv = vertices[uid]
                    mv = vertices[m]

                    # determine if the edge m->uid already exists
                is_target_of_m = [G.vp.user_id[edge[1]] for edge in list(G.iter_out_edges(mv))]
                if uid == m and "retweeted_status" in post:
                    # this is a retweet. Retweets automatically mention the retweeting
                    # user, for some reason?
                    # NOTE: this should never be relevant for follow graphs, but is left in just
                    #       in case
                    continue
                if uid in is_target_of_m:
                    # if uid is already a target of this user,
                    # find the existing edge and simply increase its weight
                    e = edges[(m, uid)]
                    G.ep.weight[e] += 1
                else:
                    # this is the first time uid has mentioned m
                    e = G.add_edge(mv, uv)
                    G.ep.weight[e] = 1
                    edges[(m, uid)] = e

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
