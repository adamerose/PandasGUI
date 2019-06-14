# PandasGUI

A GUI for viewing and analyzing Pandas DataFrames based on PyQt5.

<img src="https://raw.githubusercontent.com/adamerose/pandasgui/master/docs/gallery1.png" alt="Screenshot" width="500"/>

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
View the *iris* and *flights* DataFrames in PandasGUI
```python
import seaborn as sns
from pandasgui import show

iris = sns.load_dataset('iris')
flights = sns.load_dataset('flights')
show(iris,flights)

```

Example of MultiIndex support, renaming, and nonblocking mode. Nonblocking mode opens the GUI in a separate process and allows you to continue running code in the console
```python
import seaborn as sns
from pandasgui import show

flights = sns.load_dataset('flights')
multi = flights.set_index(['year', 'month']).unstack()  # MultiIndex example
show(flights, flightsReshaped=multi, nonblocking=True)

```

## About
This project is still in version 0.x.y and subject to major changes. Issues, feedback and forks are welcome. 

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
![](https://raw.githubusercontent.com/adamerose/pandasgui/master/docs/gallery1.png)
DataFrame Statistics
![](https://raw.githubusercontent.com/adamerose/pandasgui/master/docs/gallery2.png)
Histogram Viewer
![](https://raw.githubusercontent.com/adamerose/pandasgui/master/docs/gallery3.png)
DataFrame Viewer with MultIndex
![](https://raw.githubusercontent.com/adamerose/pandasgui/master/docs/gallery1.png)