import sys
from typing import List
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from pandasgui.utility import get_logger
from pandasgui.widgets.dataframe_viewer import DataFrameViewer
from pandasgui.widgets.grapher import Grapher
from pandasgui.widgets.filter_viewer import FilterViewer
from pandasgui.widgets.dock_widget import DockWidget
from pandasgui.store import PandasGuiDataFrame

logger = get_logger(__name__)


class DataFrameExplorer(QtWidgets.QMainWindow):
    def __init__(self, pgdf: PandasGuiDataFrame):
        super().__init__()

        pgdf = PandasGuiDataFrame.cast(pgdf)
        pgdf.dataframe_explorer = self
        self.pgdf = pgdf

        # Dock setup
        self.docks: List[DockWidget] = []
        self.setDockOptions(self.GroupedDragging | self.AllowTabbedDocks | self.AllowNestedDocks)
        self.setTabPosition(Qt.AllDockWidgetAreas, QtWidgets.QTabWidget.North)

        # DataFrame tab
        self.dataframe_tab = DataFrameViewer(pgdf)
        self.add_view(self.dataframe_tab, "DataFrame")

        # Filters tab
        self.filters_tab = FilterViewer(pgdf)
        self.add_view(self.filters_tab, "Filters")

        # Statistics tab
        self.statistics_tab = self.make_statistics_tab(pgdf)
        self.add_view(self.statistics_tab, "Statistics")

        # Grapher tab
        graph_maker = Grapher(pgdf)
        self.add_view(graph_maker, "Grapher")

    def add_view(self, widget: QtWidgets.QWidget, title: str):
        dock = DockWidget(title)
        dock.setAllowedAreas(Qt.AllDockWidgetAreas)

        frame = QtWidgets.QFrame()
        frame.setFrameStyle(frame.Box | frame.Raised)
        frame.setLineWidth(2)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(widget)
        frame.setLayout(layout)
        dock.setWidget(frame)

        if len(self.docks) > 0:
            self.tabifyDockWidget(self.docks[0], dock)
            # Keep the first tab active by default
            self.docks[0].raise_()
        else:
            self.addDockWidget(Qt.TopDockWidgetArea, dock)

        self.docks.append(dock)

    def __reduce__(self):
        # This is so dataclasses.asdict doesn't complain about this being unpicklable
        return "DataFrameExplorer"

    def make_statistics_tab(self, pgdf: PandasGuiDataFrame):
        stats_df = pd.DataFrame(
            {
                "Type": pgdf.dataframe.dtypes.replace("object", "string").astype(str),
                "Count": pgdf.dataframe.count(),
                "N Unique": pgdf.dataframe.nunique(),
                "Mean": pgdf.dataframe.mean(numeric_only=True),
                "StdDev": pgdf.dataframe.std(numeric_only=True),
                "Min": pgdf.dataframe.min(numeric_only=True),
                "Max": pgdf.dataframe.max(numeric_only=True),
            }
        )

        stats_pgdf = PandasGuiDataFrame(stats_df.reset_index())
        w = DataFrameViewer(stats_pgdf)
        w.setAutoFillBackground(True)
        return w


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    from pandasgui.datasets import pokemon

    # Create and show widget
    dfe = DataFrameExplorer(pokemon)
    dfe.show()

    sys.exit(app.exec_())
