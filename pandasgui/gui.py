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
from pandasgui.utility import fix_ipython, fix_pyqt, get_logger, as_dict, delete_datasets
from pandasgui.widgets.dataframe_explorer import DataFrameExplorer
from pandasgui.widgets.find_toolbar import FindToolbar
from pandasgui.widgets.json_viewer import JsonViewer
from pandasgui.widgets.navigator import Navigator

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
        self.navigator.setCurrentItem(self.navigator.topLevelItem(0))

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

        # Accept drops, for importing files. See methods below: dropEvent, dragEnterEvent, dragMoveEvent
        self.setAcceptDrops(True)

        self.show()

    # Create and add all widgets to GUI.
    def init_ui(self):
        # This holds the DataFrameExplorer for each DataFrame
        self.stacked_widget = QtWidgets.QStackedWidget()

        # Make the navigation bar
        self.navigator = Navigator(self.store)

        # Make splitter to hold nav and DataFrameExplorers
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.navigator)
        self.splitter.addWidget(self.stacked_widget)

        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        nav_width = self.navigator.sizeHint().width()
        self.splitter.setSizes([nav_width, self.width() - nav_width])
        self.splitter.setContentsMargins(10, 10, 10, 10)

        # makes the find toolbar
        self.find_bar = FindToolbar(self)
        self.addToolBar(self.find_bar)

        # QMainWindow setup
        self.make_menu_bar()
        self.setCentralWidget(self.splitter)

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
                                   shortcut='Ctrl+F'),
                          MenuItem(name='Import',
                                   func=self.import_dialog),
                          MenuItem(name='Export',
                                   func=self.export_dialog),
                          ],
                 'Debug': [MenuItem(name='Print Data Store',
                                    func=self.print_store),
                           MenuItem(name='View Data Store',
                                    func=self.view_store),
                           MenuItem(name='Print History (for current DataFrame)',
                                    func=self.print_history),
                           MenuItem(name='Delete local data',
                                    func=delete_datasets),


                           ],
                 'Set Style': []}

        # Add an option to the menu for each GUI style that exist for the user's system
        for ix, style in enumerate(QtWidgets.QStyleFactory.keys()):
            items['Set Style'].append(
                MenuItem(name=style,
                         func=lambda _, s=style: self.app.setStyle(s),
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

    def dropEvent(self, e):
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
            fpath_list = []
            for url in e.mimeData().urls():
                fpath_list.append(str(url.toLocalFile()))

            for fpath in fpath_list:
                self.store.import_dataframe(fpath)
        else:
            e.ignore()

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
        self.store_viewer = JsonViewer(d)
        self.store_viewer.show()

    # Return all DataFrames, or a subset specified by names. Returns a dict of name:df or a single df if there's only 1
    def get_dataframes(self, names: Union[None, str, list] = None):
        return self.store.get_dataframes(names)

    def import_dialog(self):
        dialog = QtWidgets.QFileDialog()
        paths, _ = dialog.getOpenFileNames(filter="*.csv *.xlsx")
        for path in paths:
            self.store.import_dataframe(path)

    def export_dialog(self):
        dialog = QtWidgets.QFileDialog()
        pgdf = self.store.selected_pgdf
        path, _ = dialog.getSaveFileName(directory=pgdf.name, filter="*.csv")
        pgdf.dataframe.to_csv(path, index=False)

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
