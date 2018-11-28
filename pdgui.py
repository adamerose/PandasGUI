from PyQt5 import QtCore, QtWidgets, QtGui
import pandas as pd
import sys

# This fixes lack of stack trace on PyQt exceptions
import pyqt_fix


class PandasGUI(QtWidgets.QMainWindow):

    def __init__(self, df):
        super().__init__()

        if type(df) == type(list()):
            pass  # future

        self.df = df

        # Create the navigation pane
        self.nav_view = QtWidgets.QTreeView()

        # Create the QTabWidget and add the tab_view
        self.tab_view = QtWidgets.QTabWidget()

        self.dataframe_tab = self.make_dataframe_tab()
        self.statistics_tab = self.make_statistics_tab()
        self.chart_tab = self.make_chart_tab()

        self.tab_view.addTab(self.dataframe_tab, "Dataframe")
        self.tab_view.addTab(self.statistics_tab, "Statistics")
        self.tab_view.addTab(self.chart_tab, "Test")

        # Create main Widget
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.addWidget(self.nav_view)
        self.main_layout.addWidget(self.tab_view)
        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setLayout(self.main_layout)

        self.setCentralWidget(self.main_widget)
        # Center window on screen
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)

        self.setWindowTitle('PandasGUI')

        self.show()

    def make_dataframe_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.df_model = DataFrameModel(self.df)
        view = QtWidgets.QTableView()
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

    def printdf(self):
        print(self.df_model.df)


class DataFrameModel(QtCore.QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), parent=None):
        super().__init__(parent=parent)
        self.df = df

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.df.columns.tolist()[section]
            elif orientation == QtCore.Qt.Vertical:
                return self.df.index.tolist()[section]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if (role == QtCore.Qt.DisplayRole) | (role == QtCore.Qt.EditRole) | (role == QtCore.Qt.ToolTipRole):
            if index.isValid():
                return str(self.df.iloc[index.row(), index.column()])

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.df.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.df.columns)

    def sort(self, column, order):
        colname = self.df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self.df.sort_values(colname, ascending=order == QtCore.Qt.AscendingOrder, inplace=True)
        self.df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()

    def flags(self, index):
        ''' Set flag to allow items editable (and enabled / selectable but those are on by default'''
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        ''' When an item is edited check if it is valid, if it is, return True and emit dataChanged'''
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()

            self.df.iloc[row, column] = value
            self.dataChanged.emit(index, index)
            return True


def show(df):
    app = QtWidgets.QApplication(sys.argv)

    # Choose GUI appearance
    print(QtWidgets.QStyleFactory.keys())
    style = "Fusion"
    app.setStyle(style)
    print("PyQt5 Style: " + style)

    win = PandasGUI(df)
    app.exec_()
