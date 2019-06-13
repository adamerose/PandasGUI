__all__ = ['iris','flights','multi','pokemon','all_datasets']

import seaborn as sns
import pandas as pd
import os
cwd = os.path.dirname(__file__)

iris = sns.load_dataset('iris')
flights = sns.load_dataset('flights')
multi = flights.set_index(['year', 'month']).unstack()  # MultiIndex example
pokemon = pd.read_csv(os.path.join(cwd,"data/pokemon.csv"))

all_datasets = {}


# All Seaborn data sets
for name in sns.get_dataset_names():
    all_datasets[name] = sns.load_dataset(name)

all_datasets['pokemon'] = pokemon