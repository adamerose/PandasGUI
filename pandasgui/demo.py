import pandas as pd
from pandasgui import show
import seaborn as sns

# Sample data sets
from pandasgui.datasets import iris, flights, multi, pokemon

show(iris, flights, multi)

# View all Seaborn data sets
datasets = {}
for name in sns.get_dataset_names():
    datasets[name] = sns.load_dataset(name)

show(**datasets)
