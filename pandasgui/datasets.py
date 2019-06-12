__all__ = ['iris','flights','multi','pokemon','all_datasets']

import seaborn as sns
import pandas as pd
import pkg_resources

data_path = pkg_resources.resource_filename(__name__, 'data/')


iris = sns.load_dataset('iris')
flights = sns.load_dataset('flights')
multi = flights.set_index(['year', 'month']).unstack()  # MultiIndex example
pokemon = pd.read_csv(data_path+"pokemon.csv")


# All data sets
all_datasets = {}
for name in sns.get_dataset_names():
    all_datasets[name] = sns.load_dataset(name)

all_datasets['pokemon'] = pokemon