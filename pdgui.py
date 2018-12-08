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

        self.df_dict = {}

        # Adds keyword arguments to namespace.
        for i, (key, value) in enumerate(kwargs.items()):
            self.df_dict[key] = value

        # Adds positional arguments to namespace.
        for i, value in enumerate(args):
            self.df_dict['untitled' + str(i + 1)] = value



        # Create main Widget
        self.main_layout = QtWidgets.QHBoxLayout()

        #########################################################
        # Creating and adding all widgets to main_layout

        # Make the navigation bar
        self.make_nav()

        # Make the QTabWidget
        initial_df = list(self.df_dict.values())[0]

        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setContentsMargins(0, 0, 0, 0)
        self.make_tabs(initial_df)

        # Adds navigation section to splitter.
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.nav_view)
        self.splitter.addWidget(self.tab_widget)

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

    def make_tabs(self, df):
        """Take a DataFrame and creates tabs for it in self.tab_widget."""

        # Creates the tabs
        dataframe_tab = self.make_tab_dataframe(df)
        statistics_tab = self.make_tab_statistics(df)
        chart_tab = self.make_tab_charts(df)

        # Adds them to the tab_view
        self.tab_widget.addTab(dataframe_tab, "Dataframe")
        self.tab_widget.addTab(statistics_tab, "Statistics")
        self.tab_widget.addTab(chart_tab, "Charts")

        return self.tab_widget

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

        self.stats_model = DataFrameModel(df.describe())
        view = QtWidgets.QTableView()
        view.setModel(self.stats_model)

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
        # Creates the navigation pane.
        df_names = list(self.df_dict.keys())
        self.nav_view = QtWidgets.QTreeView()

        # Creates the headers.
        model = QtGui.QStandardItemModel(0, 2, self)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Shape')

        # Adds the user-inputted dataframes as navbar elements.
        self.main_nav_branch = QtGui.QStandardItem('Master')
        rootnode = model.invisibleRootItem()
        rootnode.appendRow([self.main_nav_branch, None])
        for df_name in df_names:
            self.add_nav_dataframe(df_name, self.main_nav_branch)

        # Sets navigation pane properties.
        self.nav_view.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.nav_view.setSortingEnabled(True)
        self.nav_view.setModel(model)
        self.nav_view.expandAll()
        self.nav_view.clicked.connect(self.select_dataframe)

    def select_dataframe(self, location_clicked):
        """
        Examines navbar row pressed by user
        and then changes the dataframe shown.

        Args:
            location_clicked: Automatically passed during clicked signal.
                              Instance of QtCore.ModelIndex.
                              Provides information on the location clicked.
        """

        folder_clicked_index = location_clicked.parent().row()
        df_clicked_index = location_clicked.row()

        # Gets name of dataframe clicked by the row index.
        nav_pane = self.nav_view.model()
        df_folder = nav_pane.index(folder_clicked_index, 0)
        df_name = df_folder.child(df_clicked_index, 0).data()
        df = self.df_dict.get(df_name)

        if df is not None:
            # Remove all tabs from self.tab_widget.
            for _ in range(self.tab_widget.count()):
                self.tab_widget.removeTab(0)

            # Remake them with the new dataframe.
            self.make_tabs(df)

    def create_nav_model(self):
        model = QtGui.QStandardItemModel(0, 2, self)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Shape')
        return model

    def add_nav_dataframe(self, df_name, folder):
        """Adds a dataframe to the navigation sidebar"""

        # Calculate and format the shape of the DataFrame
        shape = self.df_dict[df_name].shape
        shape = str(shape[0]) + ' X ' + str(shape[1])

        df_name_label = QtGui.QStandardItem(df_name)
        shape_label = QtGui.QStandardItem(shape)
        folder.appendRow([df_name_label, shape_label])

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
    x = pd.read_csv('sample.csv')
    tuples = [('A', 'one', 'x'), ('A', 'one', 'y'), ('A', 'two', 'x'), ('A', 'two', 'y'),
              ('B', 'one', 'x'), ('B', 'one', 'y'), ('B', 'two', 'x'), ('B', 'two', 'y')]

    index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second', 'third'])
    multidf = pd.DataFrame(pd.np.random.randn(8, 8), index=index[:8], columns=index[:8])
    show(x, multidf=multidf, pokemon=pokemon)
