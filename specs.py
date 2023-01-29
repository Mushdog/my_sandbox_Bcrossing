"""
Control specs here that affect many scripts throughout the project
"""
from surprise import SVD, Dataset, KNNBaseline, GuessThree, GlobalMean, MovieMean, KNNBasic, TwentyMean

# Notes on default algo params:
# KNN uses 40 max neighbors by default
# min neighbors is 1, and if there's no neighbors then use global average!
# default similarity is MSD
# default user or item is USER-BASED but we override that.

ALGOS = {
    #'SVD': SVD(random_state=0),
     'SVD': SVD(n_factors=15),
    #'KNNBasic_user_msd': KNNBasic(sim_options={'user_based': True}),
    #'KNNBasic_user_cosine': KNNBasic(sim_options={'user_based': True, 'name': 'cosine'}),
    #'KNNBasic_user_pearson': KNNBasic(sim_options={'user_based': True, 'name': 'pearson'}),
    #'KNNBasic_item_msd': KNNBasic(sim_options={'user_based': False}),
    #'KNNBasic_item_cosine': KNNBasic(sim_options={'user_based': False, 'name': 'cosine'}),
    # 'KNNBasic_item_pearson': KNNBasic(sim_options={'user_based': False, 'name': 'pearson'}),
    #'KNNBaseline_item_msd': KNNBaseline(sim_options={'user_based': False}),
}

ALGOS_FOR_STANDARDS = {
    # flag: uncomment when done
    #'SVD100': SVD(random_state=0),
    'SVD': SVD(n_factors=15),
    #'SVD10': SVD(n_factors=10),
    #'SVD20': SVD(n_factors=20),
    #'SVD8': SVD(n_factors=8),
    #'SVD30': SVD(n_factors=30),
    #'SVD40': SVD(n_factors=40),
    #'SVD50': SVD(n_factors=50),
    #'SVD70': SVD(n_factors=70),
    #'SVD90': SVD(n_factors=90),
    #'SVD110': SVD(n_factors=110),
    #'MovieMean': MovieMean(),
    #'KNNBasic_user_msd': KNNBasic(sim_options={'user_based': True}),
    #'KNNBasic_user_cosine': KNNBasic(sim_options={'user_based': True, 'name': 'cosine'}),
    #'KNNBasic_user_msd_10': KNNBasic(sim_options={'user_based': True}, k=10),
    #'KNNBasic_user_cosine_10': KNNBasic(sim_options={'user_based': True, 'name': 'cosine'}, k=10),
    #'KNNBasic_item_msd': KNNBasic(sim_options={'user_based': False}),
    #'KNNBasic_item_cosine': KNNBasic(sim_options={'user_based': False, 'name': 'cosine'}),
    #'KNNBaseline_item_msd': KNNBaseline(sim_options={'user_based': False}),
    #'GuessThree': GuessThree(),
    #'GlobalMean': GlobalMean(),
    #'TwentyMean': TwentyMean(),
}


NUM_FOLDS = 5
