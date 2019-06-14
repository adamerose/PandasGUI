__all__ = ['iris', 'flights', 'multi', 'pokemon', 'multidf', 'all_datasets']

import seaborn as sns
import pandas as pd
import os

cwd = os.path.dirname(__file__)

iris = sns.load_dataset('iris')
flights = sns.load_dataset('flights')
multi = flights.set_index(['year', 'month']).unstack()  # MultiIndex example
pokemon = pd.read_csv(os.path.join(cwd, "data/pokemon.csv"))

tuples = [('A', 'one', 'x'), ('A', 'one', 'y'), ('A', 'two', 'x'), ('A', 'two', 'y'),
          ('B', 'one', 'x'), ('B', 'one', 'y'), ('B', 'two', 'x'), ('B', 'two', 'y')]
index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second', 'third'])
multidf = pd.DataFrame(pd.np.random.randn(8, 8), index=index[:8], columns=index[:8])

all_datasets = {}

# All Seaborn data sets
for name in sns.get_dataset_names():
    all_datasets[name] = sns.load_dataset(name)

all_datasets['pokemon'] = pokemon
all_datasets['multidf'] = multidf
