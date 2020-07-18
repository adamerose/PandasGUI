# PandasGui

A GUI for viewing and analyzing Pandas DataFrames based on PyQt5.

<img src="https://raw.githubusercontent.com/adamerose/pandasgui/master/docs/screenshot1.png" alt="Screenshot" width="500"/>

## Installation

Install from PyPi:

```python
pip install pandasgui
```

Install directly from Github for the latest changes.

```python
pip install git+https://github.com/adamerose/pandasgui.git
```


## Usage
Create a simple DataFrame and view it in the GUI
```python
import pandas as pd
from pandasgui import show

example_df = pd.DataFrame(([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
                          columns=['a', 'b', 'c'])
show(example_df)
```

MultiIndexes are supported. And you can pass DataFrames as a kwarg if you want to show a name other than your variable.
```python
from pandasgui import show
from pandasgui.datasets import flights

multi = flights.set_index(['year', 'month']).unstack()  # MultiIndex example
show(flights, flightsReshaped=multi)
```

## About
This project is still in version 0.x.y and subject to major changes. Issues, feedback and forks are welcome. 
Latest changes will be on the develop branch, and this will be occasionally merged to master as a release with a
tag indicating the version number, and this will be what is available on PyPi.

## Features
- View DataFrames and Series
- MultiIndex support
- Copy & Paste from GUI
- Import CSV files with drag & drop
- Tabs showing column statistics and histograms


## Screenshots
DataFrame Viewer
![](https://raw.githubusercontent.com/adamerose/pandasgui/master/docs/screenshot1.png)
DataFrame Statistics
![](https://raw.githubusercontent.com/adamerose/pandasgui/master/docs/screenshot2.png)
Histogram Viewer
![](https://raw.githubusercontent.com/adamerose/pandasgui/master/docs/screenshot3.png)
DataFrame Viewer with MultIndex
![](https://raw.githubusercontent.com/adamerose/pandasgui/master/docs/screenshot4.png)