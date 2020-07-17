import inspect
import os
import sys

import pandas as pd
import pkg_resources
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from pandasgui.store import store
from pandasgui.utility import fix_ipython, fix_pyqt, get_logger
from pandasgui.widgets import DataFrameExplorer, FindToolbar, PivotDialog, ScatterDialog

logger = get_logger(__name__)

# Global config
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "2"
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
fix_ipython()
fix_pyqt()


class PandasGUI(QtWidgets.QMainWindow):
    def __init__(self, **kwargs):
        """
        Args:
            kwargs: Dict of DataFrames where key is name & val is the DataFrame object
        """

        # Set in setupUI()
        self.stacked_widget = None
        self.splitter = None
        self.nav_tree = None

        # Get an application instance
        self.app = QtWidgets.QApplication.instance()
        if self.app:
            logger.info("Using existing QApplication instance")
        if not self.app:
            self.app = QtWidgets.QApplication(sys.argv)

        super().__init__()

        # https://stackoverflow.com/a/27178019/3620725
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Adds DataFrames listed in kwargs to store.
        for i, (df_name, df_object) in enumerate(kwargs.items()):
            store.data[df_name] = {}
            store.data[df_name]["dataframe"] = df_object

        # Generates all UI contents
        self.setupUI()

        # %% Window settings
        # Set size
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        percentage_of_screen = 0.7
        size = tuple(
            (
                pd.np.array([screen.width(), screen.height()]) * percentage_of_screen
            ).astype(int)
        )
        self.resize(QtCore.QSize(*size))
        # Center window on screen
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(
            int((screen.width() - size.width()) / 2),
            int((screen.height() - size.height()) / 2),
        )
        # Title and logo
        self.setWindowTitle("PandasGUI")
        pdgui_icon = "images/icon.png"
        pdgui_icon_path = pkg_resources.resource_filename(__name__, pdgui_icon)
        self.app.setWindowIcon(QtGui.QIcon(pdgui_icon_path))

        self.show()

    def setupUI(self):
        """
        Creates and adds all widgets to GUI.
        """

        # This holds the DataFrameExplorer for each DataFrame
        self.stacked_widget = QtWidgets.QStackedWidget()

        # Make the navigation bar
        self.nav_tree = self.NavWidget(self)
        # Creates the headers.
        self.nav_tree.setHeaderLabels(["Name", "Shape"])
        self.nav_tree.itemSelectionChanged.connect(self.nav_clicked)

        for df_name in store.data.keys():
            df_object = store.data[df_name]["dataframe"]
            self.add_dataframe(df_name, df_object)

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
        self.findBar = FindToolbar(self)
        self.addToolBar(self.findBar)

        # QMainWindow setup
        self.make_menu_bar()
        self.setCentralWidget(self.splitter)

    def import_dataframe(self, path):

        if os.path.isfile(path) and path.endswith(".csv"):
            df_name = os.path.split(path)[1]
            df_object = pd.read_csv(path)
            self.add_dataframe(df_name, df_object)

        else:
            logger.warning("Invalid file: ", path)

    def add_dataframe(self, df_name, df_object):
        """
        Add a new DataFrame to the GUI
        """

        if type(df_object) != pd.DataFrame:
            try:
                df_object = pd.DataFrame(df_object)
                logger.warning(
                    f'Automatically converted "{df_name}" from type {type(df_object)}'
                    " to DataFrame"
                )
            except:
                logger.warning(
                    f'Could not convert "{df_name}" from type {type(df_object)} to'
                    " DataFrame"
                )
                return

        # Non-string column indices causes problems when pulling them from a GUI dropdown (which will give str)
        if type(df_object.columns) != pd.MultiIndex:
            df_object.columns = df_object.columns.astype(str)

        store.data[df_name] = {}
        store.data[df_name] = {}
        store.data[df_name]["dataframe"] = df_object

        dfe = DataFrameExplorer(df_object)
        self.stacked_widget.addWidget(dfe)

        store.data[df_name]["dataframe_explorer"] = dfe
        self.add_df_to_nav(df_name)

    ####################
    # Menu bar functions

    def make_menu_bar(self):
        """
        Make the menubar and add it to the QMainWindow
        """
        # Create a menu for setting the GUI style.
        # Uses radio-style buttons in a QActionGroup.
        menubar = self.menuBar()

        # Creates an edit menu
        editMenu = menubar.addMenu("&Edit")
        findAction = QtWidgets.QAction("&Find", self)
        findAction.setShortcut("Ctrl+F")
        findAction.triggered.connect(self.findBar.show_find_bar)
        editMenu.addAction(findAction)

        styleMenu = menubar.addMenu("&Set Style")
        styleGroup = QtWidgets.QActionGroup(styleMenu)

        # Add an option to the menu for each GUI style that exist for the user's system
        for ix, style in enumerate(QtWidgets.QStyleFactory.keys()):
            styleAction = QtWidgets.QAction(f"&{style}", self, checkable=True)
            styleAction.triggered.connect(
                lambda state, style=style: self.app.setStyle(style)
                and self.app.setStyleSheet("")
            )
            styleGroup.addAction(styleAction)
            styleMenu.addAction(styleAction)

            # Set the default style to the last in the options
            if ix == len(QtWidgets.QStyleFactory.keys()) - 1:
                styleAction.trigger()

        # Creates a debug menu.
        debugMenu = menubar.addMenu("&Debug")
        testDialogAction = QtWidgets.QAction("&Test", self)
        testDialogAction.triggered.connect(self.test)
        debugMenu.addAction(testDialogAction)

        """
        # Creates a chart menu.
        chartMenu = menubar.addMenu('&Plot Charts')
        scatterDialogAction = QtWidgets.QAction('&Scatter Dialog', self)
        scatterDialogAction.triggered.connect(self.scatter_dialog)
        chartMenu.addAction(scatterDialogAction)

        # Creates a reshaping menu.
        chartMenu = menubar.addMenu('&Reshape Data')
        pivotDialogAction = QtWidgets.QAction('&Pivot Dialog', self)
        pivotDialogAction.triggered.connect(self.pivot_dialog)
        chartMenu.addAction(pivotDialogAction)
        """

    def test(self):
        logger.debug("TEST")

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
        """
        Add DataFrame to the nav by looking up the DataFrame by name in store

        Args:
            df_name (str): Name of the DataFrame
            parent (QTreeWidgetItem): Parent item in the nav tree hierarchy
        """

        if parent is None:
            parent = self.nav_tree

        # Calculate and format the shape of the DataFrame
        shape = store.data[df_name]["dataframe"].shape
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

        dfe = store.data[df_name]["dataframe_explorer"]
        self.stacked_widget.setCurrentWidget(dfe)

    ####################
    # Dialog functions. TODO: Rewrite these all

    def pivot_dialog(self):
        default = self.nav_tree.currentItem().data(0, Qt.DisplayRole)
        win = PivotDialog(store.data, default=default, gui=self)

    def scatter_dialog(self):
        default = self.nav_tree.currentItem().data(0, Qt.DisplayRole)
        win = ScatterDialog(store.data, default=default, gui=self)


def show(*args, settings: dict = {}, **kwargs):
    """
    Create and show a PandasGUI window with all the DataFrames passed. *args and **kwargs should all be DataFrames

    Args:
        *args: These should all be DataFrames. The GUI uses stack inspection to get the variable name to use in the GUI
        block (bool): Indicates whether to run app._exec on the PyQt application to block further execution of script
        **kwargs: These should all be DataFrames. The key is the desired name and the value is the DataFrame object
    """

    for key, value in settings.items():
        setattr(store.settings, key, value)

    # Get the variable names in the scope show() was called from
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()

    # Make a dictionary of the DataFrames from the position args and get their variable names using inspect
    dataframes = {}
    for i, df_object in enumerate(args):
        df_name = "untitled" + str(i + 1)

        for var_name, var_val in callers_local_vars:
            if var_val is df_object:
                df_name = var_name

        dataframes[df_name] = df_object

    # Add the dictionary of positional args to the kwargs
    if any([key in kwargs.keys() for key in dataframes.keys()]):
        logger.warning(
            "Duplicate DataFrame names were provided, duplicates were ignored."
        )
    kwargs = {**kwargs, **dataframes}

    pandas_gui = PandasGUI(**kwargs)

    if store.settings.block:
        pandas_gui.app.exec_()

    return pandas_gui


if __name__ == "__main__":
    from pandasgui.datasets import all_datasets

    show(**all_datasets, settings={"block": True})
