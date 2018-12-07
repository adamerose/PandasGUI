from PyQt5 import QtCore, QtWidgets, QtGui
import pandas as pd
import sys
import threading
import traceback
from collections import OrderedDict

# This fixes lack of stack trace on PyQt exceptions
import pyqt_fix
from dataframe_viewer import DataFrameModel, DataFrameView


class PandasGUI(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.namespace = OrderedDict(kwargs)
        self.namespace['pd'] = pd
        for i, arg in enumerate(args):
            dataframe_num = i+1
            while ('df'+str(dataframe_num)) in self.namespace.keys():
                dataframe_num += 1
            self.namespace['df'+str(dataframe_num)] = arg
        input_dataframes = self.count_dfs()

        # Create the navigation pane
        self.nav_view = QtWidgets.QTreeView()
        model = self.create_nav_model()
        rootnode = model.invisibleRootItem()
        self.main_nav_branch = QtGui.QStandardItem('Master')
        for df_name in input_dataframes:
            self.add_nav_dataframe(df_name)
        rootnode.appendRow([self.main_nav_branch, None])
        self.nav_view.setModel(model)
        self.nav_view.expandAll()
        self.nav_view.clicked.connect(self.select_dataframe)

        # Create the console
        self.console = QtWidgets.QTextEdit(self)
        default_text = ('Press run button to run code in textbox.\n'
                        'Or enter command into interpreter and press enter.')
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
        first_df = input_dataframes[0]
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

    def select_dataframe(self, name):
        '''Examines navbar row pressed by user
           and then changes the dataframe shown.'''
        row_selected = name.row()
        df = self.nav_view.model().index(0, 0).child(row_selected, 0).data()
        self.refresh_layout(dataframe_shown=df)

    def create_nav_model(self):
        model = QtGui.QStandardItemModel(0, 2, self)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Shape')
        return model

    def add_nav_dataframe(self, df_name):
        '''Adds a nav element to the navigation sidebar'''
        shape = self.namespace[df_name].shape
        shape = str(shape[0]) + ' X ' + str(shape[1])
        name = QtGui.QStandardItem(df_name)
        shape = QtGui.QStandardItem(shape)
        self.main_nav_branch.appendRow([name, shape])

    def generate_tabs(self, df):
        '''Take a dataframe and creates tab information from it.'''
        df = self.namespace[df]
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
        view = DataFrameView()
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
        '''Starts a thread waiting for interpreter input.
           Prevents locking of the gui while waiting.'''
        self.thread = threading.Thread(target=self.get_interpreter_command,
                                       args=(self.interpreter_signal,))
        self.thread.start()

    def get_interpreter_command(self, signal):
        '''Runs commands inputted in the interpreter.'''
        self.command = input('Type command below\n')
        signal.finished.emit()

    def get_textbox_command(self):
        '''Runs commands inputted to the textbox.'''
        self.command = self.console.toPlainText()
        self.run_command()

    def run_command(self):
        '''Runs user command and examines any variables added.
           If the variable is a dataframe, adds it to the navbar.'''
        if self.command:
            old_num_dfs = len(self.count_dfs())
            try:
                exec(self.command, self.namespace)
            except:
                print(traceback.format_exc())
            new_num_dfs = len(self.count_dfs())
            if new_num_dfs > old_num_dfs:
                new_df = self.count_dfs()[-1]
                self.add_nav_dataframe(new_df)
                self.refresh_layout(dataframe_shown=new_df)
            else:
                self.refresh_layout(dataframe_shown='df')
            self.console.setText('')
            self.command = None

    def printdf(self):
        print(self.df_model)

    def count_dfs(self):
        '''Returns all dfs in namespace.'''
        return [df for df in self.namespace.keys()
                if isinstance(self.namespace[df], pd.DataFrame)]

    def clear_layout(self, layout):
        '''Clears all widgets from a layout.'''
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)

    def refresh_layout(self, dataframe_shown):
        '''Clears the tab layout then redraws it showing a new dataframe.'''
        self.clear_layout(self.tab_layout)
        self.generate_tabs(dataframe_shown)
        self.tab_layout.addWidget(self.tab_view)


class InterpreterSignal(QtCore.QObject):
    '''Signal class used for sending a finished signal when
       user is finished interpreter input().'''
    finished = QtCore.pyqtSignal()


def show(*args, **kwargs):
    app = QtWidgets.QApplication(sys.argv)

    # Choose GUI appearance
    print(QtWidgets.QStyleFactory.keys())
    style = "Fusion"
    app.setStyle(style)
    print("PyQt5 Style: " + style)

    win = PandasGUI(*args, **kwargs)
    app.exec_()


def example():
    df = pd.read_csv('pokemon.csv')
    df2 = pd.read_csv('sample.csv')
    tuples = [('A', 'one', 'x'), ('A', 'one', 'y'), ('A', 'two', 'x'), ('A', 'two', 'y'),
              ('B', 'one', 'x'), ('B', 'one', 'y'), ('B', 'two', 'x'), ('B', 'two', 'y')]
    index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second', 'third'])
    df3 = pd.DataFrame(pd.np.random.randn(8, 8), index=index[:8], columns=index[:8])
    show(df, df2, multidf=df3)

if __name__ == '__main__':
    example()
