#!/usr/bin/env python
from __future__ import print_function

import argparse
import collections
import gzip
import json
import sys
import warnings
from collections import defaultdict
import geopy.distance
import csv


from . import get_resolver
from .location import Location, LocationEncoder


def parse_args():
    parser = argparse.ArgumentParser(
        description='Resolve tweet locations.',
        epilog='Paths ending in ".gz" are treated as gzipped files.')
    parser.add_argument('-s', '--statistics',
        action='store_true',
        help='show summary statistics')
    parser.add_argument('--order',
        metavar='RESOLVERS',
        help='preferred resolver order (comma-separated)')
    parser.add_argument('--options',
        default='{}',
        help='JSON dictionary of resolver options')
    parser.add_argument('--locations',
        metavar='PATH', dest='location_file',
        help='path to alternative location database')
    parser.add_argument('input_file', metavar='input_path',
        nargs='?', default=sys.stdin,
        help='file containing tweets to locate with geolocation field '
             '(defaults to standard input)')
    parser.add_argument('output_file', metavar='output_path',
        nargs='?', default=sys.stdout,
        help='file to write geolocated tweets to (defaults to standard '
             'output)')
    return parser.parse_args()


def open_file(filename, mode):
    if filename.endswith('.gz'):
        return gzip.open(filename, mode)
    else:
        return open(filename, mode)


def main():
    args = parse_args()
    warnings.simplefilter('always')
    resolver_kwargs = {}
    if args.order is not None:
        resolver_kwargs['order'] = args.order.split(',')
    if args.options is not None:
        resolver_kwargs['options'] = json.loads(args.options)

    print(resolver_kwargs)
    resolver = get_resolver(**resolver_kwargs)

    resolver.load_locations(location_file=args.location_file)
    # Variables for statistics.
    city_found = county_found = state_found = country_found = 0
    has_place = has_coordinates = has_geo = has_profile_location = 0
    resolution_method_counts = collections.defaultdict(int)
    skipped_tweets = resolved_tweets = total_tweets = 0

    users = defaultdict(list)

    with open_file(args.input_file, 'rb') as input_file, open_file(args.output_file, 'wb') as output_file:
        for i, input_line in enumerate(input_file):
            # Show warnings from the input file, not the Python source code.
            def showwarning(message, category, filename, lineno,
                            file=sys.stderr, line=None):
                sys.stderr.write(warnings.formatwarning(
                    message, category, input_file.name, i+1,
                    line=''))
            warnings.showwarning = showwarning
            try:
                if len(input_line.strip()) == 0:
                    continue
                tweet = json.loads(input_line)
            except ValueError:
                warnings.warn('Invalid JSON object')
                skipped_tweets += 1
                continue
            # Collect statistics on the tweet.
            if tweet.get('place'):
                has_place += 1
                if len(tweet["place"]["bounding_box"]["coordinates"][0]) != 4:
                    sys.exit()
            if tweet.get('coordinates'):
                has_coordinates += 1
            if tweet.get('geo'):
                has_geo += 1
            if tweet.get('user', {}).get('location', ''):
                has_profile_location += 1
            # Perform the actual resolution.
            resolution = resolver.resolve_tweet(tweet)
            if resolution:
                location = resolution[1]
                # store the location as (lat,lon),country
                users[tweet["user"]["id"]].append(((location.latitude, location.longitude), location.country))
                #  if location.country == "Canada":
                #      print(tweet["place"])
                #      print(tweet["user"]["location"])
                tweet['location'] = location
                # More statistics.
                resolution_method_counts[location.resolution_method] += 1
                if location.city:
                    city_found += 1
                elif location.county:
                    county_found += 1
                elif location.state:
                    state_found += 1
                elif location.country:
                    country_found += 1
                resolved_tweets += 1
            json_output = json.dumps(tweet, cls=LocationEncoder).encode()
            output_file.write(json_output)
            output_file.write(bytes('\n'.encode(encoding='ascii')))
            total_tweets += 1

    print('Found %d users' % len(users))
    with open("user_lat_lon.tsv", "w") as f:
        tsv_writer = csv.writer(f, delimiter="\t")
        cnt = 0
        for user in users:
            loc_list = users[user]
            if len(loc_list) >= 3:
                cnt += 1
                median = None
                best_sum = float('inf')
                for i in range(len(loc_list)):
                    sum_dist = 0
                    for j in range(len(loc_list)):
                        # extract coordinates, recall that each loc_list element
                        # is (lat,lon), country
                        coords1 = loc_list[i][0]
                        coords2 = loc_list[j][0]
                        d = geopy.distance.geodesic(coords1, coords2).km
                        sum_dist += d

                    if sum_dist < best_sum:
                        median = loc_list[i]
                        best_sum = sum_dist

                if median != None:
                    tsv_writer.writerow([user, median[0][0], median[0][1]])
        print('Found %d users with at least three located tweets' % cnt)
        print(json.dumps(users, indent=4), file=f)

    if args.statistics:
        print('Skipped %d tweets.' % skipped_tweets, file=sys.stderr)
        print('Tweets with "place" key: %d; '
                                       '"coordinates" key: %d; '
                                       '"geo" key: %d.' % (
                                        has_place, has_coordinates, has_geo), file=sys.stderr)
        print('Resolved %d tweets to a city, '
                                       '%d to a county, %d to a state, '
                                       'and %d to a country.' % (
                                city_found, county_found,
                                state_found, country_found), file=sys.stderr)
        print('Tweet resolution methods: %s.' % (
            ', '.join('%d by %s' % (v, k)
                for (k, v) in resolution_method_counts.items())), file=sys.stderr)
    print('Resolved locations for %d of %d tweets.' % (
        resolved_tweets, total_tweets), file=sys.stderr)


if __name__ == '__main__':
    main()
