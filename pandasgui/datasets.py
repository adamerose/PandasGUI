# Some small datasets from https://github.com/adamerose/datasets

import os
import shutil
import pandas as pd
import numpy as np
from pandasgui.constants import LOCAL_DATASET_DIR
import logging

logger = logging.getLogger(__name__)

__all__ = ["all_datasets",
           "simple",
           "multiindex",

           "pokemon",
           "car_crashes",
           "iris",
           "mpg",
           "penguins",
           "tips",
           "titanic",
           "gapminder",
           "stockdata",
           "trump_tweets",
           "mi_manufacturing"]

dataset_names = ["pokemon",
                 "car_crashes",
                 "iris",
                 "mpg",
                 "penguins",
                 "tips",
                 "titanic",
                 "gapminder",
                 "stockdata",
                 "trump_tweets",
                 "mi_manufacturing"]

all_datasets = {}


def read_csv(path):
    if "mi_manufacturing" in path:
        return pd.read_csv(path, index_col=[0, 1, 2], header=[0, 1, 2])
    if "stockdata" in path:
        return pd.read_csv(path, parse_dates=['Date'])
    if "trump_tweets" in path:
        return pd.read_csv(path, parse_dates=['date'])
    else:
        return pd.read_csv(path)


def to_csv(df, path):
    if "mi_manufacturing" in path:
        return df.to_csv(path, encoding='UTF-8')
    else:
        return df.to_csv(path, encoding='UTF-8', index=False)


for ix, name in enumerate(dataset_names):
    local_data_path = os.path.join(LOCAL_DATASET_DIR, f"{name}.csv")
    os.makedirs(LOCAL_DATASET_DIR, exist_ok=True)
    if os.path.exists(local_data_path):
        all_datasets[name] = read_csv(local_data_path)
    else:
        url = f"https://raw.githubusercontent.com/adamerose/datasets/master/{name}.csv"
        all_datasets[name] = read_csv(url)
        to_csv(all_datasets[name], local_data_path)
        logger.info(f"Saved {url} to {LOCAL_DATASET_DIR}")

simple = pd.DataFrame({'name': ['John', 'John', 'Mary', 'Mary', 'Pete', 'Pete', 'Mike', 'Mike'],
                       'gender': ['m', 'm', 'f', 'f', 'm', 'm', 'm', 'm'],
                       'trial': ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B'],
                       'time': [473, 439, 424, 419, 433, 374, 434, 345],
                       'points': [13, 16, 13, 18, 9, 20, 5, 18]}
                      )
all_datasets['simple'] = simple

multiindex = pd.DataFrame(np.random.randn(8, 4),
                          index=pd.MultiIndex.from_product([('bar', 'baz', 'foo', 'qux'),
                                                            ('one', 'two')],
                                                           names=['first', 'second']),
                          columns=pd.MultiIndex.from_tuples([('A', 'cat'), ('B', 'dog'),
                                                             ('B', 'cat'), ('A', 'dog')],
                                                            names=['exp', 'animal']))
all_datasets['multiindex'] = multiindex

unhashable = pd.DataFrame({'lists': [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
                           'dicts': [{'a': 1}, {'b': 2}, {'c': 3}],
                           'dicts_of_lists': [{'a': [1, 2, 3]}, {'b': [4, 5, 6]}, {'c': [7, 8, 9]}],
                           'sets': [{1, 2, 3}, {4, 5, 6}, {7, 8, 9}],
                           'tuples': [(1, 2, 3), (4, 5, 6), (7, 8, 9)]
                           }
                          )
all_datasets['unhashable'] = unhashable

# Add the datasets to globals so they can be imported like `from pandasgui.datasets import iris`
for name in all_datasets.keys():
    globals()[name] = all_datasets[name]
