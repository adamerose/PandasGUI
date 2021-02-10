# PandasGUI

A GUI for analyzing Pandas DataFrames.

## Demo

[![PandasGUI Demo](https://i.imgur.com/u3BzdoS.png)](https://www.youtube.com/watch?v=NKXdolMxW2Y "PandasGUI Demo")

## Installation

Install latest release from PyPi:

```shell
pip install pandasgui
```

Install directly from Github for the latest unreleased changes:

```shell
pip install git+https://github.com/adamerose/pandasgui.git
```

## Usage

Create and view a simple DataFrame

```python
import pandas as pd
from pandasgui import show
df = pd.DataFrame(([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), columns=['a', 'b', 'c'])
show(df)
```

PandasGUI comes with sample datasets that will download on first use.   
You can also import `all_datasets` which is a dictionary of all the sample datasets

```python
from pandasgui import show
from pandasgui.datasets import pokemon, titanic, all_datasets
show(**all_datasets)
```

## Features

- View DataFrames and Series (with MultiIndex support)
- Interactive plotting
- Filtering
- Statistics summary
- Data editing and copy / paste
- Import CSV files with drag & drop
- Search toolbar

## More Info

**Issues, feedback and pull requests are welcome.**

This project is still in version 0.x.y and subject to breaking changes. The latest changes will be on the `develop` branch, and will be occasionally merged to `master` as a release with a tag indicating the version number and published to PyPi.

If you like this project remember to leave a ⭐! And if you want to give more support you can <a href="https://www.buymeacoffee.com/adrotog" target="_blank">Buy Me A Coffee</a>.
