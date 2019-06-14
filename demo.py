import pandas as pd
import seaborn as sns
from pandasgui import show

import warnings

# warnings.filterwarnings('error')

case = 1

if case == 1:
    # Sample data sets
    from pandasgui.datasets import iris, flights, multi, pokemon

    show(iris, flights, multi)

if case == 2:
    # View all Seaborn data sets
    datasets = {}
    for name in sns.get_dataset_names():
        datasets[name] = sns.load_dataset(name)

    show(**datasets)
