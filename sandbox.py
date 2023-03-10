"""
A flexible script for exploring performance of the
Surprise recommender system library
using various MovieLens datasets
"""
# pylint: disable=E0401
import argparse
import json
import time
from collections import OrderedDict, defaultdict
import os
import datetime
import sys
from pprint import pprint

import psutil

import pandas as pd
import numpy as np
from utils import get_dfs, concat_output_filename, load_head_items
from specs import ALGOS, ALGOS_FOR_STANDARDS, NUM_FOLDS
from constants import MEASURES, get_metric_names
from prep_organized_boycotts import (
    group_by_age, group_by_gender, group_by_genre,
    group_by_occupation, group_by_power, group_by_state, group_by_genre_strict
)
from joblib import Parallel, delayed

from surprise.model_selection import cross_validate_custom
from surprise import SVD,Dataset, KNNBaseline, GuessThree, GlobalMean, MovieMean
from surprise.reader import Reader

# long-term: massively abstract this code so it will work w/ non-recsys algorithsm

def task(
    algo_name, algo, nonboycott, boycott, boycott_uid_set,
    like_boycotters_uid_set, measures, cv, verbose, identifier,
    num_ratings, num_users, num_movies, name, head_items, save_path, load_path,
    load_boycotts_path, data):
    return {
        'subset_results': cross_validate_custom(
            algo, nonboycott, boycott, boycott_uid_set,
            like_boycotters_uid_set, measures, cv, n_jobs=1,
            head_items=head_items, save_path=save_path, load_path=load_path, load_boycotts_path=load_boycotts_path, data=data
        ),
        'num_ratings': num_ratings,
        'num_users': num_users,
        'num_movies': num_movies,
        'name': name,
        'algo_name': algo_name,
        'identifier': identifier
    }


def prepare_boycott_task(i, experimental_iteration, args, config, ratings_df, seed_base, outname, algo_name, algo, head_items, data):
    """
    To simulate a boycott, we need to figure out which ratings are being held out
    For large datasets and large boycotts (e.g. 50% of ML-20M) this is very slow
    So we need to parallelize it

    That's the purpose of this function

    """
    if config['type'] == 'individual_users':
        row = experimental_iteration[1]
        identifier = row.user_id
        name = 'individual'
        if args.indices != 'all':
            if identifier < args.indices[0] or identifier > args.indices[1]:
                return
        boycott_uid_set = set([row.user_id])
        like_boycotters_uid_set = set([])
    
    elif config['type'] in [
        'sample_users',
        'gender', 'age', 'power', 'state', 'genre',
        'genre_strict',
        'occupation',
    ]:
        identifier = i
        name = experimental_iteration['name']

        possible_boycotters_df = experimental_iteration['df']                        
        print(name)
        print(possible_boycotters_df.head())
        if args.userfrac != 1.0:
            boycotters_df = possible_boycotters_df.sample(frac=args.userfrac, random_state=(seed_base+i)*2)
        else:
            boycotters_df = possible_boycotters_df
        boycott_uid_set = set(boycotters_df.user_id)
        like_boycotters_df = possible_boycotters_df.drop(boycotters_df.index)
        like_boycotters_uid_set = set(like_boycotters_df.user_id)

    tic = time.time()

    mask_boycott_ratings = ratings_df.user_id.isin(boycott_uid_set)
    non_boycott_user_ratings_df = ratings_df[~mask_boycott_ratings] # makes a df copy
    print('isin time: {}'.format(time.time() - tic))

    boycott_ratings_df = None
    boycott_user_lingering_ratings_df = None
    tic = time.time()

    # BAD (slow) CODE warning: this part is pretty slow when simulating large boycotts for large datasets (e.g. 90% of ML-20M)
    # room for improvement
    if args.ratingfrac == 1.0: # skip this complicated stuff!
        boycott_ratings_df = ratings_df[mask_boycott_ratings]
        # copy the df but drop all rows
        boycott_user_lingering_ratings_df = boycott_ratings_df.drop(boycott_ratings_df.index)
    else:
        for uid in boycott_uid_set:
            ratings_belonging_to_user = ratings_df[ratings_df.user_id == uid]
            if args.ratingfrac != 1.0:
                boycott_ratings_for_user = ratings_belonging_to_user.sample(frac=args.ratingfrac, random_state=(seed_base+i)*3)
            else:
                boycott_ratings_for_user = ratings_belonging_to_user
            lingering_ratings_for_user = ratings_belonging_to_user.drop(boycott_ratings_for_user.index)
            if boycott_ratings_df is None:
                boycott_ratings_df = boycott_ratings_for_user
            else:
                boycott_ratings_df = pd.concat([boycott_ratings_df, boycott_ratings_for_user])
            if boycott_user_lingering_ratings_df is None:
                boycott_user_lingering_ratings_df = lingering_ratings_for_user
            else:
                boycott_user_lingering_ratings_df = pd.concat([boycott_user_lingering_ratings_df, lingering_ratings_for_user])
    print('going through each uid time: {}'.format(time.time() - tic))
    
    print('Iteration: {}'.format(i))
    print('Boycott ratings: {}, Lingering Ratings from Boycott Users: {}'.format(
        len(boycott_ratings_df.index), len(boycott_user_lingering_ratings_df.index)
    ))
    all_non_boycott_ratings_df = pd.concat(
        [non_boycott_user_ratings_df, boycott_user_lingering_ratings_df])

    print('Created dataframes', psutil.virtual_memory().used / (1024**3))

    nonboycott = Dataset.load_from_df(
        all_non_boycott_ratings_df[['user_id', 'movie_id', 'rating']],
        reader=Reader()
    ) # makes a copy
    boycott = Dataset.load_from_df(
        boycott_ratings_df[['user_id', 'movie_id', 'rating']],
        reader=Reader()
    ) # makes a copy
    # why are the Dataset objects taking up 4GB when the dataframe is only 760 MB???
    print('nonboycott.raw_ratings size', sys.getsizeof(nonboycott.raw_ratings))
    print('Created dataset objects', psutil.virtual_memory().used / (1024**3))

    identifier = str(identifier).zfill(4)
    num_users = len(all_non_boycott_ratings_df.user_id.value_counts())
    num_movies = len(all_non_boycott_ratings_df.movie_id.value_counts())
    num_ratings =  len(all_non_boycott_ratings_df.index)

    # make sure to save the set of boycott ids and like boycott ids
    experiment_identifier_to_uid_sets = {
        identifier: {}
    }
    experiment_identifier_to_uid_sets[identifier]['boycott_uid_set'] = ';'.join(str(x) for x in boycott_uid_set)
    experiment_identifier_to_uid_sets[identifier]['like_boycotters_uid_set'] = ';'.join(str(x) for x in like_boycotters_uid_set)

    save_path = outname.replace('results/', 'predictions/boycotts/{}__'.format(identifier)).replace('.csv', '_')
    if args.save_path == 'False':
        print('Since you passed --save_path False, predictions will NOT BE SAVED')
        save_path = None
    elif args.save_path is None:
        save_path = os.getcwd() + '/' + save_path
    else:
        save_path = args.save_path + '/' + save_path

    if args.load_path == 'False':
        load_path = None
    elif args.load_path is None:
        load_path = os.getcwd() + '/predictions/standards/{}_{}_'.format(args.dataset, algo_name)
    else:
        load_path = args.load_path + '/standards/{}_{}_'.format(args.dataset, algo_name)

    load_boycotts_path = save_path
    if args.load_boycotts_path is None:
        load_boycotts_path = None
    return (
        algo_name, algo, nonboycott, boycott, boycott_uid_set, like_boycotters_uid_set, MEASURES, NUM_FOLDS,
        False, identifier,
        num_ratings,
        num_users,
        num_movies, name,
        head_items, save_path, load_path, load_boycotts_path, data
    ), experiment_identifier_to_uid_sets
    


def main(args):
    """
    Run the sandbox experiments
    """
    out_prefix = 'out/' if args.send_to_out else ""
    times = OrderedDict()
    times['start'] = time.time()
    algos = ALGOS
    if args.movie_mean:
        algos = {
            'MovieMean': MovieMean(),
            'GlobalMean': GlobalMean(),
        }
    algos_for_standards = ALGOS_FOR_STANDARDS
    dfs = get_dfs(args.dataset)
    head_items = load_head_items(args.dataset)
    times['dfs_loaded'] = time.time() - times['start']
    print('Got dataframes, took {} seconds'.format(times['dfs_loaded']))
    print('Total examples: {}'.format(len(dfs['ratings'].index)))

    ratings_df, users_df, movies_df = dfs['ratings'], dfs['users'], dfs['movies']
    if args.mode == 'info':
        print(ratings_df.memory_usage(index=True))
        print(users_df.memory_usage(index=True))
        print(movies_df.memory_usage(index=True))

        print(ratings_df.info())
        print(users_df.info())
        return
    data = Dataset.load_from_df(
        ratings_df[['user_id', 'movie_id', 'rating']],
        reader=Reader()
    )
    times['data_constructed'] = time.time() - times['dfs_loaded']

    # note to reader: why are precision, recall, and ndcg all stuffed together in one string?
    # this ensures they will be computed all at once. Evaluation code will split them up for presentation
    metric_names = []
    for measure in MEASURES:
        if '_' in measure:
            splitnames = measure.lower().split('_')
            metric_names += splitnames
            metric_names += [x + '_frac' for x in splitnames]
            metric_names += ['tail' + x for x in splitnames]
        else:
            metric_names.append(measure.lower())
    metric_names = get_metric_names()
    if args.compute_standards:
        standard_results = defaultdict(list)
        for algo_name in algos_for_standards:
            for _ in range(args.num_standards):
                filename_ratingcv_standards = out_prefix + 'standard_results/{}_ratingcv_standards_for_{}.json'.format(
                    args.dataset, algo_name)

                print('Computing standard results for {}'.format(algo_name))
                if args.save_path is False:
                    save_path = None
                elif args.save_path is None:
                    save_path = os.getcwd() + '/' + out_prefix + 'predictions/standards/{}_{}_'.format(args.dataset, algo_name)
                else:
                    save_path = args.save_path

                if 'KNN' in algo_name and args.dataset == 'ml-20m':
                    # running this in parallel runs out of memory with KNN
                    results = cross_validate_custom(
                        algos_for_standards[algo_name], data, Dataset.load_from_df(pd.DataFrame(),
                        reader=Reader()), [], [], MEASURES, NUM_FOLDS, n_jobs=1, head_items=head_items,
                        save_path=save_path)
                else:
                    results = cross_validate_custom(
                        algos_for_standards[algo_name], data, Dataset.load_from_df(pd.DataFrame(),
                        reader=Reader()), [], [], MEASURES, NUM_FOLDS, head_items=head_items,
                        save_path=save_path)
                saved_results = {}
                for metric in metric_names:
                    saved_results[metric] = np.mean(results[metric + '_all'])
                    # frac_key = metric + '_frac_all'
                    # if frac_key in results:
                    #     saved_results[frac_key] = np.mean(results[frac_key])

                with open(filename_ratingcv_standards, 'w') as f:
                    json.dump(saved_results, f)
                    
                standard_results[algo_name].append(saved_results)
            standard_results_df = pd.DataFrame(standard_results[algo_name])
            print(standard_results_df.mean())
            standard_results_df.mean().to_csv('{}'.format(
                filename_ratingcv_standards).replace('.json', '_{}.csv'.format(
                    args.num_standards)
                )
            )

    experiment_configs = []
    if args.grouping == 'individual_users':
        experiment_configs += [{'type': 'individual_users', 'size': None}]
    elif args.grouping == 'sample':
        if args.sample_sizes:
            experiment_configs += [
                {
                    'type': 'sample_users', 'size': sample_size
                } for sample_size in args.sample_sizes]
        else:
            raise ValueError(
                'When using grouping="sample", you must provide a set of sample sizes'
            )
    elif args.grouping in [
        'gender', 'age', 'power', 'state', 'genre', 'genre_strict', 'occupation', 
    ]:
        experiment_configs += [{'type': args.grouping, 'size': None}]
    else:
        experiment_configs = []


    uid_to_error = {}
    experimental_iterations = []
    seed_base = args.indices[0]
    for config in experiment_configs:
        outname = out_prefix + concat_output_filename(
            args.dataset, config['type'], args.userfrac,
            args.ratingfrac,
            config['size'], args.num_samples, args.indices
        )
        if config['type'] == 'individual_users':
            experimental_iterations = list(users_df.iterrows())
        elif config['type'] == 'sample_users':
            experimental_iterations = [{
                'df': users_df.sample(config['size'], random_state=seed_base+index), # copies user_df
                'name': '{} user sample'.format(config['size'])
            } for index in range(args.num_samples)]
        elif config['type'] == 'gender':
            for _ in range(args.num_samples):
                experimental_iterations += group_by_gender(users_df)
        elif config['type'] == 'age':
            for _ in range(args.num_samples):
                experimental_iterations += group_by_age(users_df)
        elif config['type'] == 'state':
            for _ in range(args.num_samples):
                experimental_iterations += group_by_state(users_df, dataset=args.dataset)
        elif config['type'] == 'genre':
            for _ in range(args.num_samples):
                experimental_iterations += group_by_genre(
                    users_df=users_df, ratings_df=ratings_df, movies_df=movies_df,
                    dataset=args.dataset)
        elif config['type'] == 'genre_strict':
            for _ in range(args.num_samples):
                experimental_iterations += group_by_genre_strict(
                    users_df=users_df, ratings_df=ratings_df, movies_df=movies_df,
                    dataset=args.dataset)
        elif config['type'] == 'power':
            for _ in range(args.num_samples):
                experimental_iterations += group_by_power(users_df=users_df, ratings_df=ratings_df, dataset=args.dataset)
        elif config['type'] == 'occupation':
            for _ in range(args.num_samples):
                experimental_iterations += group_by_occupation(users_df)

        experiment_identifier_to_uid_sets = {}
        for algo_name in algos:
            prep_boycott_tasks = (
                delayed(prepare_boycott_task)(
                    i, experimental_iteration, args, config,
                    ratings_df, seed_base,
                    outname, algo_name, algos[algo_name], head_items, data
                ) for i, experimental_iteration in enumerate(experimental_iterations)
            )
            simulate_boycott_tasks = []
            tic = time.time()
            out = Parallel(n_jobs=-1, verbose=5, max_nbytes=None)((x for x in prep_boycott_tasks))
            for task_args, d in out:
                simulate_boycott_tasks.append(delayed(task)(*task_args))
                experiment_identifier_to_uid_sets.update(d)
            print('parallelized prep_boycott_task took {} seconds'.format(time.time() - tic))
            print('About to run Parallel() with {} tasks'.format(len(simulate_boycott_tasks)))
            out_dicts = Parallel(n_jobs=-1, verbose=5)((x for x in simulate_boycott_tasks))
            for d in out_dicts:
                res = d['subset_results']
                algo_name = d['algo_name']
                uid = str(d['identifier']) + '_' + d['algo_name']
                uid_to_error[uid] = {
                    'num_ratings': d['num_ratings'],
                    'num_users': d['num_users'],
                    'num_movies': d['num_movies'],
                    'name': d['name'],
                    'algo_name': d['algo_name'],
                }
                for metric in metric_names + ['fit_time', 'test_times', 'num_tested']:
                    for group in ['all', 'non-boycott', 'boycott', 'like-boycott', 'all-like-boycott']:
                        key = '{}_{}'.format(metric, group)
                        # if group in ['boycott', ]:
                        #     val = np.nanmean(res[key])
                        vals = res.get(key)
                        if vals:
                            val = np.mean(res[key])
                            uid_to_error[uid].update({
                                key: val,
                            })
                        standards_key = 'standards_' + key
                        standards_vals = res.get(standards_key)
                        if standards_vals:
                            standards_val = np.mean(res[standards_key])
                            uid_to_error[uid].update({
                                standards_key: standards_val,
                            })
        err_df = pd.DataFrame.from_dict(uid_to_error, orient='index')
        uid_sets_outname = outname.replace('results/', 'uid_sets/uid_sets_')
        pd.DataFrame.from_dict(experiment_identifier_to_uid_sets, orient='index').to_csv(uid_sets_outname)
        if args.movie_mean:
            outname = outname.replace('results/', 'results/MOVIEMEAN_')
        err_df.to_csv(outname)
        print('Full runtime was: {} for {} experimental iterations'.format(time.time() - times['start'], len(experimental_iterations)))


def parse():
    """
    Parse args and handles list splitting

    Example:
    python sandbox.py --grouping state

    python sandbox.py --grouping sample --sample_sizes 1 --num_samples 1 --dataset ml-1m --indices 0,0

    python sandbox.py --grouping sample --sample_sizes 1 --num_samples 1 --dataset ml-1m --compute_standards --indices 0,0
    python sandbox.py --grouping sample --sample_sizes 3 --num_samples 2 --dataset test_ml-1m --compute_standards --indices 1,2
    python sandbox.py --grouping sample --sample_sizes 3 --num_samples 250 --indices 251,500 --dataset ml-1m
    python sandbox.py --grouping sample --sample_sizes 2 --num_samples 2 --dataset ml-100k --indices 1,2
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--indices', help='either a comma separate pair of indices counting from 1 like 1,10. Can also be the string "all"')
    parser.add_argument('--grouping')
    parser.add_argument('--sample_sizes')
    parser.add_argument('--num_samples', type=int)
    parser.add_argument('--dataset', default='bcrossing')
    parser.add_argument(
        '--compute_standards', action='store_true',
        help='Defaults to false. Pass --compute_standards if you want to compute standards (you really only need to do this once)')
    parser.add_argument(
        '--load_predictions', action='store_true',
        help="Pass this argument if you want to try and load predictions. NOT CURRENTLY SUPPORTED.")
    parser.add_argument(
        '--num_standards', default=1, type=int,
        help='number of times to replicate standards calculation (to account for random fold shuffling)'
    )
    parser.add_argument(
        '--movie_mean', help='Defaults to False. If True, override everything and just use MovieMean and GlobalMean',
        action='store_true')
    parser.add_argument(
        '--send_to_out', help='Save all the outputs to a copy of the filesystem in the "/out" directory. The purpose is to make it easier to copy results to AWS s3 and merge results from spot instances',
        action='store_true')
    parser.add_argument(
        '--save_path', help='where to save predictions'
    )
    parser.add_argument(
        '--load_path', help='where to load standards predictions'
    )
    parser.add_argument(
        '--load_boycotts_path', help='where to load boycotts predictions'
    )

    parser.add_argument('--mode', default='compute')
    parser.add_argument('--userfrac', type=float, default=1.0)
    parser.add_argument('--ratingfrac', type=float, default=1.0)
    args = parser.parse_args()

    # check for errors in cli args
    if args.indices is None:
        raise ValueError("Please provide indices for this run. This will be used to help organize output files and determine seeds for PRNG.")
    if ',' in args.indices:
        args.indices = [int(x) for x in args.indices.split(',')]


    if args.sample_sizes:
        indices_coverage = args.indices[1] - args.indices[0] + 1
        if indices_coverage != args.num_samples:
            raise ValueError(
                'Indices cover {} boycott configs, but you selected {} samples. Please provide indices that match the number of samples selected'.format(
                    indices_coverage, args.num_samples,
                )
            )

    # make dirs as needed
    for name in [
        'logs',
        'results',
        'standard_results',
        'processed_results',
        'predictions',
        'predictions/standards',
        'predictions/boycotts',
        'uid_sets'
    ]:
        if args.send_to_out:
            directory = 'out/' + name
        else:
            directory = name
        if not os.path.exists(directory):
            print('Missing directory {}, going to create it.'.format(directory))
            os.makedirs(directory)
    logname = 'logs/{}.txt'.format(datetime.date.today())
    if args.send_to_out:
        logname = 'out/' + logname
    
    starttime = datetime.datetime.now()
    with open(logname, 'a') as f:
        msg = '{}\n{}\n\n'.format(str(starttime), str(args))
        f.write(msg)

    if args.sample_sizes:
        args.sample_sizes = [int(x) for x in args.sample_sizes.split(',')]
        if args.num_samples is None:
            args.num_samples = 1000
    else:
        if args.num_samples is None:
            args.num_samples = 1

    
    main(args)
    endtime = datetime.datetime.now()
    with open(logname, 'a') as f:
        msg = 'Finished at time {}\nTotal runtime was {}\n'.format(
            str(endtime), endtime - starttime
        )
        f.write(msg)


if __name__ == '__main__':
    parse()
