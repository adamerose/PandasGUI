from PyQt5 import QtCore, QtWidgets, QtGui
import pandas as pd
import sys

# This fixes lack of stack trace on PyQt exceptions
import pyqt_fix
from dataframe_viewer import DataFrameModel


class PandasGUI(QtWidgets.QMainWindow):

    def __init__(self, df):
        super().__init__()

        if isinstance(df, list):
            pass  # future

        self.df = df

        # Create the navigation pane
        self.nav_view = QtWidgets.QTreeView()

        # Create the console
        self.console = QtWidgets.QTextEdit(self)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.console.setFont(font)
        self.console_button = QtWidgets.QPushButton('Run', self)
        self.console_button.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                          QtWidgets.QSizePolicy.Expanding)
        self.console_button.clicked.connect(self.enter_command)

        # Create the QTabWidget and add the tab_view
        self.generate_tabs()

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

        # Adds Console and button to main section.
        self.console_layout = QtWidgets.QHBoxLayout()
        self.console_layout.addWidget(self.console)
        self.console_layout.addWidget(self.console_button)
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

    def generate_tabs(self):
        if hasattr(self, 'tab_view'):
            delattr(self, 'tab_view')
        self.tab_view = QtWidgets.QTabWidget()

        self.dataframe_tab = self.make_dataframe_tab()
        self.statistics_tab = self.make_statistics_tab()
        self.chart_tab = self.make_chart_tab()

        self.tab_view.addTab(self.dataframe_tab, "Dataframe")
        self.tab_view.addTab(self.statistics_tab, "Statistics")
        self.tab_view.addTab(self.chart_tab, "Charts")

    def make_dataframe_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.df_model = DataFrameModel(self.df)
        view = QtWidgets.QTableView()
        view.setSortingEnabled(True)
        view.setModel(self.df_model)

        # view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        view.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow)
        layout.addWidget(view)
        tab.setLayout(layout)
        return tab

    def make_statistics_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.stats_model = DataFrameModel(self.df.describe())
        view = QtWidgets.QTableView()
        view.setModel(self.stats_model)

        view.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow)
        layout.addWidget(view)

        tab.setLayout(layout)

        return tab

    def make_chart_tab(self):
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

    def enter_command(self):
        namespace = {'df': self.df, 'pd': pd}
        command = self.console.toPlainText()
        if command:
            print(command)
            exec(command, namespace)
            self.df = namespace['df']
            self.clear_layout(self.tab_layout)
            self.generate_tabs()
            self.tab_layout.addWidget(self.tab_view)

    def printdf(self):
        print(self.df_model)

    def clear_layout(self, layout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)


def show(df):
    app = QtWidgets.QApplication(sys.argv)

    # Choose GUI appearance
    print(QtWidgets.QStyleFactory.keys())
    style = "Fusion"
    app.setStyle(style)
    print("PyQt5 Style: " + style)

    win = PandasGUI(df)
    app.exec_()
