from PyQt5 import QtCore, QtWidgets, QtGui
import pandas as pd
import sys
import threading
import traceback
from collections import OrderedDict
import inspect

# This fixes lack of stack trace on PyQt exceptions
import pyqt_fix
from dataframe_viewer import DataFrameModel, DataFrameView


class PandasGUI(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        """

        Args:
            *args (): Tuple of DataFrame objects
            **kwargs (): Dict of (key, value) pairs of (DataFrame name, DataFrame object)
        """
        super().__init__()

        # Dictionary holding all the DataFrames in the GUI keyed by name
        self.df_dict = {}

        # Dictionary holding metadata for the DataFrames, including the following:
        '''
        tab_widget: QTabWidget object
        '''
        self.df_metadata = {}

        # Adds keyword arguments to df_dict.
        for i, (df_name, df_object) in enumerate(kwargs.items()):
            self.df_dict[df_name] = df_object
            self.df_metadata[df_name] = {}

        # Adds positional arguments to df_dict.
        for i, df_object in enumerate(args):
            df_name = 'untitled' + str(i + 1)
            self.df_dict[df_name] = df_object
            self.df_metadata[df_name] = {}

        # Create main Widget
        self.main_layout = QtWidgets.QHBoxLayout()

        #########################################################
        # Creating and adding all widgets to main_layout

        # Make the navigation bar
        self.make_nav()

        # Make the QTabWidgets for each DataFrame

        self.tabs_stacked_widget = QtWidgets.QStackedWidget()

        for df_name, df_object in self.df_dict.items():
            tab_widget = self.make_tab_widget(df_object)
            self.df_metadata[df_name]['tab_widget'] = tab_widget
            self.tabs_stacked_widget.addWidget(tab_widget)

        initial_df_name = list(self.df_dict.keys())[0]
        initial_tab_widget = self.df_metadata[initial_df_name]['tab_widget']

        self.tabs_stacked_widget.setCurrentWidget(initial_tab_widget)
        # self.tabs_stacked_widget.setContentsMargins(0, 0, 0, 0)


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

        self.show()

    ####################
    # Tab widget functions

    def make_tab_widget(self, df):
        """Take a DataFrame and creates tabs for it in self.tab_widget."""

        # Creates the tabs
        dataframe_tab = self.make_tab_dataframe(df)
        statistics_tab = self.make_tab_statistics(df)
        chart_tab = self.make_tab_charts(df)

        tab_widget = QtWidgets.QTabWidget()
        # Adds them to the tab_view
        tab_widget.addTab(dataframe_tab, "Dataframe")
        tab_widget.addTab(statistics_tab, "Statistics")
        tab_widget.addTab(chart_tab, "Charts")

        return tab_widget

    def make_tab_dataframe(self, df):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.df_model = DataFrameModel(df)
        view = DataFrameView()
        view.setModel(self.df_model)

        # view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        view.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow)
        layout.addWidget(view)
        tab.setLayout(layout)
        return tab

    def make_tab_statistics(self, df):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        stats_model = DataFrameModel(df.describe())
        view = QtWidgets.QTableView()
        view.setModel(stats_model)

        print(df.describe())
        view.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow)
        layout.addWidget(view)

        tab.setLayout(layout)

        return tab

    def make_tab_charts(self, df):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        button = QtWidgets.QPushButton("Print DF")
        button.clicked.connect(self.printdf)

        layout.addWidget(button)
        tab.setLayout(layout)
        return tab

    def make_tab_reshape(self):
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
        df_names = list(self.df_dict.keys())
        self.nav_view = QtWidgets.QTreeView()

        model = QtGui.QStandardItemModel(0, 2, self)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Shape')
        rootnode = model.invisibleRootItem()

        self.main_nav_branch = QtGui.QStandardItem('Master')
        for df_name in df_names:
            self.add_nav_dataframe(df_name)
        rootnode.appendRow([self.main_nav_branch, None])
        self.nav_view.setModel(model)
        self.nav_view.expandAll()
        self.nav_view.clicked.connect(self.select_dataframe)

    def select_dataframe(self, name):
        """Examines navbar row pressed by user
           and then changes the dataframe shown."""
        row_selected = name.row()
        df_name = self.nav_view.model().index(0, 0).child(row_selected, 0).data()
        df = self.df_dict[df_name]

        tab_widget = self.df_metadata[df_name]['tab_widget']

        self.tabs_stacked_widget.setCurrentWidget(tab_widget)


    def create_nav_model(self):
        model = QtGui.QStandardItemModel(0, 2, self)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Shape')
        return model

    def add_nav_dataframe(self, df_name):
        """Adds a dataframe to the navigation sidebar"""

        # Calculate and format the shape of the DataFrame
        shape = self.df_dict[df_name].shape
        shape = str(shape[0]) + ' X ' + str(shape[1])

        df_name = QtGui.QStandardItem(df_name)
        shape = QtGui.QStandardItem(shape)
        self.main_nav_branch.appendRow([df_name, shape])

    ####################

    def printdf(self):
        print(self.df_model)


def show(*args, **kwargs):
    app = QtWidgets.QApplication(sys.argv)

    # Choose GUI appearance
    print(QtWidgets.QStyleFactory.keys())
    style = "Fusion"
    app.setStyle(style)
    print("PyQt5 Style: " + style)

    win = PandasGUI(*args, **kwargs)
    app.exec_()


if __name__ == '__main__':
    pokemon = pd.read_csv('pokemon.csv')

    sample = pd.read_csv('sample.csv')

    tuples = [('A', 'one', 'x'), ('A', 'one', 'y'), ('A', 'two', 'x'), ('A', 'two', 'y'),
              ('B', 'one', 'x'), ('B', 'one', 'y'), ('B', 'two', 'x'), ('B', 'two', 'y')]
    index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second', 'third'])
    multidf = pd.DataFrame(pd.np.random.randn(8, 8), index=index[:8], columns=index[:8])

    show(sample, multidf=multidf, pokemon=pokemon)
