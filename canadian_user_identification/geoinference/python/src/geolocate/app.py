##
#  Copyright (c) 2015, Derek Ruths, David Jurgens
#
#  All rights reserved. See LICENSE file for details
##
import argparse
import json
import os, os.path
import gzip
import time

from dataset import Dataset, posts2dataset
from sparse_dataset import SparseDataset
from spatial_label_propagation import SpatialLabelPropagation

def train(args):
    parser = argparse.ArgumentParser(prog='geoinf train',description='train a geoinference method on a specific dataset')
    parser.add_argument('-f','--force',help='overwrite the output model directory if it already exists')
    parser.add_argument('method_name',help='the method to use')
    parser.add_argument('method_settings',help='a json file containing method-specific configurations')
    parser.add_argument('dataset_dir',help='a directory containing a geoinference dataset')
    parser.add_argument('model_dir',help='a (non-existing) directory where the trained model will be stored')
    parser.add_argument('--location-source', nargs=1,
                            help='specifies the source of ground-truth locations')

    args = parser.parse_args(args)

    if os.path.exists(args.model_dir):
        question = "Would you like to remove the existing model directory %s?" % args.model_dir
        if input(question+' (y/n): ').lower().strip() == "y":
            print("Removing existing model directory...")
            os.system("rm -r %s" % args.model_dir)
        else:
            raise Exception('dataset directory %s exists' % args.model_dir)
        print('creating directory %s' % args.model_dir)
        os.mkdir(args.model_dir)

    #  # confirm that the output directory doesn't exist
    #  if os.path.exists(args.model_dir) and not args.force:
    #      raise Exception('output model_dir cannot exist')

    # load the method
    # method = get_method_by_name(args.method_name)

    # load the data
    with open(args.method_settings,'r') as fh:
        settings = json.load(fh)

        location_source = args.location_source
        if location_source:
                location_source = location_source[0]
                print('Using %s as the source of ground truth location'
                             % location_source)
                settings['location_source'] = location_source



    # load the dataset
    ds = None #Dataset(args.dataset_dir)
    if not location_source is None:
            ds = SparseDataset(args.dataset_dir, default_location_source=location_source)
    else:
            ds = SparseDataset(args.dataset_dir)


    # load the method
    # method = get_method_by_name(args.method_name)
    # method_inst = method()
    method_inst = SpatialLabelPropagation()

    print("Starting")
    start_time = time.time()
    method_inst.train_model(settings,ds,args.model_dir)
    end_time = time.time()
    print('Trained model %s on dataset %s in %f seconds'
                    % (args.method_name, args.dataset_dir, end_time - start_time))

    # drop some metadata into the run method
    # run the method
    # gi_inst = method()
    # gi_inst.train(settings,ds,args.model_dir)

    return

def build_dataset(args):
    parser = argparse.ArgumentParser(prog='geoinf build_dataset',description='build a new dataset')
    parser.add_argument('-f','--force',action='store_true')
    parser.add_argument('dataset_dir',help='the directory to put the dataset in')
    parser.add_argument('posts_file',help='the posts.json.gz file to use')
    parser.add_argument('user_id_field',help='the field name holding the user id of the post author')
    parser.add_argument('mention_field',help='the field name holding the list of user ids mentioned in a post')

    args = parser.parse_args(args)

    uid_field_name = args.user_id_field.split('.')[::-1]
    mention_field_name = args.mention_field.split('.')[::-1]
    posts2dataset(args.dataset_dir,args.posts_file,
                  lambda x: (lambda a: lambda dic, ind: a(a, dic, ind))(lambda s, dic, ind: str(dic) if ind == -1  else s(s,dic[uid_field_name[ind]], ind-1))(x, len(uid_field_name)-1),
                  lambda x: (lambda a: lambda dic, ind: a(a, dic, ind))(lambda s, dic, ind: str(dic) if ind == -1 else (s(s,dic.get(mention_field_name[ind],[]), ind-1) if type(dic) == dict else map(lambda d: s(s,d,ind), dic)))(x, len(mention_field_name)-1),
                  force=args.force)

    # done

def main():
    parser = argparse.ArgumentParser(prog='geoinf',description='run a spatial label propagation method on a dataset')
    parser.add_argument('action',choices=['train','build_dataset'],
            help='indicate whether to train the model or create a dataset')
    parser.add_argument('action_args',nargs=argparse.REMAINDER,
            help='arguments specific to the chosen action')

    args = parser.parse_args()

    try:
        if args.action == 'train':
            train(args.action_args)
        elif args.action == 'build_dataset':
            build_dataset(args.action_args)
        else:
            raise Exception('unknown action: %s' % args.action)

    except Exception as e:
        print(e)

    # done!

if __name__ == '__main__':
    main()


