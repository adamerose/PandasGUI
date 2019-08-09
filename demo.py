# View all example datasets
from PyQt5 import QtWebEngineWidgets

from pandasgui import show
import numpy as np
import pandas as pd
import seaborn as sns

# Example 1 - Basic usage
df = pd.DataFrame(np.random.rand(5, 5), columns=['col1', 'col2', 'col3', 'col4', 'col5'],
                  index=['A', 'B', 'C', 'D', 'E'])
show(df)

# Example 2 - View all Seaborn datasets
all_datasets = {}
for name in sns.get_dataset_names():
    all_datasets[name] = sns.load_dataset(name)

show(**all_datasets)

# Example 3 - DataFrame with MultiIndex
tuples = [('A', 'one', 'x'), ('A', 'one', 'y'), ('A', 'two', 'x'), ('A', 'two', 'y'),
          ('B', 'one', 'x'), ('B', 'one', 'y'), ('B', 'two', 'x'), ('B', 'two', 'y')]
index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second', 'third'])
multidf = pd.DataFrame(pd.np.random.randn(8, 8), index=index[:8], columns=index[:8])

show(multidf)
