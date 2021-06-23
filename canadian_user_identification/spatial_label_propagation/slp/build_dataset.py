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
import networkit as nk
import sys
import csv

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
    G = nk.graph.Graph(weighted=True, directed=True)

    # figure out the working dir
    if not working_dir:
        working_dir = os.path.dirname(posts_dir)

    cnt = 0
    # maps user id --> vertex descriptor
    vertices = dict()
    for posts_fname in os.listdir(posts_dir):
        fh = gzip.open(os.path.join(posts_dir, posts_fname),'r')
        print(f"Processing {posts_fname}...")
        for line in fh:
            cnt += 1
            post = json.loads(line)
            # NOTE: this works to extract follow relations too, even if this variable
            # is called "mentions"
            mentions = index_json(extract_mentions, post)
            uid = str(index_json(extract_user_id, post))

            # vertex for this user
            if uid not in vertices:
                v = G.addNode() # v is an integer descriptor
                vertices[uid] = v

            for m in mentions:
                m = str(m)
                if m not in vertices:
                    v = G.addNode()
                    vertices[m] = v
                uv = vertices[uid]
                mv = vertices[m]

                if uid == m and "retweeted_status" in post:
                    # this is a retweet. Retweets automatically mention the retweeting
                    # user, for some reason?
                    continue
                if G.hasEdge(uv, mv):
                    # if m is already a target of this user, this is not the
                    # first time uid has mentioned m
                    # find the existing edge and simply increase its weight
                    w = G.weight(uv, mv)
                    G.setWeight(uv, mv, w+1)
                else:
                    # this is the first time uid has mentioned m
                    G.addEdge(uv, mv, 1)

            if extract_incoming_edges:
                followers = index_json(extract_incoming_edges, post)
                for m in followers:
                    m = str(m)
                    if m not in vertices:
                        v = G.addNode()
                        vertices[m] = v
                    uv = vertices[uid]
                    mv = vertices[m]

                    if uid == m and "retweeted_status" in post:
                        continue

                    if G.hasEdge(mv, uv):
                        # if uid is already a target of this user,
                        # find the existing edge and simply increase its weight
                        w = G.weight(mv, uv)
                        G.setWeight(mv, uv, w+1)
                    else:
                        # this is the first time uid has mentioned m
                        G.addEdge(mv, uv, 1)
            #  print("User", uid)
            #  print("Mentions", mentions)
            #  print(vertices)
            #  print(list(G.iterNodes()))
            #  print(list(G.iterEdgesWeights()))
            #  sys.exit()
    print(f"Processed {cnt} total objects.")
    print(f"Found {G.numberOfNodes()} vertices and {G.numberOfEdges()} edges.")

    # iterate over all edges (source, target)
    # if both (source, target) and (target, source) are edges,
    # then keep the edges
    # otherwise, remove them
    edges = list(G.iterEdges())
    for source, target in edges:
        if (not G.hasEdge(target, source)) or target == source:
            G.removeEdge(source, target)
    print(f"Found {G.numberOfNodes()} vertices and {G.numberOfEdges()} bidirectional edges.")


    # Remove any vertices with degree 0 from the final graph
    for vstr, v in list(vertices.items()):
      if G.degree(v) == 0:
          G.removeNode(v)
          del vertices[vstr]

    print(f"Found {G.numberOfNodes()} vertices with degree > 0 and {G.numberOfEdges()} bidirectional edges.")

    if not G.checkConsistency():
        raise Exception("The constructed graph is inconsistent. Something went wrong! Please fix this error and try again.")


    print("Writing network...", end=" ")
    dest = os.path.join(working_dir,'saved_graph.gt')
    nk.writeGraph(G, dest, nk.Format.GraphToolBinary)
    print("Done!")

    # TODO: write vertex map and also add code to load it in / pass it around
    print("Writing user ID to vertex map...", end=" ")
    vertex_path = os.path.join(working_dir,'vertex_to_userID.csv')
    with open(vertex_path, "w") as f:
        writer = csv.writer(f)
        # saving the graph will condense the vertex IDs, so make sure
        # to save the condensed IDs (ranging from 0 to numNodes-1) accordingly
        u2v = list(sorted(vertices.items(), key=lambda x: x[1]))
        idx = 0
        for user, vertex in u2v:
            writer.writerow([idx, user])
            idx += 1
    print("Done!")

    # done
    return
