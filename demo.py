from pandasgui import show
from pandasgui.datasets import all_datasets

show(**all_datasets, settings={'block': True})
