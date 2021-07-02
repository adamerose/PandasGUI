import sys
from PyQt5 import QtWidgets

from pandasgui.utility import clear_layout
from pandasgui.widgets.dataframe_viewer import DataFrameViewer
from pandasgui.store import PandasGuiDataFrameStore

import logging

logger = logging.getLogger(__name__)


class StatisticsViewer(QtWidgets.QWidget):
    def __init__(self, pgdf: PandasGuiDataFrameStore):
        super().__init__()
        pgdf = PandasGuiDataFrameStore.cast(pgdf)
        self.pgdf = pgdf

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.dataframe_viewer = DataFrameViewer(self.pgdf.column_statistics)
        self.layout.addWidget(self.dataframe_viewer)

    # Replace the data in self.dataframe_viewer pgdf with the current statistics of the main pgdf
    def refresh_statistics(self):
        # self.dataframe_viewer.pgdf.paste_data(0, 0, self.pgdf.column_statistics)
        clear_layout(self.layout)
        self.dataframe_viewer = DataFrameViewer(self.pgdf.column_statistics)
        self.layout.addWidget(self.dataframe_viewer)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    from pandasgui.datasets import pokemon

    view = StatisticsViewer(pokemon)
    view.pgdf.data_changed()
    view.show()
    app.exec_()
