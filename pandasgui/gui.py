"""Defines the main PandasGUI class and related functions"""

import inspect
import sys
import os
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from pandasgui.widgets import PivotDialog, ScatterDialog
from pandasgui.widgets import DataFrameExplorer
from pandasgui.widgets import Find_Toolbar
import pkg_resources

class PandasGUI(QtWidgets.QMainWindow):

    def __init__(self, nonblocking=False, **kwargs):
        """
        Args:
            *args (): Tuple of DataFrame objects
            **kwargs (): Dict of (key, value) pairs of
                         {'DataFrame name': DataFrame object}
        """
        if nonblocking:
            print("Opening PandasGUI (nonblocking mode)...")
        else:
            print("Opening PandasGUI...")
        super().__init__()
        self.app = QtWidgets.QApplication.instance()

        # https://stackoverflow.com/a/27178019/3620725
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # self.df_dicts is a dictionary of all dataframes in the GUI.
        # {dataframe name: objects}

        # The objects are their own dictionary of:
        # {'dataframe': DataFrame object
        # 'view': DataFrameViewer object
        # 'model': DataFrameModel object
        # 'dataframe_explorer': DataFrameExplorer object}
        # 'display_df': DataFrame object
        # This is a truncated version of the dataframe for displaying
        self.df_dicts = {}

        # setupUI() class variable initialization.
        self.main_layout = None
        self.stacked_widget = None
        self.df_shown = None
        self.splitter = None
        self.main_widget = None

        # Nav bar class variable initialization.
        self.nav_tree = None

        # Tab widget class variable initialization.
        self.headers_highlighted = None

        # Adds keyword arguments to df_dict.
        for i, (df_name, df_object) in enumerate(kwargs.items()):

            if type(df_object) == pd.Series:
                df_object = df_object.to_frame()
                print(f'"{df_name}" was automatically converted from Series to DataFrame for viewing')
            self.df_dicts[df_name] = {}
            self.df_dicts[df_name]['dataframe'] = df_object

        # Set window size to percentage of screen
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        percentage_of_screen = 0.7
        size = tuple((pd.np.array([screen.width(), screen.height()]) * percentage_of_screen).astype(int))
        self.resize(QtCore.QSize(*size))

        # Generates the user interface.
        self.setupUI()

        # Window settings
        if nonblocking:
            self.setWindowTitle('PandasGUI (nonblocking)')
        else:
            self.setWindowTitle('PandasGUI')
        pdgui_icon = 'images/icon.png'
        pdgui_icon_path = pkg_resources.resource_filename(__name__, pdgui_icon)

        self.app.setWindowIcon(QtGui.QIcon(pdgui_icon_path))

        # Create main Widget
        self.show()

        # Center window on screen
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(int((screen.width() - size.width()) / 2), int((screen.height() - size.height()) / 2))

    def setupUI(self):
        """
        Creates and adds all widgets to main_layout.
        """

        self.main_layout = QtWidgets.QHBoxLayout()

        # makes the find toolbar
        self.findBar = Find_Toolbar(self)
        self.addToolBar(self.findBar)

        # Make the menu bar
        self.make_menu_bar()

        # This holds the DataFrameExplorer for each DataFrame
        self.stacked_widget = QtWidgets.QStackedWidget()

        # Make the navigation bar
        self.nav_tree = self.NavWidget(self)
        # Creates the headers.
        self.nav_tree.setHeaderLabels(['Name', 'Shape'])
        self.nav_tree.itemSelectionChanged.connect(self.nav_clicked)

        for df_name in self.df_dicts.keys():
            df_object = self.df_dicts[df_name]['dataframe']
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

        self.setCentralWidget(self.splitter)
        self.splitter.setContentsMargins(10, 10, 10, 10)

    def import_dataframe(self, path):

        if os.path.isfile(path) and path.endswith('.csv'):
            df_name = os.path.split(path)[1]
            df_object = pd.read_csv(path)
            self.add_dataframe(df_name, df_object)

        else:
            print("Invalid file: ", path)

    def add_dataframe(self, df_name, df_object):
        '''
        Add a new DataFrame to the GUI
        '''

        self.df_dicts[df_name] = {}
        self.df_dicts[df_name] = {}
        self.df_dicts[df_name]['dataframe'] = df_object

        dfe = DataFrameExplorer(df_object)
        self.df_dicts[df_name]['dataframe_explorer'] = dfe
        self.stacked_widget.addWidget(dfe)
        self.add_df_to_nav(df_name)

    ####################
    # Menu bar functions

    def make_menu_bar(self):
        '''
        Make the menubar and add it to the QMainWindow
        '''
        # Create a menu for setting the GUI style.
        # Uses radio-style buttons in a QActionGroup.
        menubar = self.menuBar()

        # Creates an edit menu
        editMenu = menubar.addMenu('&Edit')
        findAction = QtWidgets.QAction('&Find', self)
        findAction.setShortcut('Ctrl+F')
        findAction.triggered.connect(self.findBar.show_find_bar)
        editMenu.addAction(findAction)

        styleMenu = menubar.addMenu('&Set Style')
        styleGroup = QtWidgets.QActionGroup(styleMenu, exclusive=True)

        # Add an option to the menu for each GUI style that exist for the user's system
        for style in QtWidgets.QStyleFactory.keys():
            styleAction = QtWidgets.QAction(f'&{style}', self, checkable=True)
            styleAction.triggered.connect(
                lambda state, style=style: self.app.setStyle(style) and self.app.setStyleSheet(""))
            styleGroup.addAction(styleAction)
            styleMenu.addAction(styleAction)
        # Set the default style
        styleAction.trigger()

        # Creates a debug menu.
        debugMenu = menubar.addMenu('&Debug')
        testDialogAction = QtWidgets.QAction('&Test', self)
        testDialogAction.triggered.connect(self.test)
        debugMenu.addAction(testDialogAction)

        '''
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
        '''

    # I just use this function for printing various things to console while the GUI is running
    def test(self):
        print('----------------')
        print('splitter', self.splitter.size())
        print('nav_tree', self.nav_tree.size())
        print('stacked_widget', self.stacked_widget.size())
        print('splitter', self.splitter.sizeHint())
        print('nav_tree', self.nav_tree.sizeHint())
        print('stacked_widget', self.stacked_widget.sizeHint())
        print('----------------')

    class NavWidget(QtWidgets.QTreeWidget):
        def __init__(self, gui):
            super().__init__()
            self.gui = gui
            self.setHeaderLabels(['HeaderLabel'])
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
        Add DataFrame to the nav by looking up the DataFrame by name in df_dicts

        Args:
            df_name (str): Name of the DataFrame
            parent (QTreeWidgetItem): Parent item in the nav tree hierarchy
        """

        if parent is None:
            parent = self.nav_tree

        # Calculate and format the shape of the DataFrame
        shape = self.df_dicts[df_name]['dataframe'].shape
        shape = str(shape[0]) + ' X ' + str(shape[1])

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

        dfe = self.df_dicts[df_name]['dataframe_explorer']
        self.stacked_widget.setCurrentWidget(dfe)

    ####################
    # Dialog functions. TODO: Rewrite these all

    def pivot_dialog(self):
        default = self.nav_tree.currentItem().data(0, Qt.DisplayRole)
        win = PivotDialog(self.df_dicts, default=default, gui=self)

    def scatter_dialog(self):
        default = self.nav_tree.currentItem().data(0, Qt.DisplayRole)
        win = ScatterDialog(self.df_dicts, default=default, gui=self)


def show(*args, nonblocking=False, **kwargs):
    """
    Create and show a PandasGUI window with all the DataFrames passed. *args and **kwargs should all be DataFrames

    Args:
        *args: These should all be DataFrames. The GUI uses stack inspection to get the variable name to use in the GUI
        nonblocking (bool): Indicates whether the GUI should be started in non-blocking mode (in a separate process)
        **kwargs: These should all be DataFrames. The key is the desired name and the value is the DataFrame object
    """

    # Get the variable names in the scope show() was called from
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()

    # Make a dictionary of the DataFrames from the position args and get their variable names using inspect
    dataframes = {}
    for i, df_object in enumerate(args):
        df_name = 'untitled' + str(i + 1)

        for var_name, var_val in callers_local_vars:
            if var_val is df_object:
                df_name = var_name

        dataframes[df_name] = df_object

    # Add the dictionary of positional args to the kwargs
    if (any([key in kwargs.keys() for key in dataframes.keys()])):
        print("Warning! Duplicate DataFrame names were given, duplicates were ignored.")
    kwargs = {**kwargs, **dataframes}

    # Run the GUI in a separate process
    if nonblocking:
        from pandasgui.nonblocking import show_nonblocking
        show_nonblocking(**kwargs)
        return

    # Create the application and PandasGUI window
    app = QtWidgets.QApplication.instance()
    if app:
        print('Using existing QApplication instance')
    if not app:
        app = QtWidgets.QApplication(sys.argv)
    win = PandasGUI(**kwargs)
    app.exec_()


if __name__ == '__main__':

    # Fix lack of stack trace on PyQt exceptions
    def my_exception_hook(exctype, value, traceback):
        # Print the error and traceback
        print(exctype, value, traceback)
        # Call the normal Exception hook after
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)


    sys.excepthook = my_exception_hook

    try:
        # Get paths of drag & dropped files and prepare to open them in the GUI
        file_paths = sys.argv[1:]
        if file_paths:
            file_dataframes = {}
            for path in file_paths:
                if os.path.isfile(path) and path.endswith('.csv'):
                    df = pd.read_csv(path)
                    filename = os.path.split(path)[1]
                    file_dataframes[filename] = df
            show(**file_dataframes)

        # Script was run normally, open sample data sets
        else:
            from pandasgui.datasets import iris, flights, multi, all_datasets

            show(**all_datasets)

    # Catch errors and call input() so they can be viewed before the console window closes when running with drag n drop
    except Exception as e:
        print(e)
        import traceback

        traceback.print_exc()
        input()
