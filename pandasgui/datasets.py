# Some small datasets from https://github.com/adamerose/datasets

import os
import pandas as pd
from pandasgui.utility import get_logger

logger = get_logger(__name__)

__all__ = ["all_datasets",

           "pokemon",
           "car_crashes",
           "iris",
           "mpg",
           "penguins",
           "tips",
           "titanic",
           "gapminder",
           "stockdata",
           "mi_manufacturing", ]

dataset_names = [x for x in __all__ if x != "all_datasets"]

all_datasets = {}


def read_csv(path):
    if "mi_manufacturing" in path:
        return pd.read_csv(path, index_col=[0, 1, 2], header=[0, 1, 2])
    else:
        return pd.read_csv(path)


for ix, name in enumerate(dataset_names):
    all_datasets[name] = read_csv(os.path.join("https://raw.githubusercontent.com/adamerose/datasets/master/",
                                               f"{name}.csv"))

# Add the datasets to globals so they can be imported like `from pandasgui.datasets import iris`
for name in all_datasets.keys():
    globals()[name] = all_datasets[name]
