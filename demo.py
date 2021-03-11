# Open PandasGUI by passing one or more DataFrames to `show`. The name in the GUI will be matched to the variable name.
import pandas as pd
from pandasgui import show
df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6], 'c': [7, 8, 9]})
show(df)

# PandasGUI comes with sample datasets which get downloaded on first import.
# This includes `all_datasets` which is a dictionary of all the sample datasets like Dict[str, DataFrame]
# You can pass DataFrames as kwargs to specify different names. This also works with dictionary unpacking
from pandasgui.datasets import pokemon, mpg, multiindex, all_datasets
show(pokemon_stats=pokemon, mi_example=multiindex)
show(**all_datasets)

# The only reserved argument name is `settings`, which accepts a dictionary of settings for the GUI.
show(pokemon, settings={'theme':'dark', ''})
# PandasGUI will attempt to convert any object you pass to `show` into a DataFrame
show(test1={'a': [1, 2, 3]}, test2=[5, 6, 7, 8, 9])

# Read DataFrames from the GUI using square brackets
gui = show(pokemon, mpg)
pokemon_new = gui['pokemon']

# Use the `pg` IPython magic command to directly modify DataFrames in the GUI
%pg pokemon['Null Type'] = pokemon['Type 1'].isna()