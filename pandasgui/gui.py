import inspect
import os
import sys
import pprint
from typing import Union, Iterable, Callable
from dataclasses import dataclass
import pandas as pd
import pkg_resources
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from pandasgui.store import Store, PandasGuiDataFrame
from pandasgui.utility import fix_ipython, fix_pyqt, get_logger, as_dict
from pandasgui.widgets.dataframe_explorer import DataFrameExplorer
from pandasgui.widgets.find_toolbar import FindToolbar
from pandasgui.widgets.json_viewer import JsonViewer

logger = get_logger(__name__)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


# Set the exception hook to our wrapping function
sys.excepthook = except_hook

# Enables PyQt event loop in IPython
fix_ipython()

# Keep a list of PandasGui widgets so they don't get garbage collected
refs = []


class PandasGui(QtWidgets.QMainWindow):
    def __init__(self, settings: dict = {}, **kwargs):
        """
        Args:
            settings: Dict of settings, as defined in pandasgui.store.Settings
            kwargs: Dict of DataFrames where key is name & val is the DataFrame object
        """
        refs.append(self)
        self.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        self.store = Store()
        self.store.gui = self

        super().__init__()
        self.init_app()
        self.init_ui()

        # Add user provided settings to data store
        for key, value in settings.items():
            setattr(self.store.settings, key, value)

        # Adds DataFrames listed in kwargs to data store.
        for df_name, df in kwargs.items():
            self.store.add_dataframe(df, df_name)

        # Default to first item
        self.stacked_widget.setCurrentWidget(self.store.data[0].dataframe_explorer)
        self.nav_tree.setCurrentItem(self.nav_tree.topLevelItem(0))

        # Start event loop if blocking enabled
        if self.store.settings.block:
            self.app.exec_()

    # Configure app settings
    def init_app(self):

        self.resize(QtCore.QSize(int(0.7 * QtWidgets.QDesktopWidget().screenGeometry().width()),
                                 int(0.7 * QtWidgets.QDesktopWidget().screenGeometry().height())))

        # Center window on screen
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(
            int((screen.width() - size.width()) / 2),
            int((screen.height() - size.height()) / 2),
        )

        # Set window title and icon
        self.setWindowTitle("PandasGui")
        pdgui_icon = "images/icon.png"
        pdgui_icon_path = pkg_resources.resource_filename(__name__, pdgui_icon)
        self.app.setWindowIcon(QtGui.QIcon(pdgui_icon_path))

        self.show()

    # Create and add all widgets to GUI.
    def init_ui(self):
        # This holds the DataFrameExplorer for each DataFrame
        self.stacked_widget = QtWidgets.QStackedWidget()

        # Make the navigation bar
        self.nav_tree = self.NavWidget(self)
        # Creates the headers.
        self.nav_tree.setHeaderLabels(["Name", "Shape"])
        self.nav_tree.itemSelectionChanged.connect(self.nav_clicked)

        # Make splitter to hold nav and DataFrameExplorers
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.nav_tree)
        self.splitter.addWidget(self.stacked_widget)

        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        nav_width = self.nav_tree.sizeHint().width()
        self.splitter.setSizes([nav_width, self.width() - nav_width])
        self.splitter.setContentsMargins(10, 10, 10, 10)

        # makes the find toolbar
        self.find_bar = FindToolbar(self)
        self.addToolBar(self.find_bar)

        # QMainWindow setup
        self.make_menu_bar()
        self.setCentralWidget(self.splitter)

    def import_dataframe(self, path):
        self.store.import_dataframe(path)

    ####################
    # Menu bar functions

    def make_menu_bar(self):
        menubar = self.menuBar()

        @dataclass
        class MenuItem:
            name: str
            func: Callable
            shortcut: str = ''

        items = {'Edit': [MenuItem(name='Find',
                                   func=self.find_bar.show_find_bar,
                                   shortcut='Ctrl+F')],
                 'Debug': [MenuItem(name='Print Data Store',
                                    func=self.print_store),
                           MenuItem(name='View Data Store',
                                    func=self.view_store),
                           MenuItem(name='Print History (for current DataFrame)',
                                    func=self.print_history)
                           ],
                 'Set Style': []}

        # Add an option to the menu for each GUI style that exist for the user's system
        for ix, style in enumerate(QtWidgets.QStyleFactory.keys()):
            items['Set Style'].append(
                MenuItem(name=style,
                         func=lambda x=style: self.app.setStyle(x),
                         )
            )

            # Set the default style to the last in the options
            self.app.setStyle(QtWidgets.QStyleFactory.keys()[-1])

        # Add menu items and actions to UI using the schema defined above
        for menu_name in items.keys():
            menu = menubar.addMenu(menu_name)
            for x in items[menu_name]:
                action = QtWidgets.QAction(x.name, self)
                action.setShortcut(x.shortcut)
                action.triggered.connect(x.func)
                menu.addAction(action)

    class NavWidget(QtWidgets.QTreeWidget):
        def __init__(self, gui):
            super().__init__()
            self.gui = gui
            self.setHeaderLabels(["HeaderLabel"])
            self.expandAll()
            self.setAcceptDrops(True)

            for i in range(self.columnCount()):
                self.resizeColumnToContents(i)

            self.setColumnWidth(0, 150)
            self.setColumnWidth(1, 150)

        def rowsInserted(self, parent: QtCore.QModelIndex, start: int, end: int):
            super().rowsInserted(parent, start, end)
            self.expandAll()

        def sizeHint(self):
            # Width
            width = 0
            for i in range(self.columnCount()):
                width += self.columnWidth(i)
            return QtCore.QSize(300, 500)

        def dragEnterEvent(self, e):
            if e.mimeData().hasUrls:
                e.accept()
            else:
                e.ignore()

        def dragMoveEvent(self, e):
            if e.mimeData().hasUrls:
                e.accept()
            else:
                e.ignore()

        def dropEvent(self, e):
            if e.mimeData().hasUrls:
                e.setDropAction(QtCore.Qt.CopyAction)
                e.accept()
                fpath_list = []
                for url in e.mimeData().urls():
                    fpath_list.append(str(url.toLocalFile()))

                for fpath in fpath_list:
                    self.gui.import_dataframe(fpath)
            else:
                e.ignore()

    def add_df_to_nav(self, df_name, parent=None):
        if parent is None:
            parent = self.nav_tree

        # Calculate and format the shape of the DataFrame
        shape = self.store.get_pgdf(df_name).dataframe.shape
        shape = str(shape[0]) + " X " + str(shape[1])

        item = QtWidgets.QTreeWidgetItem(parent, [df_name, shape])
        self.nav_tree.itemSelectionChanged.emit()
        self.nav_tree.setCurrentItem(item)

    def nav_clicked(self):
        """
        Show the DataFrameExplorer corresponding to the highlighted nav item.
        """
        try:
            item = self.nav_tree.selectedItems()[0]
        except IndexError:
            return

        df_name = item.data(0, Qt.DisplayRole)

        dfe = self.store.get_pgdf(df_name).dataframe_explorer
        self.stacked_widget.setCurrentWidget(dfe)

    def print_store(self):
        d = as_dict(self.store)
        pprint.pprint(d)

    def print_history(self):
        pgdf = self.store.data[self.stacked_widget.currentIndex()]
        if len(pgdf.history) == 0:
            print(f"No actions recorded yet for {pgdf.name}")
        else:
            header = f'---- History ({pgdf.name}) ----'
            print(header)
            for h in pgdf.history:
                print(h)
            print('-' * len(header))

    def view_store(self):
        d = as_dict(self.store)
        print(d)
        self.store_viewer = JsonViewer(d)
        self.store_viewer.show()

    # Return all DataFrames, or a subset specified by names. Returns a dict of name:df or a single df if there's only 1
    def get_dataframes(self, names: Union[None, str, list] = None):
        self.store.get_dataframes(names)


def show(*args,
         settings: dict = {},
         **kwargs):
    # Get the variable names in the scope show() was called from
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()

    # Make a dictionary of the DataFrames from the position args and get their variable names using inspect
    dataframes = {}
    untitled_number = 1
    for i, df_object in enumerate(args):
        df_name = None

        for var_name, var_val in callers_local_vars:
            if var_val is df_object:
                df_name = var_name

        if df_name is None:
            df_name = f"untitled_{untitled_number}"
            untitled_number += 1
        dataframes[df_name] = df_object

    # Add the dictionary of positional args to the kwargs
    if any([key in kwargs.keys() for key in dataframes.keys()]):
        logger.warning("Duplicate DataFrame names were provided, duplicates were ignored.")

    kwargs = {**kwargs, **dataframes}

    pandas_gui = PandasGui(settings=settings, **kwargs)
    return pandas_gui


if __name__ == "__main__":
    from pandasgui.datasets import all_datasets

    gui = show(**all_datasets, settings={'block': True})
