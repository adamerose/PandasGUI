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

import pyqt_fix


class DataFrameTableModel(QtCore.QAbstractTableModel):
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.df = df

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if role == QtCore.Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.df.columns[section]
            else:
                return self.df.index[section]
        if role == QtCore.Qt.ToolTipRole:
            if orientation == Qt.Horizontal:
                return str(self.df.columns[section])
            else:
                return str(self.df.index[section])

    # Required for table
    def columnCount(self, parent=None):
        return len(self.df.columns)

    # Required
    def rowCount(self, parent=None):
        return len(self.df)

    # Required
    def data(self, index: QModelIndex, role: int):
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole or role == QtCore.Qt.ToolTipRole:
            row = index.row()
            col = index.column()
            return str(self.df.iloc[row, col])

        if role == QtCore.Qt.DecorationRole:
            row = index.row()

            color = [QtGui.QColor('red'), QtGui.QColor('green'), QtGui.QColor('blue')][row % 3]
            pixmap = QtGui.QPixmap(26, 26)
            pixmap.fill(color)
            return None

    # Optional
    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    # Required if item is editable
    def setData(self, index, value, role):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            col = index.column()
            try:
                self.df.iat[row, col] = value
            except ValueError as e:
                return False
            self.dataChanged.emit(index, index)

            return True
        return False


class DataFrameView(QtWidgets.QWidget):
    def func(self):
        print(self.horzHeader.size())

    def __init__(self, df):
        super().__init__()
        df = df.copy()

        # Set up DataFrame TableView and Model
        self.tableView = DataFrameTableView(df)
        model = DataFrameTableModel(df)
        self.tableView.setModel(model)

        # Create headers
        self.horzHeader = DataFrameHeaderView(table=self.tableView, df=df, orientation=Qt.Horizontal)
        self.vertHeader = DataFrameHeaderView(table=self.tableView, df=df, orientation=Qt.Vertical)

        # Create scrollbars
        # self.horzScrollBar = QtWidgets.QScrollBar(orientation=Qt.Horizontal)
        # self.vertScrollBar = QtWidgets.QScrollBar(orientation=Qt.Vertical)

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

        # Add items to layout
        self.gridLayout.addWidget(self.horzHeader, 0, 1)
        self.gridLayout.addWidget(self.vertHeader, 1, 0)
        self.gridLayout.addWidget(self.tableView, 1, 1, alignment=Qt.AlignLeft | Qt.AlignTop)
        self.gridLayout.addWidget(self.tableView.horizontalScrollBar(), 2, 1, 2, 1, alignment= Qt.AlignTop)
        self.gridLayout.addWidget(self.tableView.verticalScrollBar(), 1, 2, 1, 2, alignment=Qt.AlignLeft)

        for item in [self.tableView, self.horzHeader, self.vertHeader, self.tableView.horizontalScrollBar(), self.tableView.verticalScrollBar()]:
            item.setContentsMargins(0, 0, 0, 0)
            # item.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
            # item.setStyleSheet("border: 1px solid red;")
            item.show()


class DataFrameTableView(QtWidgets.QTableView):
    def __init__(self, df):
        super().__init__()

        # Hide headers
        self.horizontalHeader().hide()
        self.verticalHeader().hide()

    def sizeHint(self):
        if not self.model():
            return QSize(640, 480)

        # Width
        width = 2
        width += self.verticalHeader().width()
        for i in range(self.model().columnCount()):
            width += self.columnWidth(i)

        # Height
        height = 2
        height += self.horizontalHeader().height()
        for i in range(self.model().rowCount()):
            height += self.rowHeight(i)

        return QSize(width, height)


class DataFrameHeader1(QtWidgets.QHeaderView):
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        # Settings
        self.setSectionsClickable(True)
        self.setHighlightSections(True)

    def paintSection(self, painter: QPainter, rect: QRect, logicalIndex: int):
        if rect.isValid():
            vals = self.model().headerData(logicalIndex, self.orientation(), QtCore.Qt.DisplayRole)

            if type(vals) == str:
                super().paintSection(painter, rect, logicalIndex)
            elif type(vals) == tuple:
                if self.orientation() == Qt.Horizontal:
                    for i, val in enumerate(vals):
                        h = rect.height() / len(vals)
                        subrect = QRect(rect.left(), int(rect.top() + i * h), rect.width(), int(h))

                        painter.save()
                        super().paintSection(painter, subrect, logicalIndex)
                        painter.restore()
                        painter.drawText(subrect, Qt.AlignCenter, val)
                else:
                    for i, val in enumerate(vals):
                        w = rect.width() / len(vals)
                        subrect = QRect(int(rect.left() + i * w), rect.top(), int(w), rect.height())

                        painter.save()
                        super().paintSection(painter, subrect, logicalIndex)
                        painter.restore()
                        painter.drawText(subrect, Qt.AlignCenter, val)

    def sizeHint(self):

        baseSize = self.parent().sizeHint()

        if self.orientation() == Qt.Horizontal:
            vals = self.model().headerData(0, self.orientation(), QtCore.Qt.DisplayRole)
            h = 0
            for val in vals:
                h += QFontMetrics(QtGui.QFont(val)).height()
            baseSize.setHeight(h)
        else:
            vals = self.model().headerData(0, self.orientation(), QtCore.Qt.DisplayRole)
            w = 0
            for val in vals:
                label = QtWidgets.QLabel(val)
                w += label.fontMetrics().boundingRect(label.text()).width() * 1.5
                w = 100
            baseSize.setWidth(w)

        return baseSize


class DataFrameHeaderModel(QtCore.QAbstractTableModel):
    def __init__(self, df, orientation, parent=None):
        super().__init__(parent)
        self.df = df
        self.orientation = orientation

    # Optional for table
    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.ToolTipRole:
            try:
                if orientation == Qt.Horizontal:
                    return str(self.df.columns.names[section])
                else:
                    return str(self.df.index.names[section])
            except IndexError:
                return False

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


# This table view shows the dataframe multindex values
class DataFrameHeaderView(QtWidgets.QTableView):
    def __init__(self, table: DataFrameTableView, df, orientation):
        super().__init__()

        # Setup
        self.orientation = orientation
        self.df = df
        self.table = table
        self.setModel(DataFrameHeaderModel(df, orientation))
        self.setSpans()
        # self.setSpan(1, 1, 2, 2)

        # Settings
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum))
        # self.setSelectionMode(QAbstractItemView.NoSelection)

        # self.setSelectionMode(self.SingleSelection)

        if orientation == Qt.Horizontal:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            # self.setSelectionBehavior(self.SelectColumns)
            self.horizontalHeader().hide()
            self.setStyleSheet("background-color: #F0F0F0;"
                               "border: 1px solid black;"
                               "border-bottom: 0px solid black;")
        else:
            self.resizeColumnsToContents()

            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            # self.setSelectionBehavior(self.SelectRows)
            self.verticalHeader().hide()
            self.setStyleSheet("background-color: #F0F0F0;"
                               "border: 1px solid black;"
                               "border-right: 0px solid black;")

    def setSpans(self):
        df = self.model().df

        if self.orientation == Qt.Horizontal:

            if type(df.columns) == pd.MultiIndex:
                N = len(df.columns[0])
            else:
                N = 1
            print(N)
            for level in range(N):  # Iterates over header sections

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
        else:
            if type(df.index) == pd.MultiIndex:
                N = len(df.index[0])
            else:
                N = 1

            for level in range(N):  # Iterates over the vertical header columns

                if type(df.index) == pd.MultiIndex:
                    arr = [df.index[i][level] for i in range(len(df.index))]
                else:
                    arr = df.index

                # Holds the starting index of a range of equal values.
                # None means it is not currently in a range of equal values.
                match_start = None

                for row in range(1, len(arr)):  # Iterates over cells in col

                    # Check if cell matches cell to its left
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

    def sizeHint(self):
        if self.orientation == Qt.Horizontal:
            width = self.table.sizeHint().width() + self.verticalHeader().width()
            # Height
            height = 2
            for i in range(self.model().rowCount()):
                height += self.rowHeight(i)
        else:
            height = self.table.sizeHint().height() + self.horizontalHeader().height()
            # Width
            width = 2
            for i in range(self.model().columnCount()):
                width += self.columnWidth(i)
        return QSize(width, height)

    # This is needed because otherwise when the horizontal header is a single row it will be made bigger with whitespace
    def minimumSizeHint(self):
        if self.orientation == Qt.Horizontal:
            height = self.sizeHint().height()
            width = 50
        else:
            height = 50
            width = self.sizeHint().width()
        return QSize(width, height)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Windows XP')
    print(QtWidgets.QStyleFactory.keys())

    # Prepare sample data with 3 index levels all unique
    tuples = [('WW1', 'A', '1'), ('WW1', 'A', '2'), ('WW1', 'B', '3'), ('WW1', 'B', '4'),
              ('WW2', 'C', '5'), ('WW2', 'C', '6'), ('WW2', 'D', '7'), ('WW2', 'D', '8')]
    index = pd.MultiIndex.from_tuples(tuples, names=['week', 'letter', 'level'])
    df = pd.DataFrame(pd.np.random.randint(0, 10, (8, 8)), index=index[:8], columns=index[:8])

    # Prepare sample data with 3 index levels all unique
    tuples = [('WW1',), ('WW1',), ('WW1',), ('WW1',), ('WW1',), ('WW1',), ('WW1',), ('WW1',)]
    index = pd.MultiIndex.from_tuples(tuples, names=['week'])
    df2 = pd.DataFrame(pd.np.random.randint(0, 10, (8, 8)), index=index[:8], columns=index[:8])

    singles = [('A'), ('A'), ('C'), ('D'),
               ('E'), ('F'), ('F'), ('H')]
    df3 = pd.DataFrame(pd.np.random.randint(0, 10, (4, 8)), index=singles[0:4], columns=singles[0:8])

    df4 = pd.read_csv("sample_data/pokemon.csv")
    print(type(df.describe().T))
    view = DataFrameView(df.describe().T)
    view.show()

    # view2 = DataFrameTableView(df)
    # view2.setModel(DataFrameTableModel(df))
    # view2.show()
    sys.exit(app.exec_())
