# Get an application instance
from PyQt5 import QtWidgets, QtCore
from pandasgui import show
import pandas as pd
import numpy as np

app = QtWidgets.QApplication([])

for i in range(10):
    df = pd.DataFrame(np.random.rand(5, 5), columns=['col1', 'col2', 'col3', 'col4', 'col5'],
                      index=['A', 'B', 'C', 'D', 'E'])
    show(df, block=False)
app.exec_()
