from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, QSize, QRect, Qt, QPoint
from PyQt5.QtGui import QPainter, QFont, QFontMetrics, QPalette, QBrush, QColor, QTransform
from PyQt5.QtWidgets import QSizePolicy
import pandas as pd
import numpy as np
import datetime
import sys

try:
    import pyqt_fix
except:
    pass


class DataFrameView(QtWidgets.QWidget):
    """
    This is a container for the DataFrameTableView and two DataFrameHeaderViews in a QGridLayout
    """

    def __init__(self, df):
        super().__init__()

        df = df.copy()

        # Set up DataFrame TableView and Model
        self.tableView = DataFrameTableView(df)

        # Create headers
        self.horzHeader = DataFrameHeaderView(table=self.tableView, df=df, orientation=Qt.Horizontal)
        self.vertHeader = DataFrameHeaderView(table=self.tableView, df=df, orientation=Qt.Vertical)

        # Set up layout
        self.gridLayout = QtWidgets.QGridLayout()
        self.setLayout(self.gridLayout)

        # Link scrollbars
        self.tableView.horizontalScrollBar().valueChanged.connect(
            self.horzHeader.horizontalScrollBar().setValue)
        self.tableView.verticalScrollBar().valueChanged.connect(
            self.vertHeader.verticalScrollBar().setValue)

        self.tableView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # TESTING
        # btn = QtWidgets.QPushButton("test")
        # btn.clicked.connect(self.func)
        # self.gridLayout.addWidget(btn, 0, 0)

        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)

        # corner_box = QtWidgets.QLabel("X")
        # corner_box.resize(QSize(50, 50))
        # self.gridLayout.addWidget(corner_box, 0, 0, 1, 2)

        # Toggle level names
        if not (any(df.columns.names) or df.columns.name):
            self.horzHeader.verticalHeader().setFixedWidth(1)
        if not (any(df.index.names) or df.index.name):
            self.vertHeader.horizontalHeader().setFixedHeight(1)

        # Set up space left of horzHeader to align it with the data table edge
        horzHeaderLayout = QtWidgets.QHBoxLayout()
        width = self.vertHeader.width() - self.horzHeader.verticalHeader().width()

        horzSpacer = QtWidgets.QSpacerItem(width, 20, QSizePolicy.Fixed, QSizePolicy.Fixed)
        horzHeaderLayout.addItem(horzSpacer)
        horzHeaderLayout.addWidget(self.horzHeader)

        # Set up space above data table to make room for vertHeader level names
        tableViewLayout = QtWidgets.QVBoxLayout()
        height = self.vertHeader.horizontalHeader().height()
        verticalSpacer = QtWidgets.QSpacerItem(20, height, QSizePolicy.Fixed, QSizePolicy.Fixed)
        tableViewLayout.addItem(verticalSpacer)
        tableViewLayout.addWidget(self.tableView)

        self.tableView.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum))

        # Add items to layout
        self.gridLayout.addLayout(horzHeaderLayout, 0, 0, 1, 2)
        self.gridLayout.addWidget(self.vertHeader, 1, 0)
        self.gridLayout.addLayout(tableViewLayout, 1, 1)
        self.gridLayout.addWidget(self.tableView.horizontalScrollBar(), 2, 1, 2, 1)
        self.gridLayout.addWidget(self.tableView.verticalScrollBar(), 1, 2, 1, 1)
        self.gridLayout.setColumnStretch(3, 1)
        self.gridLayout.setRowStretch(4, 1)

        # self.setStyleSheet("background-color: white")

        for item in [self.tableView, self.horzHeader, self.vertHeader, self.tableView.horizontalScrollBar(),
                     self.tableView.verticalScrollBar()]:
            item.setContentsMargins(0, 0, 0, 0)
            # item.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
            # item.setStyleSheet("border: 1px solid red;")
            item.show()


class DataFrameTableModel(QtCore.QAbstractTableModel):
    """
    Model for DataFrameTableView to connect for DataFrame data
    """

    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.df = df

    def headerData(self, section, orientation, role=None):
        # Headers for DataFrameTableView are hidden. Header data is shown in DataFrameHeaderView
        pass

    def columnCount(self, parent=None):
        return len(self.df.columns)

    def rowCount(self, parent=None):
        return len(self.df)

    # Returns the data from the DataFrame
    def data(self, index, role=None):
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole or role == QtCore.Qt.ToolTipRole:
            row = index.row()
            col = index.column()
            cell = self.df.iloc[row, col]

            if isinstance(cell, str):
                try:
                    cell = float(cell)
                except ValueError:
                    pass
            if isinstance(cell, np.floating):
                return "{:.4f}".format(cell)

            return str(cell)

    def flags(self, index):
        # Set the table to be editable
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    # Set data in the DataFrame. Required if table is editable
    def setData(self, index, value, role=None):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            col = index.column()
            try:
                self.df.iat[row, col] = value
            except Exception as e:
                print(e)
                return False
            self.dataChanged.emit(index, index)

            return True


class DataFrameTableView(QtWidgets.QTableView):
    """
    Displays the DataFrame contents as a table
    """

    def __init__(self, df):
        super().__init__()

        # Create and set model
        model = DataFrameTableModel(df)
        self.setModel(model)

        # Hide the headers. The DataFrame headers (index & columns) will be displayed in the DataFrameHeaderViews
        self.horizontalHeader().hide()
        self.verticalHeader().hide()

    def sizeHint(self):
        # Set width and height based on number of columns in model
        # Width
        width = 8  # To account for borders
        width += self.verticalHeader().width()
        for i in range(self.model().columnCount()):
            width += self.columnWidth(i)

        # Height
        height = 8
        height += self.horizontalHeader().height()
        for i in range(self.model().rowCount()):
            height += self.rowHeight(i)

        return QSize(width, height)


class DataFrameHeaderModel(QtCore.QAbstractTableModel):
    """
    Model for DataFrameHeaderView
    """

    def __init__(self, df, orientation, parent=None):
        super().__init__(parent)
        self.df = df
        self.orientation = orientation

    # Required for table
    def columnCount(self, parent=None):

        if self.orientation == Qt.Horizontal:
            return len(self.df.columns.values)

        else:  # Vertical
            if type(self.df.index) == pd.MultiIndex:

                # This if statement is needed because if we get a single string it will return the length of the string
                if type(self.df.index.values[0]) == tuple:
                    return len(self.df.index.values[0])
                else:
                    return 1
            else:
                return 1

    # Required
    def rowCount(self, parent=None):
        # Horizontal
        if self.orientation == Qt.Horizontal:
            if type(self.df.columns) == pd.MultiIndex:
                if type(self.df.columns.values[0]) == tuple:
                    return len(self.df.columns.values[0])
                else:
                    return 1
            else:  # Not multiindex
                return 1
        else:  # Vertical
            if type(self.df.index) == pd.MultiIndex:
                return len(self.df.index.values)
            else:
                return len(self.df.index.values)

    # Required
    def data(self, index: QModelIndex, role: int):
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.ToolTipRole:
            if self.orientation == Qt.Horizontal:
                if type(self.df.columns) == pd.MultiIndex:
                    row = index.row()
                    col = index.column()
                    return str(self.df.columns.values[col][row])
                else:  # Not MultiIndex
                    col = index.column()
                    return str(self.df.columns.values[col])
            elif self.orientation == Qt.Vertical:
                if type(self.df.index) == pd.MultiIndex:
                    row = index.row()
                    col = index.column()
                    return str(self.df.index.values[row][col])
                else:  # Not MultiIndex
                    row = index.row()
                    return str(self.df.index.values[row])

    # The headers of this table will show the level names of the MultiIndex
    def headerData(self, section, orientation, role=None):
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.ToolTipRole:
            # self.orientation says which DataFrameHeaderView this is and orientation says which of its headers this is
            if self.orientation == Qt.Horizontal and orientation == Qt.Vertical:
                if type(self.df.columns) == pd.MultiIndex:
                    return str(self.df.columns.names[section])
                else:
                    return str(self.df.columns.name)
            elif self.orientation == Qt.Vertical and orientation == Qt.Horizontal:
                if type(self.df.columns) == pd.MultiIndex:
                    return str(self.df.index.names[section])
                else:
                    return str(self.df.index.name)

            else:
                # These cells should be hidden anyways
                return None


class DataFrameHeaderView(QtWidgets.QTableView):
    """
    Displays the DataFrame index or columns depending on orientation
    """

    def __init__(self, table: DataFrameTableView, df, orientation):
        super().__init__()

        # Setup
        self.orientation = orientation
        self.df = df
        self.table = table  # This is the DataFrameTableView that this is a header for
        self.setModel(DataFrameHeaderModel(df, orientation))
        self.setSpans()

        # Settings
        self.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum))
        self.setSelectionMode(self.NoSelection)

        # Orientation specific settings
        if orientation == Qt.Horizontal:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Scrollbar is replaced in DataFrameView
            self.horizontalHeader().hide()
            self.verticalHeader().setDisabled(True)
            # self.setStyleSheet("background-color: #F8F8F8;"
            #                    "border: 0px solid black;")
        else:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.verticalHeader().hide()
            self.horizontalHeader().setDisabled(True)
            # self.setStyleSheet("background-color: #F8F8F8;"
            #                    "border: 0px solid black;")

            self.resizeVertHeader()

        # Set initial size
        self.resize(self.sizeHint())

    # Fits columns to contents but with a minimum width and added padding
    def resizeHorzHeader(self):
        min_size = 125
        padding = 20
        self.resizeColumnsToContents()

        for col in range(self.model().columnCount()):
            width = self.columnWidth(col)
            if width + padding < min_size:
                new_width = 125
            else:
                new_width = width + padding

            self.setColumnWidth(col, new_width)
            self.table.setColumnWidth(col, new_width)

    # Fits columns to contents but with a minimum width and added padding
    def resizeVertHeader(self):
        max_size = 250
        self.resizeColumnsToContents()

        for col in range(self.model().columnCount()):
            width = self.columnWidth(col)
            if width > max_size:
                self.setColumnWidth(col, max_size)


    # This sets spans to group together adjacent cells with the same values
    def setSpans(self):
        df = self.model().df

        # Find spans for horizontal DataFrameHeaderView
        if self.orientation == Qt.Horizontal:

            # Find how many levels the MultiIndex has
            if type(df.columns) == pd.MultiIndex:
                N = len(df.columns[0])
            else:
                N = 1

            for level in range(N):  # Iterates over the levels

                # Find how many segments the MultiIndex has
                if type(df.columns) == pd.MultiIndex:
                    arr = [df.columns[i][level] for i in range(len(df.columns))]
                else:
                    arr = df.columns

                # Holds the starting index of a range of equal values.
                # None means it is not currently in a range of equal values.
                match_start = None

                for col in range(1, len(arr)):  # Iterates over cells in row
                    # Check if cell matches cell to its left
                    if arr[col] == arr[col - 1]:
                        if match_start is None:
                            match_start = col - 1
                        # If this is the last cell, need to end it
                        if col == len(arr) - 1:
                            match_end = col
                            span_size = match_end - match_start + 1
                            self.setSpan(level, match_start, 1, span_size)
                    else:
                        if match_start is not None:
                            match_end = col - 1
                            span_size = match_end - match_start + 1
                            self.setSpan(level, match_start, 1, span_size)
                            match_start = None

        # Find spans for vertical DataFrameHeaderView
        else:

            # Find how many levels the MultiIndex has
            if type(df.index) == pd.MultiIndex:
                N = len(df.index[0])
            else:
                N = 1

            for level in range(N):  # Iterates over the levels

                # Find how many segments the MultiIndex has
                if type(df.index) == pd.MultiIndex:
                    arr = [df.index[i][level] for i in range(len(df.index))]
                else:
                    arr = df.index

                # Holds the starting index of a range of equal values.
                # None means it is not currently in a range of equal values.
                match_start = None

                for row in range(1, len(arr)):  # Iterates over cells in column

                    # Check if cell matches cell above
                    if arr[row] == arr[row - 1]:
                        if match_start is None:
                            match_start = row - 1
                        # If this is the last cell, need to end it
                        if row == len(arr) - 1:
                            match_end = row
                            span_size = match_end - match_start + 1
                            self.setSpan(match_start, level, span_size, 1)
                    else:
                        if match_start is not None:
                            match_end = row - 1
                            span_size = match_end - match_start + 1
                            self.setSpan(match_start, level, span_size, 1)
                            match_start = None

    # Return the size of the header needed to match the corresponding DataFrameTableView
    def sizeHint(self):
        # Horizontal DataFrameHeaderView
        if self.orientation == Qt.Horizontal:
            # Width of DataFrameTableView
            width = self.table.sizeHint().width() + self.verticalHeader().width()
            # Height
            height = 8
            for i in range(self.model().rowCount()):
                height += self.rowHeight(i)
        # Vertical DataFrameHeaderView
        else:
            # Height of DataFrameTableView
            height = self.table.sizeHint().height() + self.horizontalHeader().height()
            # Width
            width = 8
            for i in range(self.model().columnCount()):
                width += self.columnWidth(i)
        return QSize(width, height)

    # This is needed because otherwise when the horizontal header is a single row it will add whitespace to be bigger
    def minimumSizeHint(self):
        if self.orientation == Qt.Horizontal:
            height = self.sizeHint().height()
            width = 8
        else:
            height = 8
            width = self.sizeHint().width()
        return QSize(width, height)


# Examples
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Windows XP')
    print(QtWidgets.QStyleFactory.keys())

    # Prepare sample data with 3 index levels all unique
    tuples = [('WW1', 'A', '1'), ('WW1', 'A', '2'), ('WW1', 'B', '3'), ('WW1', 'B', '4'),
              ('WW2', 'B', '5'), ('WW2', 'C', '6'), ('WW2', 'D', '7'), ('WW2', 'D', '8')]
    index = pd.MultiIndex.from_tuples(tuples, names=['week', 'letter', 'level'])
    df = pd.DataFrame(pd.np.random.randint(0, 10, (8, 8)), index=index[:8], columns=index[:8])

    # Prepare sample data with 3 index levels all unique
    tuples = [('WW1',), ('WW1',), ('WW1',), ('WW1',), ('WW1',), ('WW1',), ('WW1',), ('WW1',)]
    index = pd.MultiIndex.from_tuples(tuples, names=['week'])
    df2 = pd.DataFrame(pd.np.random.randint(0, 10, (8, 8)), index=index[:8], columns=index[:8])

    singles = [('A'), ('A'), ('C'), ('D'),
               ('E'), ('F'), ('F'), ('H')]
    df3 = pd.DataFrame(pd.np.random.randint(0, 10, (4, 8)), index=singles[0:4], columns=singles[0:8])

    n=60
    df6 = pd.DataFrame([[1 for i in range(n)]],columns=["x"*i for i in range(n,0,-1)])

    pokemon = pd.read_csv(r'C:\_MyFiles\Programming\Python Projects\pandasgui\pandasgui\sample_data\pokemon.csv')
    # sample = pd.read_csv('sample_data/sample.csv')

    tuples = [('A', 'one', 'x'), ('A', 'one', 'y'), ('A', 'two', 'x'), ('A', 'two', 'y'),
              ('B', 'one', 'x'), ('B', 'one', 'y'), ('B', 'two', 'x'), ('B', 'two', 'y')]
    index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second', 'third'])
    multidf = pd.DataFrame(pd.np.random.randn(8, 8), index=index[:8], columns=index[:8])

    tab_df = multidf.describe(include='all').T
    tab_df.insert(loc=0, column='Type', value=multidf.dtypes)

    pivot_table = pokemon.pivot_table(values='HP', index='Generation')
    df7 = pd.read_csv(r"C:\Users\Adam-PC\Desktop\pivot tut\SalesOrders.csv").describe(include='all')

    view = DataFrameView(df7)
    view.show()

    # view2 = DataFrameTableView(df)
    # view2.setModel(DataFrameTableModel(df))
    # view2.show()
    sys.exit(app.exec_())
