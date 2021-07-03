import sys
from typing import List
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from pandasgui.widgets.containers import Container
from pandasgui.widgets.dataframe_viewer import DataFrameViewer
from pandasgui.widgets.column_viewer import ColumnViewer
from pandasgui.widgets.grapher import Grapher
from pandasgui.widgets.reshaper import Reshaper
from pandasgui.widgets.filter_viewer import FilterViewer
from pandasgui.widgets.stats_viewer import StatisticsViewer
from pandasgui.widgets.dock_widget import DockWidget
from pandasgui.store import PandasGuiDataFrameStore

import logging

logger = logging.getLogger(__name__)


class DataFrameExplorer(QtWidgets.QWidget):
    def __init__(self, pgdf: PandasGuiDataFrameStore):
        super().__init__()

        pgdf = PandasGuiDataFrameStore.cast(pgdf)
        pgdf.dataframe_explorer = self
        self.pgdf = pgdf

        ##################
        # Set up main views in Dock tabs
        self.main_window = QtWidgets.QMainWindow()
        self.docks: List[DockWidget] = []
        self.main_window.setDockOptions(
            self.main_window.GroupedDragging | self.main_window.AllowTabbedDocks | self.main_window.AllowNestedDocks)
        self.main_window.setTabPosition(Qt.AllDockWidgetAreas, QtWidgets.QTabWidget.North)

        self.dataframe_viewer = DataFrameViewer(pgdf)
        self.statistics_viewer = StatisticsViewer(pgdf)
        self.grapher = Grapher(pgdf)
        self.reshaper = Reshaper(pgdf)

        self.dataframe_dock = self.add_view(self.dataframe_viewer, "DataFrame")
        self.statistics_dock = self.add_view(self.statistics_viewer, "Statistics")
        self.grapher_dock = self.add_view(self.grapher, "Grapher")
        self.reshaper_dock = self.add_view(self.reshaper, "Reshaper")

        def set_active_tab(name):
            self.active_tab = name

        self.dataframe_dock.activated.connect(lambda: set_active_tab("DataFrame"))
        self.statistics_dock.activated.connect(lambda: set_active_tab("Statistics"))
        self.grapher_dock.activated.connect(lambda: set_active_tab("Grapher"))
        self.reshaper_dock.activated.connect(lambda: set_active_tab("Reshaper"))

        self.dataframe_viewer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        ##################
        # Non-Dock widgets

        self.filter_viewer = FilterViewer(pgdf)
        self.column_viewer = ColumnArranger(self.pgdf)

        ##################
        # Set up overall layout

        self.splitter = QtWidgets.QSplitter(Qt.Horizontal)
        self.side_bar = QtWidgets.QSplitter(Qt.Vertical)

        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.splitter)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.filter_viewer_container = Container(self.filter_viewer, "Filters")

        self.splitter.addWidget(self.side_bar)
        self.splitter.addWidget(self.main_window)
        self.side_bar.addWidget(self.filter_viewer_container)
        self.side_bar.addWidget(Container(self.column_viewer, "Columns"))

    # Add a dock to the MainWindow widget
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
            self.main_window.tabifyDockWidget(self.docks[0], dock)
            # Keep the first tab active by default
            self.docks[0].raise_()
        else:
            self.main_window.addDockWidget(Qt.LeftDockWidgetArea, dock)

        self.docks.append(dock)
        return dock


class ColumnArranger(ColumnViewer):

    def __init__(self, pgdf: PandasGuiDataFrameStore):
        super().__init__(pgdf)
        pgdf = PandasGuiDataFrameStore.cast(pgdf)
        self.pgdf = pgdf

        self.tree.setAcceptDrops(True)
        self.tree.setDragEnabled(True)
        self.tree.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.tree.setHeaderLabels(['Name'])
        self.refresh()

        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.tree.onDropSignal.connect(self.columns_rearranged)
        self.tree.itemDoubleClicked.connect(self.on_double_click)

        self.tree.mouseReleaseEventSignal.connect(self.on_mouseReleaseEvent)

    def on_double_click(self, item: QtWidgets.QTreeWidgetItem):
        ix = self.tree.indexOfTopLevelItem(item)
        self.pgdf.dataframe_viewer.scroll_to_column(ix)

    def columns_rearranged(self):
        items = [self.tree.topLevelItem(x).text(0) for x in range(self.tree.topLevelItemCount())]
        self.pgdf.reorder_columns(items)

    def on_mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            pos = event.pos()
            item = self.tree.itemAt(pos)
            ix = self.tree.indexAt(pos)
            ix_list = [self.tree.indexOfTopLevelItem(x) for x in self.tree.selectedItems()]
            if item:
                menu = QtWidgets.QMenu(self.tree)

                action1 = QtWidgets.QAction("Move To Front")
                action1.triggered.connect(lambda: self.pgdf.move_columns(ix_list, 0, True))

                action2 = QtWidgets.QAction("Move To End")
                action2.triggered.connect(
                    lambda: self.pgdf.move_columns(ix_list, len(self.pgdf.df_unfiltered.columns), True))

                for action in [action1, action2]:
                    menu.addAction(action)

                menu.exec_(QtGui.QCursor().pos())

        super().mouseReleaseEvent(event)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    from pandasgui.datasets import pokemon

    # Create and show widget
    dfe = DataFrameExplorer(pokemon)
    dfe.show()

    sys.exit(app.exec_())
