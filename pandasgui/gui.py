import inspect
import sys
import os
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from pandasgui.dataframe_viewer import DataFrameViewer
from pandasgui.dialogs import PivotDialog, ScatterDialog

# Fix lack of stack trace on PyQt exceptions
try:
    import pyqt_fix
except ImportError:
    pass


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

        # self.df_dicts is a dictionary of all dataframes in the GUI.
        # {dataframe name: objects}

        # The objects are their own dictionary of:
        # {'dataframe': DataFrame object
        # 'view': DataFrameViewer object
        # 'model': DataFrameModel object
        # 'tab_widget': QTabWidget object}
        # 'display_df': DataFrame object
        # This is a truncated version of the dataframe for displaying
        self.df_dicts = {}

        # setupUI() class variable initialization.
        self.main_layout = None
        self.tabs_stacked_widget = None
        self.df_shown = None
        self.splitter = None
        self.main_widget = None

        # Nav bar class variable initialization.
        self.nav_tree = None

        # Tab widget class variable initialization.
        self.headers_highlighted = None

        # Adds keyword arguments to df_dict.
        for i, (df_name, df_object) in enumerate(kwargs.items()):

            if type(df_object) == pd.core.series.Series:
                df_object = df_object.to_frame()
                print(f'"{df_name}" was automatically converted from Series to DataFrame')
            self.df_dicts[df_name] = {}
            self.df_dicts[df_name]['dataframe'] = df_object

        # Generates the user interface.
        self.setupUI()

        # Window settings
        if nonblocking:
            self.setWindowTitle('PandasGUI (nonblocking)')
        else:
            self.setWindowTitle('PandasGUI')

        self.app.setWindowIcon(QtGui.QIcon('images/icon.png'))

        # Create main Widget
        self.show()

        screen = QtWidgets.QDesktopWidget().screenGeometry()

        percentage_of_screen = 0.6
        size = tuple((pd.np.array([screen.width(), screen.height()]) * percentage_of_screen).astype(int))
        self.resize(QtCore.QSize(*size))

        print('test')
        print(size)
        print(self.size())
        # Center window on screen
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(int((screen.width() - size.width()) / 2), int((screen.height() - size.height()) / 2))

    def setupUI(self):
        """
        Creates and adds all widgets to main_layout.
        """

        self.main_layout = QtWidgets.QHBoxLayout()

        # Make the menu bar
        self.make_menu_bar()

        # Make the QTabWidgets for each DataFrame
        self.tabs_stacked_widget = QtWidgets.QStackedWidget()
        for df_name in self.df_dicts.keys():
            tab_widget = self.make_tab_widget(df_name)
            self.df_dicts[df_name]['tab_widget'] = tab_widget
            self.tabs_stacked_widget.addWidget(tab_widget)

        # Make the navigation bar
        self.make_nav()

        # Adds navigation section to splitter.
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.nav_tree)
        self.splitter.addWidget(self.tabs_stacked_widget)

        # Combines navigation section and main section.
        self.main_layout.addWidget(self.splitter)
        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setLayout(self.main_layout)

        self.setCentralWidget(self.main_widget)

    def import_dataframe(self, path):
        print(path)
        if os.path.isfile(path) and path.endswith('.csv'):
            df_name = os.path.split(path)[1]
            df_object = pd.read_csv(path)
            self.add_dataframe(df_name, df_object)
        else:
            print("Invalid file: ", path)

    def add_dataframe(self, df_name, df_object, parent_name=None):
        '''

        :param df_name:
        :param df_object:
        :param parent_name: Name of the parent this should be under in the navbar
        :return:
        '''

        self.df_dicts[df_name] = {}
        self.df_dicts[df_name] = {}
        self.df_dicts[df_name]['dataframe'] = df_object

        # Make tab widget
        tab_widget = self.make_tab_widget(df_name)
        self.df_dicts[df_name]['tab_widget'] = tab_widget
        self.tabs_stacked_widget.addWidget(tab_widget)

        # Add it to the nav
        parent = None
        for item in self.nav_tree.findItems(parent_name, Qt.MatchExactly, column=0):
            parent = item

        self.add_df_to_nav(df_name, parent)

    ####################
    # Menu bar functions

    def make_menu_bar(self):

        # Create a menu for setting the GUI style.
        # Uses radio-style buttons in a QActionGroup.
        menubar = self.menuBar()
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

        # Creates a chart menu.
        chartMenu = menubar.addMenu('&Plot Charts')
        # chartGroup = QtWidgets.QActionGroup(chartMenu)

        scatterDialogAction = QtWidgets.QAction('&Scatter Dialog', self)
        scatterDialogAction.triggered.connect(self.scatter_dialog)
        chartMenu.addAction(scatterDialogAction)

        # Creates a reshaping menu.
        chartMenu = menubar.addMenu('&Reshape Data')

        pivotDialogAction = QtWidgets.QAction('&Pivot Dialog', self)
        pivotDialogAction.triggered.connect(self.pivot_dialog)
        chartMenu.addAction(pivotDialogAction)

    ####################
    # Tab widget functions

    def make_tab_widget(self, df_name):
        """Take a DataFrame and creates tabs for it in self.tab_widget."""

        # Creates the tabs
        dataframe_tab = self.make_dataframe_tab(df_name)
        statistics_tab = self.make_statistics_tab(df_name)
        chart_tab = self.make_tab_charts()

        tab_widget = QtWidgets.QTabWidget()

        # Adds them to the tab_view
        tab_widget.addTab(dataframe_tab, "Dataframe")
        tab_widget.addTab(statistics_tab, "Statistics")
        tab_widget.addTab(chart_tab, "Test")

        return tab_widget

    def make_dataframe_tab(self, df_name):

        df = self.df_dicts[df_name]['dataframe']

        # Create a smaller version to display so it doesn't lag
        df = df.head(1000)
        self.df_dicts[df_name]['display_df'] = df

        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        view = DataFrameViewer(df)

        layout.addWidget(view)
        tab.setLayout(layout)
        return tab

    def make_statistics_tab(self, df_name):

        df = self.df_dicts[df_name]['dataframe']

        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        tab_df = pd.DataFrame({
            'Type': df.dtypes.replace('object', 'string'),
            'Count': df.count(),
            'Mean': df.mean(),
            'StdDev': df.std(),
            'Min': df.min(),
            'Max': df.max(),
        })

        view = DataFrameViewer(tab_df)

        layout.addWidget(view)

        tab.setLayout(layout)

        return tab

    def make_tab_charts(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        button = QtWidgets.QPushButton("Test")
        button.clicked.connect(self.test)

        layout.addWidget(button)
        tab.setLayout(layout)
        return tab

    ####################
    # Nav bar functions

    class NavWidget(QtWidgets.QTreeWidget):
        def __init__(self, gui):
            super().__init__()
            self.gui = gui
            self.setHeaderLabels(['HeaderLabel'])
            self.expandAll()
            self.setAcceptDrops(True)
            self.setColumnWidth(0, 200)

        def rowsInserted(self, parent: QtCore.QModelIndex, start: int, end: int):
            super().rowsInserted(parent, start, end)
            self.expandAll()

        def sizeHint(self):
            # Width
            width = 10
            for i in range(self.columnCount()):
                width += self.columnWidth(i)
            return QtCore.QSize(500, 500)

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

    def make_nav(self):
        # Create the navigation pane
        df_names = list(self.df_dicts.keys())
        self.nav_tree = self.NavWidget(self)

        # Creates the headers.
        self.nav_tree.setHeaderLabels(['Name', 'Shape'])
        self.nav_tree.itemClicked.connect(self.nav_clicked)
        for df_name in df_names:
            self.add_df_to_nav(df_name)

    def test(self, x):
        print(self.df_dicts)

    def add_df_to_nav(self, df_name, parent=None):
        '''Add DataFrame to nav from df_dicts'''
        if parent is None:
            parent = self.nav_tree

        # Calculate and format the shape of the DataFrame
        shape = self.df_dicts[df_name]['dataframe'].shape
        shape = str(shape[0]) + ' X ' + str(shape[1])

        item = QtWidgets.QTreeWidgetItem(parent, [df_name, shape])
        self.nav_tree.itemClicked.emit(item, 0)
        self.nav_tree.setCurrentItem(item)

    def nav_clicked(self, item, column):
        """
        Examines navbar row pressed by user
        and then changes the dataframe shown.

        Args:
            location_clicked: Automatically passed during clicked signal.
                              Instance of QtCore.ModelIndex.
                              Provides information on the location clicked,
                              accessible with methods such as row() or data().
        """

        df_name = item.data(0, Qt.DisplayRole)
        df_properties = self.df_dicts.get(df_name)

        # If the dataframe exists, change the tab widget shown.
        if df_properties is not None:
            self.df_shown = df_properties['dataframe']
            tab_widget = df_properties['tab_widget']
            self.tabs_stacked_widget.setCurrentWidget(tab_widget)

    ####################
    # Dialog functions.

    def pivot_dialog(self):
        default = self.nav_tree.currentItem().data(0, Qt.DisplayRole)
        win = PivotDialog(self.df_dicts, default=default, gui=self)

    def scatter_dialog(self):
        default = self.nav_tree.currentItem().data(0, Qt.DisplayRole)
        win = ScatterDialog(self.df_dicts, default=default, gui=self)


def show(*args, nonblocking=False, **kwargs):
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
    try:
        file_paths = sys.argv[1:]
        file_dataframes = {}
        for path in file_paths:
            if os.path.isfile(path) and path.endswith('.csv'):
                df = pd.read_csv(path)
                filename = os.path.split(path)[1]
                file_dataframes[filename] = df

        pokemon = pd.read_csv('sample_data/pokemon.csv')
        sample = pd.read_csv('sample_data/sample.csv')

        tuples = [('A', 'one', 'x'), ('A', 'one', 'y'), ('A', 'two', 'x'), ('A', 'two', 'y'),
                  ('B', 'one', 'x'), ('B', 'one', 'y'), ('B', 'two', 'x'), ('B', 'two', 'y')]
        index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second', 'third'])
        multidf = pd.DataFrame(pd.np.random.randn(8, 8), index=index[:8], columns=index[:8])
        # big = pd.read_csv('sample_data/1500000 Sales Records.csv')
        # show(big)

        if file_dataframes:
            show(**file_dataframes)
        else:
            show(pokemon, multidf, sample)
    except Exception as e:
        print(e)
        import traceback

        traceback.print_exc()

        input()
