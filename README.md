# PandasGUI

This project allows display and modification of Pandas DataFrames through a GUI based on PyQt5

## Installation

Run the following to install:

```python
pip install pandasgui
```

## Usage
###Basic
```python
import pandas as pd
from pandasgui import show

# Basic example with multiindex dataframe
arrays = [['bar', 'bar', 'baz', 'baz', 'foo', 'foo', 'qux', 'qux'],
         ['one', 'two', 'one', 'two', 'one', 'two', 'one', 'two']]
random_df = pd.DataFrame(pd.np.random.randn(8, 8), index=arrays, columns=arrays)
show(random_df)

```

###Advanced
```python
import pandas as pd
from pandasgui import show

# Example showing nonblocking instance, passing multiple dataframes, and custom names as kwargs
arrays = [['bar', 'bar', 'baz', 'baz', 'foo', 'foo', 'qux', 'qux'],
         ['one', 'two', 'one', 'two', 'one', 'two', 'one', 'two']]
random_df = pd.DataFrame(pd.np.random.randn(8, 8), index=arrays, columns=arrays)
random_df_2 = pd.DataFrame(pd.np.random.randn(8, 8)*10, index=arrays, columns=arrays)
random_df_long = pd.DataFrame(pd.np.random.randn(500, 8)*100, columns=arrays)
show(random_df_long, nonblocking=True)
show(custom_name_1=random_df, custom_name_2=random_df_2)

```
