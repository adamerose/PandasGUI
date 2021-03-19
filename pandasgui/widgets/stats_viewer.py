import sys
from typing import List
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from pandasgui.utility import nunique
from pandasgui.widgets.dataframe_viewer import DataFrameViewer
from pandasgui.widgets.grapher import Grapher
from pandasgui.widgets.reshaper import Reshaper
from pandasgui.widgets.filter_viewer import FilterViewer
from pandasgui.widgets.dock_widget import DockWidget
from pandasgui.store import PandasGuiDataFrameStore

import logging
logger = logging.getLogger(__name__)

class StatisticsViewer(QtWidgets.QWidget):
    def __init__(self, pgdf: PandasGuiDataFrameStore):
        super().__init__()

        pgdf = PandasGuiDataFrameStore.cast(pgdf)
        pgdf.dataframe_explorer = self
        self.pgdf = pgdf

        self.dataframe_viewer = DataFrameViewer(pgdf.column_statistics)

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.dataframe_viewer)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    from pandasgui.datasets import pokemon, mi_manufacturing, multiindex, simple

    view = StatisticsViewer(pokemon)
    view.pgdf.data_changed()
    view.show()
    app.exec_()
