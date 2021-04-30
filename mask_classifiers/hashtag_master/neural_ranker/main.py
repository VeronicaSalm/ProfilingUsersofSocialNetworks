import argparse
from hashtag_master.neural_ranker.rerank import *
from hashtag_master.neural_ranker.metrics import *
from hashtag_master.neural_ranker.config import get_resources
from hashtag_master.neural_ranker.features.feature_extractor import FeatureExtractor
from hashtag_master.neural_ranker.models import mse_ranker, mr_ranker, mse_multi_ranker, mr_multi_ranker
import sys


def create_neural_ranking_model(model_type):
    """
    Trains and returns the neural ranking model, without calling it from the command-line.
    Uses hard-coded paths for convenience for our task.
    """
    train_path = "hashtag_master/data/our_dataset/train_corrected.tsv"
    train_topk_path = "train_topk.tsv"
    test_path = "hashtag_master/data/our_dataset/test_corrected.tsv"
    test_topk_path = "hashtag_master/data/our_dataset/test_topk.tsv"

    feature_extractor = FeatureExtractor(get_resources(), model_type)
    train_feats, train_labels, _, _ = feature_extractor.get_features(train_path, train_topk_path)

    epochs, lr1, lr2 = 100, 0.01, 0.05

    # Initialize model
    model = None
    if model_type == "mse":
        model = mse_ranker.MSERanker(epochs, lr1)
    elif model_type == "mr":
        model = mr_ranker.MRRanker(epochs, lr1)
    elif model_type == "mse_multi":
        model = mse_multi_ranker.MSEMultiRanker(epochs, lr1, lr2)
    elif model_type == "mr_multi":
        model = mr_multi_ranker.MRMultiRanker(epochs, lr1, lr2)

    # Train model
    model.train(train_feats, train_labels)

    return model, feature_extractor


def main(args):

    feature_extractor = FeatureExtractor(get_resources(), args.model)
    train_feats, train_labels, _, _ = feature_extractor.get_features(args.train, args.train_topk)
    test_feats, _, test_segs, test_gold_truths = feature_extractor.get_features(args.test, args.test_topk)

    epochs, lr1, lr2 = 100, 0.01, 0.05

    # Initialize model
    model = None
    if args.model == "mse":
        model = mse_ranker.MSERanker(epochs, lr1)
    elif args.model == "mr":
        model = mr_ranker.MRRanker(epochs, lr1)
    elif args.model == "mse_multi":
        model = mse_multi_ranker.MSEMultiRanker(epochs, lr1, lr2)
    elif args.model == "mr_multi":
        model = mr_multi_ranker.MRMultiRanker(epochs, lr1, lr2)

    # Train model
    model.train(train_feats, train_labels)

    # Rerank top-k segmentations
    top_segmentations = []
    i = 1
    for segs_feats, segs, gds in zip(test_feats, test_segs, test_gold_truths):
        print("Hashtag", i)
        print(segs)
        print(gds)
        if len(segs) == 1:
            top_segmentations.extend(segs)
        else:
            reranked_segs = rerank(segs, segs_feats, model, args.model)
            print(reranked_segs)
            top_segmentations.append(reranked_segs)
        i += 1
        if i == 10:
            sys.exit()

    if args.output is not None:
        fp = open(args.output, 'w')
        for segs in top_segmentations:
            target = "".join(segs[0].split())
            fp.write(target + "\t" + "\t".join([seg.strip() for seg in segs]) + "\n")
        fp.close()

    # Evaluate metrics
    print("MRR:", mean_reciprocal_rank(test_gold_truths, top_segmentations))
    print("Accuracy@1:", accuracy(1, test_gold_truths, top_segmentations))
    print("Accuracy@2:", accuracy(2, test_gold_truths, top_segmentations))
    print("Fscore@1:", fscore(1, test_gold_truths, top_segmentations))
    print("Fscore@2:", fscore(2, test_gold_truths, top_segmentations))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Runs our pairwise neural ranker model.')
    parser.add_argument('--train', help='Path to train hashtags file.\n'
                                        'The input file is tab seperated. The format is: \n'
                                        '<tweet> <hashtag without #> <tab separated gold-truth segmentations>.',
                        dest='train', type=str)
    parser.add_argument('--train_topk', help='Path to top-k candidates file of traning dataset. \n'
                                             'The output file is tab seperated. The format is: \n'
                                             '<hashtag without #> <tab separated top-k candidates>.',
                        dest='train_topk', type=str)
    parser.add_argument('--test', help='Path to test hashtags file. The format is same as traning dataset. \n',
                        dest='test', type=str)
    parser.add_argument('--test_topk', help='Path to top-k candidates file of traning dataset. \n'
                                            'The format is same as training dataset.',
                        dest='test_topk', type=str)
    parser.add_argument('--out', help='Path to reranked candidates file. \n'
                                      'The output file is tab seperated. The format is: \n'
                                      '<hashtag without #> <tab separated top-k candidates>.',
                        dest='output', type=str)
    parser.add_argument('--model', type=str, dest='model', default="mse_multi", help='Type of model. The input should be one'
                                                                'of the strings: mse, mse_multi, mr, mr_multi')
    args = parser.parse_args()
    main(args)
