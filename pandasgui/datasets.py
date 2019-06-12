__all__ = ['iris','flights','multi','pokemon']

import seaborn as sns
import pandas as pd
import pkg_resources

data_path = pkg_resources.resource_filename(__name__, 'data/')


iris = sns.load_dataset('iris')
flights = sns.load_dataset('flights')
multi = flights.set_index(['year', 'month']).unstack()  # MultiIndex example
pokemon = pd.read_csv(data_path+"pokemon.csv")