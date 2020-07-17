from pandasgui import show
import numpy as np
import pandas as pd

# Example 1 - Basic usage
df = pd.DataFrame(
    np.random.rand(5, 5),
    columns=["col1", "col2", "col3", "col4", "col5"],
    index=["A", "B", "C", "D", "E"],
)
show(df)

# Example 2 - Multiple DataFrames
from pandasgui.datasets import pokemon, titanic, mpg

show(pokemon, titanic, mileage=mpg)

# Example 3 - Multiple DataFrames with dictionary unpacking
from pandasgui.datasets import pokemon, titanic, mpg

df_dict = {"pokemon": pokemon, "titanic": titanic, "mileage": mpg}
show(**df_dict)
