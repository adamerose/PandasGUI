# PandasGUI

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

example_df = pd.DataFrame(pd.np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
                          columns=['a', 'b', 'c'])
show(example_df)

```

Example of MultiIndex support, renaming, and nonblocking mode. Nonblocking mode opens the GUI in a separate process and allows you to continue running code in the console
```python
import seaborn as sns
from pandasgui import show

flights = sns.load_dataset('flights')
multi = flights.set_index(['year', 'month']).unstack()  # MultiIndex example
if __name__ == '__main__':  # This is needed when starting a new process. Not necessary in interactive console.
    show(flights, flightsReshaped=multi, nonblocking=True)

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

## Requirements
- pandas
- PyQt5
- seaborn

## Screenshots
DataFrame Viewer
![](https://raw.githubusercontent.com/adamerose/pandasgui/master/docs/screenshot1.png)
DataFrame Statistics
![](https://raw.githubusercontent.com/adamerose/pandasgui/master/docs/screenshot2.png)
Histogram Viewer
![](https://raw.githubusercontent.com/adamerose/pandasgui/master/docs/screenshot3.png)
DataFrame Viewer with MultIndex
![](https://raw.githubusercontent.com/adamerose/pandasgui/master/docs/screenshot4.png)