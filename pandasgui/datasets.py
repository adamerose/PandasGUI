# Some small datasets from https://github.com/adamerose/datasets

import os
import pandas as pd
from pandasgui.utility import get_logger
from appdirs import user_data_dir

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

local_data_dir = os.path.join(user_data_dir(), "pandasgui", "dataset_files")


def read_csv(path):
    if "mi_manufacturing" in path:
        return pd.read_csv(path, index_col=[0, 1, 2], header=[0, 1, 2])
    else:
        return pd.read_csv(path)


def to_csv(df, path):
    if "mi_manufacturing" in path:
        return df.to_csv(path, encoding='UTF-8')
    else:
        return df.to_csv(path, encoding='UTF-8', index=False)


for ix, name in enumerate(dataset_names):
    local_data_path = os.path.join(local_data_dir, f"{name}.csv")
    os.makedirs(local_data_dir, exist_ok=True)
    if os.path.exists(local_data_path):
        all_datasets[name] = read_csv(local_data_path)
    else:
        url = f"https://raw.githubusercontent.com/adamerose/datasets/master/{name}.csv"
        all_datasets[name] = read_csv(url)
        to_csv(all_datasets[name], local_data_path)
        logger.info(f"Saved {url} to {local_data_dir}")

# Add the datasets to globals so they can be imported like `from pandasgui.datasets import iris`
for name in all_datasets.keys():
    globals()[name] = all_datasets[name]
