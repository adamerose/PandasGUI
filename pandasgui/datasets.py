import os
from typing import Dict, Union

import pandas as pd
import numpy as np
from pandasgui.constants import LOCAL_DATASET_DIR
import logging
from pandasgui.utility import SlicableOrderedDict
logger = logging.getLogger(__name__)




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


calculated_datasets = [
    "simple",
    "multiindex",
    "small",
    "unhashable"
]

csv_datasets = [
    "pokemon",
    "googleplaystore",
    "googleplaystore_reviews",
    "netflix_titles",
    "trump_tweets",
    "harry_potter_characters",
    "happiness",
    "country_indicators",
    "us_shooting_incidents",
    "stockdata",
    "gapminder",
    "anscombe",
    "attention",
    "brain_networks",
    "diamonds",
    "dots",
    "exercise",
    "flights",
    "fmri",
    "gammas",
    "geyser",
    "iris",
    "mpg",
    "penguins",
    "planets",
    "tips",
    "titanic",
    "seinfeld_episodes",
    "seinfeld_scripts",
    "mi_manufacturing"
]

__all__ = ["all_datasets",

           # csv_datasets
           "pokemon",
           "googleplaystore",
           "googleplaystore_reviews",
           "netflix_titles",
           "trump_tweets",
           "harry_potter_characters",
           "happiness",
           "country_indicators",
           "us_shooting_incidents",
           "stockdata",
           "gapminder",
           "anscombe",
           "attention",
           "brain_networks",
           "diamonds",
           "dots",
           "exercise",
           "flights",
           "fmri",
           "gammas",
           "geyser",
           "iris",
           "mpg",
           "penguins",
           "planets",
           "tips",
           "titanic",
           "seinfeld_episodes",
           "seinfeld_scripts",
           "mi_manufacturing",

           # calculated_datasets
           "simple",
           "multiindex",
           "small",
           "unhashable"
           ]


def __getattr__(name: str) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
    if name not in __all__:
        raise AttributeError

    elif name == 'all_datasets':
        all_datasets = SlicableOrderedDict()
        for n in csv_datasets + calculated_datasets:
            try:
                all_datasets[n] = __getattr__(n)
            except:
                # Don't want to completely fail to open PandasGUI if deprecated datasets aren't found
                logger.warning(f"Failed to load {name}.csv")
        return all_datasets

    # Download CSV files from Github repo, or open locally cached version
    elif name in csv_datasets:
        csv_path = os.path.join(LOCAL_DATASET_DIR, f"{name}.csv")
        csv_url = fr"https://raw.githubusercontent.com/adamerose/datasets/master/{name}.csv"
        if os.path.exists(csv_path):
            df = read_csv(csv_path)
        else:
            logger.info(f"Downloading {csv_url}")
            df = read_csv(csv_url)
            os.makedirs(LOCAL_DATASET_DIR, exist_ok=True)
            to_csv(df, csv_path)
            logger.info(f"Saved {name}.csv to {csv_path}")
        return df

    # Return calculated datasets
    elif name in calculated_datasets:
        if name == 'simple':
            return pd.DataFrame({'name': ['John', 'John', 'Mary', 'Mary', 'Pete', 'Pete', 'Mike', 'Mike'],
                                 'gender': ['m', 'm', 'f', 'f', 'm', 'm', 'm', 'm'],
                                 'trial': ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B'],
                                 'time': [473, 439, 424, 419, 433, 374, 434, 345],
                                 'points': [13, 16, 13, 18, 9, 20, 5, 18]}
                                )
        elif name == 'small':
            return pd.DataFrame({'a': [1, 2],
                                 'b': [3, 4]}
                                )
        elif name == 'multiindex':
            return pd.DataFrame(np.random.randn(8, 4),
                                index=pd.MultiIndex.from_product([('bar', 'baz', 'foo', 'qux'),
                                                                  ('one', 'two')],
                                                                 names=['first', 'second']),
                                columns=pd.MultiIndex.from_tuples([('A', 'cat'), ('B', 'dog'),
                                                                   ('B', 'cat'), ('A', 'dog')],
                                                                  names=['exp', 'animal']))
        elif name == 'unhashable':
            return pd.DataFrame({'lists': [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
                                 'dicts': [{'a': 1}, {'b': 2}, {'c': 3}],
                                 'dicts_of_lists': [{'a': [1, 2, 3]}, {'b': [4, 5, 6]}, {'c': [7, 8, 9]}],
                                 'sets': [{1, 2, 3}, {4, 5, 6}, {7, 8, 9}],
                                 'tuples': [(1, 2, 3), (4, 5, 6), (7, 8, 9)]
                                 }
                                )
