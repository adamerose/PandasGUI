# PandasGui

A GUI built with PyQt5 for analyzing Pandas DataFrames.

<img src="https://raw.githubusercontent.com/adamerose/pandasgui/develop/screenshots/dataframe.png" alt="Screenshot" width="500"/>

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

Or if you are running your code as a script instead of within iPython, you will need to block execution until you close the GUI
```python
show(df, block=True)
```

PandasGUI comes with sample datasets that will automatically download on first usage
```python
from pandasgui import show
from pandasgui.datasets import pokemon, titanic
show(pokemon, titanic)
```

This module also exports `all_datasets` which is a dictionary of all the sample datasets
```python
from pandasgui import show 
from pandasgui.datasets import all_datasets
show(**all_datasets)
```

## Demo
![Demo](https://s8.gifyu.com/images/demo.gif)

## Features
- View DataFrames and Series (with MultiIndex support)
- Filtering
- Interactive plotting
- Statistics summary
- Data editing and copy / paste
- Import CSV files with drag & drop


## Screenshots
DataFrame Viewer  

<img src="https://raw.githubusercontent.com/adamerose/pandasgui/develop/screenshots/dataframe.png" alt="Screenshot" width="500"/>

Filters  

<img src="https://raw.githubusercontent.com/adamerose/pandasgui/develop/screenshots/filters.png" alt="Screenshot" width="500"/>


Statistics  

<img src="https://raw.githubusercontent.com/adamerose/pandasgui/develop/screenshots/statistics.png" alt="Screenshot" width="500"/>

Grapher  

<img src="https://raw.githubusercontent.com/adamerose/pandasgui/develop/screenshots/grapher.png" alt="Screenshot" width="500"/>

MultiIndex Support  

<img src="https://raw.githubusercontent.com/adamerose/pandasgui/develop/screenshots/multi_index.png" alt="Screenshot" width="500"/>

## More Info
This project is still in version 0.x.y and still subject to major changes. Issues, feedback and pull requests are welcome. 
Latest changes will be on the develop branch, and this will be occasionally merged to master as a release with a
tag indicating the version number, and this will be what is available on PyPi.
