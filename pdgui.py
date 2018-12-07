from PyQt5 import QtCore, QtWidgets, QtGui
import pandas as pd
import sys
import time
import threading
import queue
import traceback
from multiprocessing import Process
from collections import OrderedDict

# This fixes lack of stack trace on PyQt exceptions
import pyqt_fix
from dataframe_viewer import DataFrameModel


class PandasGUI(QtWidgets.QMainWindow):

    def __init__(self, **kwargs):
        super().__init__()
        self.__dict__.update(kwargs)
        self.dataframes = OrderedDict(kwargs)

        # Create the navigation pane
        self.nav_view = QtWidgets.QTreeView()
        model = self.create_nav_model()
        rootnode = model.invisibleRootItem()
        branch1 = QtGui.QStandardItem('Master')
        for df_name in self.dataframes.keys():
            shape = self.dataframes[df_name].shape
            shape = str(shape[0]) + ' X ' + str(shape[1])
            name = QtGui.QStandardItem(df_name)
            shape = QtGui.QStandardItem(shape)
            branch1.appendRow([name, shape])
        rootnode.appendRow([branch1, None])
        self.nav_view.setModel(model)
        self.nav_view.expandAll()
        self.nav_view.clicked.connect(self.treefunction)

        # Create the console
        self.console = QtWidgets.QTextEdit(self)
        default_text = ('Press run button to run code in textbox.')
        self.console.setPlaceholderText(default_text)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.console.setFont(font)
        self.run_text_button = QtWidgets.QPushButton('Run', self)
        self.run_text_button.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                           QtWidgets.QSizePolicy.Expanding)
        self.run_text_button.clicked.connect(self.get_textbox_command)
        self.interpreter_signal = InterpreterSignal()
        self.enable_interpreter()
        self.interpreter_signal.finished.connect(self.run_command)
        self.interpreter_signal.finished.connect(self.enable_interpreter)

        # Create the QTabWidget and add the tab_view
        first_df = self.dataframes[(list(self.dataframes.keys())[0])]
        self.generate_tabs(first_df)

        # Create main Widget
        self.main_layout = QtWidgets.QHBoxLayout()

        # Adds tabs to QTabWidget layout.
        # Then Adds QTabWidget layout to the main section.
        self.console_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.tab_layout = QtWidgets.QHBoxLayout()
        self.tab_layout.addWidget(self.tab_view)
        self.tab_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widget = QtWidgets.QWidget()
        self.tab_widget.setLayout(self.tab_layout)
        self.console_splitter.addWidget(self.tab_widget)

        # Adds Console and buttons to main section.
        self.console_layout = QtWidgets.QHBoxLayout()
        self.console_layout.addWidget(self.console)
        self.console_layout.addWidget(self.run_text_button)
        self.console_layout.setContentsMargins(0, 0, 0, 0)
        self.console_widget = QtWidgets.QWidget()
        self.console_widget.setLayout(self.console_layout)
        self.console_splitter.addWidget(self.console_widget)

        # Adds navigation section to window.
        self.nav_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.nav_splitter.addWidget(self.nav_view)
        self.nav_splitter.addWidget(self.console_splitter)

        # Combines navigation section and main section.
        self.main_layout.addWidget(self.nav_splitter)
        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setLayout(self.main_layout)

        self.setCentralWidget(self.main_widget)
        # Center window on screen
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2,
                  (screen.height() - size.height()) / 2)

        self.setWindowTitle('PandasGUI')

        self.show()

    def treefunction(self, index):
        self.clear_layout(self.tab_layout)
        self.generate_tabs(self.dataframes[index.data()])
        self.tab_layout.addWidget(self.tab_view)

    def create_nav_model(self):
        model = QtGui.QStandardItemModel(0, 2, self)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Shape')
        return model

    def add_nav_dataframe(self, model, name):
        model.insertRow(0)
        model.setData(model.index(0, 1), name)

    def generate_tabs(self, df):
        if hasattr(self, 'tab_view'):
            delattr(self, 'tab_view')
        self.tab_view = QtWidgets.QTabWidget()

        self.dataframe_tab = self.make_dataframe_tab(df)
        self.statistics_tab = self.make_statistics_tab(df)
        self.chart_tab = self.make_chart_tab(df)

        self.tab_view.addTab(self.dataframe_tab, "Dataframe")
        self.tab_view.addTab(self.statistics_tab, "Statistics")
        self.tab_view.addTab(self.chart_tab, "Charts")

    def make_dataframe_tab(self, df):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.df_model = DataFrameModel(df)
        view = QtWidgets.QTableView()
        view.setSortingEnabled(True)
        view.setModel(self.df_model)

        # view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        view.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow)
        layout.addWidget(view)
        tab.setLayout(layout)
        return tab

    def make_statistics_tab(self, df):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.stats_model = DataFrameModel(df.describe())
        view = QtWidgets.QTableView()
        view.setModel(self.stats_model)

        view.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow)
        layout.addWidget(view)

        tab.setLayout(layout)

        return tab

    def make_chart_tab(self, df):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        button = QtWidgets.QPushButton("Print DF")
        button.clicked.connect(self.printdf)

        layout.addWidget(button)
        tab.setLayout(layout)
        return tab

    def make_reshape_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        button = QtWidgets.QPushButton("Print DF")
        button.clicked.connect(self.printdf)

        layout.addWidget(button)
        tab.setLayout(layout)
        return tab

    def enable_interpreter(self):
        self.thread = threading.Thread(target=self.get_interpreter_command,
                                       args=(self.interpreter_signal,))
        self.thread.start()

    def get_interpreter_command(self, signal):
        self.command = input('Type command below\n')
        signal.finished.emit()

    def get_textbox_command(self):
        self.command = self.console.toPlainText()
        self.run_command()

    def run_command(self):
        if self.command:
            try:
                exec(self.command, globals())
            except:
                print(traceback.format_exc())
            self.df = df
            self.clear_layout(self.tab_layout)
            self.generate_tabs()
            self.tab_layout.addWidget(self.tab_view)
        self.console.setText('')
        self.console.setEnabled(True)
        self.command = None

    def printdf(self):
        print(self.df_model)

    def clear_layout(self, layout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)


class InterpreterSignal(QtCore.QObject):
    finished = QtCore.pyqtSignal()


def show(**kwargs):
    app = QtWidgets.QApplication(sys.argv)

    # Choose GUI appearance
    print(QtWidgets.QStyleFactory.keys())
    style = "Fusion"
    app.setStyle(style)
    print("PyQt5 Style: " + style)

    win = PandasGUI(**kwargs)
    app.exec_()

if __name__ == '__main__':
    df = pd.read_csv('pokemon.csv')
    df2 = pd.read_csv('sample.csv')
    show(df=df, df2=df2)
