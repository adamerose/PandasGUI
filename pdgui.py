from PyQt5 import QtCore, QtWidgets, QtGui
import pandas as pd
import sys
from threading import Thread
import traceback
from collections import OrderedDict
import inspect

# This fixes lack of stack trace on PyQt exceptions
import pyqt_fix
from dataframe_viewer import DataFrameModel, DataFrameView

class PandasGUI(QtWidgets.QMainWindow):

    def __init__(self, *args, app, **kwargs):
        """

        Args:
            *args (): Tuple of DataFrame objects
            **kwargs (): Dict of (key, value) pairs of (DataFrame name, DataFrame object)
        """
        super().__init__()
        self.app = app

        # Dictionary where the key is the DataFrame name and the value is a dictionary holding the various objects
        # associated with that DataFrame.
        '''
        dataframe: DataFrame object
        view: DataFrameViewer object
        model: DataFrameModel object
        tab_widget: QTabWidget object
        '''
        self.df_dicts = {}

        # I needed to add a second '.f_back', not sure why
        callers_local_vars = inspect.currentframe().f_back.f_back.f_locals.items()

        # Adds positional arguments to df_dicts.
        for i, df_object in enumerate(args):
            df_name = 'untitled' + str(i + 1)

            for var_name, var_val in callers_local_vars:
                if var_val is df_object:
                    df_name = var_name

            self.df_dicts[df_name] = {}
            self.df_dicts[df_name]['dataframe'] = df_object

        # Adds keyword arguments to df_dict.
        for i, (df_name, df_object) in enumerate(kwargs.items()):
            self.df_dicts[df_name] = {}
            self.df_dicts[df_name]['dataframe'] = df_object

        # Create main Widget
        self.main_layout = QtWidgets.QHBoxLayout()

        #########################################################
        # Creating and adding all widgets to main_layout

        # Make the menu bar
        self.make_menu_bar()

        # Make the navigation bar
        self.make_nav()

        # Make the QTabWidgets for each DataFrame

        self.tabs_stacked_widget = QtWidgets.QStackedWidget()

        # Iterate over all dataframe names and make the tab_widgets
        for df_name in self.df_dicts.keys():

            tab_widget = self.make_tab_widget(df_name)
            self.df_dicts[df_name]['tab_widget'] = tab_widget
            self.tabs_stacked_widget.addWidget(tab_widget)

        initial_df_name = list(self.df_dicts.keys())[0]
        initial_tab_widget = self.df_dicts[initial_df_name]['tab_widget']

        self.tabs_stacked_widget.setCurrentWidget(initial_tab_widget)

        # Adds navigation section to splitter.
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.nav_view)
        self.splitter.addWidget(self.tabs_stacked_widget)

        # Combines navigation section and main section.
        self.main_layout.addWidget(self.splitter)
        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setLayout(self.main_layout)

        self.setCentralWidget(self.main_widget)
        #########################################################

        # Center window on screen
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)
        self.setWindowTitle('PandasGUI')
        self.app.setWindowIcon(QtGui.QIcon('icon.png'))

        self.show()

    ####################
    # Menu bar functions

    def make_menu_bar(self):

        ## Create a menu for setting the GUI style with radio-style buttons in a QActionGroup
        menubar = self.menuBar()
        styleMenu = menubar.addMenu('&Set Style')
        styleGroup = QtWidgets.QActionGroup(styleMenu, exclusive=True)

        # Iterate over all GUI Styles that exist for the user's system
        for style in QtWidgets.QStyleFactory.keys():
            styleAction = QtWidgets.QAction(f'&{style}', self, checkable=True)
            styleAction.triggered.connect(lambda state, style=style: self.set_style(style))
            styleGroup.addAction(styleAction)
            styleMenu.addAction(styleAction)

        # Set the default style
        styleAction.trigger()  # REEEEEEE

    def set_style(self, style):
        print("Setting style to", style)
        self.app.setStyle(style)

    ####################
    # Tab widget functions

    def make_tab_widget(self, df_name):
        """Take a DataFrame and creates tabs for it in self.tab_widget."""

        # Creates the tabs
        dataframe_tab = self.make_tab_dataframe(df_name)
        statistics_tab = self.make_tab_statistics(df_name)
        chart_tab = self.make_tab_charts()

        tab_widget = QtWidgets.QTabWidget()
        # Adds them to the tab_view
        tab_widget.addTab(dataframe_tab, "Dataframe")
        tab_widget.addTab(statistics_tab, "Statistics")
        tab_widget.addTab(chart_tab, "Charts")

        return tab_widget

    def make_tab_dataframe(self, df_name):

        df = self.df_dicts[df_name]['dataframe']

        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        model = DataFrameModel(df)
        view = DataFrameView()
        view.setModel(model)

        # view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        view.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow)
        layout.addWidget(view)
        tab.setLayout(layout)
        return tab

    def make_tab_statistics(self, df_name):

        df = self.df_dicts[df_name]['dataframe']

        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        tab_df = df.describe(include='all').T
        tab_df.insert(loc=0, column='Type', value=df.dtypes)
        model = DataFrameModel(tab_df)
        view = DataFrameView()
        view.setModel(model)

        view.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow)
        layout.addWidget(view)

        tab.setLayout(layout)

        return tab

    def make_tab_charts(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        button = QtWidgets.QPushButton("Print DF")
        button.clicked.connect(self.printdf)

        layout.addWidget(button)
        tab.setLayout(layout)
        return tab


    ####################
    # Nav bar functions

    def make_nav(self):
        # Create the navigation pane
        df_names = list(self.df_dicts.keys())
        self.nav_view = QtWidgets.QTreeView()

        model = QtGui.QStandardItemModel(0, 2, self)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Shape')
        root_node = model.invisibleRootItem()

        self.main_nav_branch = QtGui.QStandardItem('Master')
        for df_name in df_names:
            # Adds a dataframe to the navigation sidebar

            # Calculate and format the shape of the DataFrame
            shape = self.df_dicts[df_name]['dataframe'].shape
            shape = str(shape[0]) + ' X ' + str(shape[1])

            df_name = QtGui.QStandardItem(df_name)
            df_name.setEditable(False)
            shape = QtGui.QStandardItem(shape)
            shape.setEditable(False)
            self.main_nav_branch.appendRow([df_name, shape])

        root_node.appendRow([self.main_nav_branch, None])
        self.nav_view.setModel(model)
        self.nav_view.expandAll()
        self.nav_view.clicked.connect(self.select_dataframe)

    def select_dataframe(self, index):
        """Examines navbar row pressed by user
           and then changes the dataframe shown."""
        row_selected = index.row()
        df_name = self.nav_view.model().index(0, 0).child(row_selected, 0).data()

        tab_widget = self.df_dicts[df_name]['tab_widget']

        self.tabs_stacked_widget.setCurrentWidget(tab_widget)

    def create_nav_model(self):
        model = QtGui.QStandardItemModel(0, 2, self)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Shape')
        return model

    ####################

    def printdf(self):
        print('debug')


def start_gui(*args, **kwargs):
    app = QtWidgets.QApplication(sys.argv)

    win = PandasGUI(*args, **kwargs, app=app)
    app.exec_()


def show(*args, **kwargs):
    thread = Thread(target=start_gui, args=args, kwargs=kwargs)
    thread.start()


if __name__ == '__main__':
    pokemon = pd.read_csv('pokemon.csv')

    sample = pd.read_csv('sample.csv')

    tuples = [('A', 'one', 'x'), ('A', 'one', 'y'), ('A', 'two', 'x'), ('A', 'two', 'y'),
              ('B', 'one', 'x'), ('B', 'one', 'y'), ('B', 'two', 'x'), ('B', 'two', 'y')]
    index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second', 'third'])
    multidf = pd.DataFrame(pd.np.random.randn(8, 8), index=index[:8], columns=index[:8])

    show(sample, multidf=multidf, pokemon=pokemon)
