"""Defines sample datasets for use in testing and demos"""

import seaborn as sns
import pandas as pd
import warnings

__all__ = ['all_datasets',
           'iris', 'flights', 'multi', 'pokemon', 'multidf', 'multidf_columns', 'multidf_index']

# This warning is given by sns.get_dataset_names
warnings.filterwarnings('ignore', message='No parser was explicitly specified')

iris = sns.load_dataset('iris')
flights = sns.load_dataset('flights')
multi = flights.set_index(['year', 'month']).unstack()  # MultiIndex example
pokemon = pd.read_csv(r'https://gist.githubusercontent.com/adamerose/'
                      r'400cb7025fa33ff4534f0b032b26321c/raw/6013206a582db794ed89fdf5e2c7567372489025/pokemon.csv')

tuples = [('A', 'one', 'x'), ('A', 'one', 'y'), ('A', 'two', 'x'), ('A', 'two', 'y'),
          ('B', 'one', 'x'), ('B', 'one', 'y'), ('B', 'two', 'x'), ('B', 'two', 'y')]
index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second', 'third'])
multidf = pd.DataFrame(pd.np.random.randn(8, 8), index=index[:8], columns=index[:8])
multidf_columns = pd.DataFrame(pd.np.random.randn(8, 8), columns=index[:8])
multidf_index = pd.DataFrame(pd.np.random.randn(8, 8), index=index[:8])

all_datasets = {}

# All Seaborn data sets
for name in sns.get_dataset_names():
    all_datasets[name] = sns.load_dataset(name)

all_datasets['pokemon'] = pokemon
all_datasets['multidf'] = multidf
all_datasets['multidf_columns'] = multidf_columns
all_datasets['multidf_index'] = multidf_index
