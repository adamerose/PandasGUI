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

class DataFrameExplorer(QtWidgets.QMainWindow):
    def __init__(self, pgdf: PandasGuiDataFrameStore):
        super().__init__()

        pgdf = PandasGuiDataFrameStore.cast(pgdf)
        pgdf.dataframe_explorer = self
        self.pgdf = pgdf

        # Dock setup
        self.docks: List[DockWidget] = []
        self.setDockOptions(self.GroupedDragging | self.AllowTabbedDocks | self.AllowNestedDocks)
        self.setTabPosition(Qt.AllDockWidgetAreas, QtWidgets.QTabWidget.North)

        # DataFrame tab
        self.dataframe_viewer = DataFrameViewer(pgdf)
        self.dataframe_dock = self.add_view(self.dataframe_viewer, "DataFrame")

        # Filters tab
        self.filter_viewer = FilterViewer(pgdf)
        self.filters_dock = self.add_view(self.filter_viewer, "Filters")

        # Statistics tab
        self.statistics_viewer = self.make_statistics_tab(pgdf)
        self.statistics_dock = self.add_view(self.statistics_viewer, "Statistics")

        # Grapher tab
        self.grapher = Grapher(pgdf)
        self.grapher_dock = self.add_view(self.grapher, "Grapher")

        # Reshaper tab
        self.reshaper = Reshaper(pgdf)
        self.reshaper_dock = self.add_view(self.reshaper, "Reshaper")

        def set_active_tab(name):
            self.active_tab = name
        self.dataframe_dock.activated.connect(lambda: set_active_tab("DataFrame"))
        self.filters_dock.activated.connect(lambda: set_active_tab("Filters"))
        self.statistics_dock.activated.connect(lambda: set_active_tab("Statistics"))
        self.grapher_dock.activated.connect(lambda: set_active_tab("Grapher"))
        self.reshaper_dock.activated.connect(lambda: set_active_tab("Reshaper"))

        # Layout
        self.dataframe_viewer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.addDockWidget(Qt.RightDockWidgetArea, self.filters_dock)

    def add_view(self, widget: QtWidgets.QWidget, title: str):
        dock = DockWidget(title, self.pgdf.name)
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
            self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        self.docks.append(dock)
        return dock

    def __reduce__(self):
        # This is so dataclasses.asdict doesn't complain about this being unpicklable
        return "DataFrameExplorer"

    def make_statistics_tab(self, pgdf: PandasGuiDataFrameStore):

        stats_df = pd.DataFrame(
            {
                "Type": pgdf.df.dtypes.replace("object", "string").astype(str),
                "Count": pgdf.df.count(),
                "N Unique": nunique(pgdf.df),
                "Mean": pgdf.df.mean(numeric_only=True),
                "StdDev": pgdf.df.std(numeric_only=True),
                "Min": pgdf.df.min(numeric_only=True),
                "Max": pgdf.df.max(numeric_only=True),
            },
            index=pgdf.df.columns
        )

        self.stats_pgdf = PandasGuiDataFrameStore(stats_df.reset_index())
        w = DataFrameViewer(self.stats_pgdf)
        w.setAutoFillBackground(True)
        return w


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    from pandasgui.datasets import pokemon

    # Create and show widget
    dfe = DataFrameExplorer(pokemon)
    dfe.show()

    sys.exit(app.exec_())
