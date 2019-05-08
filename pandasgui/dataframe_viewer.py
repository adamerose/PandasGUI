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


class DataFrameViewer(QtWidgets.QWidget):
    """
    This is a container for the DataTableView and two DataFrameHeaderViews in a QGridLayout
    """

    def __init__(self, df):
        super().__init__()

        df = df.copy()

        # Set up DataFrame TableView and Model
        self.dataView = DataTableView(df, parent=self)

        # Create headers
        self.columnHeader = HeaderView(parent=self, df=df, orientation=Qt.Horizontal)
        self.indexHeader = HeaderView(parent=self, df=df, orientation=Qt.Vertical)

        # Set up layout
        self.gridLayout = QtWidgets.QGridLayout()
        self.setLayout(self.gridLayout)

        # Link scrollbars
        # Scrolling in data table also scrolls the headers
        self.dataView.horizontalScrollBar().valueChanged.connect(
            self.columnHeader.horizontalScrollBar().setValue)
        self.dataView.verticalScrollBar().valueChanged.connect(
            self.indexHeader.verticalScrollBar().setValue)
        # Scrolling in headers also scrolls the data table
        self.columnHeader.horizontalScrollBar().valueChanged.connect(
            self.dataView.horizontalScrollBar().setValue)
        self.indexHeader.verticalScrollBar().valueChanged.connect(
            self.dataView.verticalScrollBar().setValue)

        self.dataView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dataView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Disable scrolling on the headers. Even though the scrollbars are hidden, scrolling by dragging desyncs them
        self.indexHeader.horizontalScrollBar().valueChanged.connect(lambda: None)

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
            self.columnHeader.verticalHeader().setFixedWidth(1)
        if not (any(df.index.names) or df.index.name):
            self.indexHeader.horizontalHeader().setFixedHeight(1)

        # Set up space left of horzHeader to align it with the data table edge
        horzHeaderLayout = QtWidgets.QHBoxLayout()
        width = self.indexHeader.width() - self.columnHeader.verticalHeader().width()

        horzSpacer = QtWidgets.QSpacerItem(width, 20, QSizePolicy.Fixed, QSizePolicy.Fixed)
        horzHeaderLayout.addItem(horzSpacer)
        horzHeaderLayout.addWidget(self.columnHeader)

        # Set up space above data table body and below the horizontal header to make room for vertHeader level names
        tableViewLayout = QtWidgets.QVBoxLayout()
        height = self.indexHeader.horizontalHeader().height()
        verticalSpacer = QtWidgets.QSpacerItem(20, height, QSizePolicy.Fixed, QSizePolicy.Fixed)
        tableViewLayout.addItem(verticalSpacer)
        tableViewLayout.addWidget(self.dataView)

        self.dataView.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum))

        # Add items to layout
        self.gridLayout.addLayout(horzHeaderLayout, 0, 0, 1, 2)
        self.gridLayout.addWidget(self.indexHeader, 1, 0, 1, 1)
        self.gridLayout.addLayout(tableViewLayout, 1, 1)
        self.gridLayout.addWidget(self.dataView.horizontalScrollBar(), 2, 1, 2, 1, alignment=Qt.AlignTop)
        self.gridLayout.addWidget(self.dataView.verticalScrollBar(), 1, 2, 1, 1, alignment=Qt.AlignLeft)

        # self.setStyleSheet("background-color: white")

        for item in [self.dataView, self.columnHeader, self.indexHeader, self.dataView.horizontalScrollBar(),
                     self.dataView.verticalScrollBar()]:
            item.setContentsMargins(0, 0, 0, 0)
            # item.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
            item.setStyleSheet("border: 0px solid black;")
            item.show()

        # self.tableView.setStyleSheet("border: 0px solid red;")


class DataTableModel(QtCore.QAbstractTableModel):
    """
    Model for DataTableView to connect for DataFrame data
    """

    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.df = df

    def headerData(self, section, orientation, role=None):
        # Headers for DataTableView are hidden. Header data is shown in HeaderView
        pass

    def columnCount(self, parent=None):
        if type(self.df) == pd.Series:
            return 1
        else:
            return self.df.columns.shape[0]

    def rowCount(self, parent=None):
        return len(self.df)

    # Returns the data from the DataFrame
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole or role == QtCore.Qt.ToolTipRole:
            row = index.row()
            col = index.column()
            cell = self.df.iloc[row, col]

            # NaN case
            if pd.isnull(cell):
                return ""

            # Float formatting
            if isinstance(cell, (float, np.floating)):
                return "{:.4f}".format(cell)

            return str(cell)

        elif role == QtCore.Qt.ToolTipRole:
            row = index.row()
            col = index.column()
            cell = self.df.iloc[row, col]

            # NaN case
            if pd.isnull(cell):
                return "NaN"

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


class DataTableView(QtWidgets.QTableView):
    """
    Displays the DataFrame contents as a table
    """

    def __init__(self, df, parent):
        super().__init__(parent)
        self.parent = parent

        # Create and set model
        model = DataTableModel(df)
        self.setModel(model)

        # Hide the headers. The DataFrame headers (index & columns) will be displayed in the DataFrameHeaderViews
        self.horizontalHeader().hide()
        self.verticalHeader().hide()

        # Link selection to headers
        self.selectionModel().selectionChanged.connect(self.on_selectionChanged)

    def on_selectionChanged(self):

        if self.hasFocus():
            print('x')
            columnHeader = self.parent.columnHeader
            indexHeader = self.parent.indexHeader

            # Temporarily enable MultiSelection so we can add multiple rows / columns to selection
            initialColumnSelectionMode = columnHeader.selectionMode()
            initialIndexSelectionMode = indexHeader.selectionMode()

            columnHeader.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
            indexHeader.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

            columnHeader.selectionModel().clearSelection()
            indexHeader.selectionModel().clearSelection()

            # Select all rows or columns in the data table view that are selected in headers
            rows = []
            cols = []
            for ix in self.selectedIndexes():
                rows.append(ix.row())
                cols.append(ix.column())
            # Check for focus because we don't want to change it if it trigger the selection in this table view
            for row in set(rows):
                indexHeader.selectRow(row)
            for col in set(cols):
                columnHeader.selectColumn(col)

            columnHeader.setSelectionMode(initialColumnSelectionMode)
            indexHeader.setSelectionMode(initialIndexSelectionMode)

    def keyPressEvent(self, event):

        QtWidgets.QTableView.keyPressEvent(self, event)

        if event.matches(QtGui.QKeySequence.Copy):
            print('Ctrl + C')
            self.copy()
        if event.matches(QtGui.QKeySequence.Paste):
            self.paste()
            print('Ctrl + V')

    def copy(self):
        # Set up clipboard object
        app = QtWidgets.QApplication.instance()
        if not app:
            app = QtWidgets.QApplication(sys.argv)
        clipboard = app.clipboard()

        text = ""

        last_row = None
        for ix in self.selectedIndexes():
            if last_row is None:
                last_row = ix.row()

            value = str(self.model().data(self.model().index(ix.row(), ix.column())))

            if text == "":
                # First item
                pass
            elif ix.row() != last_row:
                # New row
                text += '\n'
                last_row = ix.row()
            else:
                text += '\t'

            text += value

        clipboard.setText(text)

    def paste(self):
        # Set up clipboard object
        app = QtWidgets.QApplication.instance()
        if not app:
            app = QtWidgets.QApplication(sys.argv)
        clipboard = app.clipboard()

        # TODO
        print(clipboard.text())

    def sizeHint(self):
        # Set width and height based on number of columns in model
        # Width
        width = 2 * self.frameWidth()  # Account for border & padding
        # width += self.verticalScrollBar().width()  # Dark theme has scrollbars always shown
        for i in range(self.model().columnCount()):
            width += self.columnWidth(i)

        # Height
        height = 2 * self.frameWidth()  # Account for border & padding
        # height += self.horizontalScrollBar().height()  # Dark theme has scrollbars always shown
        for i in range(self.model().rowCount()):
            height += self.rowHeight(i)

        return QSize(width, height)


class HeaderModel(QtCore.QAbstractTableModel):
    """
    Model for HeaderView
    """

    def __init__(self, df, orientation, parent=None):
        super().__init__(parent)
        self.df = df
        self.orientation = orientation

    def columnCount(self, parent=None):
        if self.orientation == Qt.Horizontal:
            return self.df.columns.shape[0]
        else:  # Vertical
            return self.df.index.nlevels

    def rowCount(self, parent=None):
        if self.orientation == Qt.Horizontal:
            return self.df.columns.nlevels
        elif self.orientation == Qt.Vertical:
            return self.df.index.shape[0]

    def data(self, index, role=None):
        row = index.row()
        col = index.column()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.ToolTipRole:

            if self.orientation == Qt.Horizontal:

                if type(self.df.columns) == pd.MultiIndex:
                    return str(self.df.columns.values[col][row])
                else:
                    return str(self.df.columns.values[col])

            elif self.orientation == Qt.Vertical:

                if type(self.df.index) == pd.MultiIndex:
                    return str(self.df.index.values[row][col])
                else:
                    return str(self.df.index.values[row])

    # The headers of this table will show the level names of the MultiIndex
    def headerData(self, section, orientation, role=None):
        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole]:

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
                return None  # These cells should be hidden anyways


class HeaderView(QtWidgets.QTableView):
    """
    Displays the DataFrame index or columns depending on orientation
    """

    def __init__(self, parent: DataFrameViewer, df, orientation):
        super().__init__(parent)

        # Setup
        self.orientation = orientation
        self.df = df
        self.parent = parent
        self.table = parent.dataView
        self.setModel(HeaderModel(df, orientation))
        self.setSpans()

        # Settings
        self.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum))
        # self.setSelectionMode(self.NoSelection)

        # Link selection to DataTable
        self.selectionModel().selectionChanged.connect(self.on_selectionChanged)

        # Orientation specific settings
        if orientation == Qt.Horizontal:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Scrollbar is replaced in DataFrameViewer
            self.horizontalHeader().hide()
            self.verticalHeader().setDisabled(True)
            self.verticalHeader().setHighlightSections(False)  # Selection lags a lot without this

        else:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.verticalHeader().hide()
            self.horizontalHeader().setDisabled(True)
            self.horizontalHeader().setHighlightSections(False)  # Selection lags a lot without this

            self.resizeVertHeader()

        # Set initial size
        self.resize(self.sizeHint())

    def on_selectionChanged(self):
        # Check focus so we don't get recursive loop, since headers trigger selection of data cells and vice versa
        if self.hasFocus():

            # Clear selection of other header
            if self.orientation == Qt.Horizontal:
                self.parent.indexHeader.selectionModel().clearSelection()
            else:
                self.parent.columnHeader.selectionModel().clearSelection()

            dataView = self.parent.dataView

            # Set selection mode so selecting one row or column at a time adds to selection each time
            initialSelectionMode = dataView.selectionMode()
            dataView.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
            dataView.selectionModel().clearSelection()

            if self.orientation == Qt.Horizontal:
                # Find max row (lowest row visually containing a selected cell)
                maximum = max([ix.row() for ix in self.selectedIndexes()])
                cols = []
                # Loop over selected cells
                for ix in self.selectedIndexes():
                    if ix.row() == maximum:
                        for seg in range(self.columnSpan(ix.row(), ix.column())):
                            cols.append(ix.column() + seg)

                # Selection
                total_selection = QtCore.QItemSelection()
                cols = sorted(list(set(cols)))
                contiguous_start = cols[0]
                contiguous_prev = cols[0]
                for col in cols:
                    if col == cols[-1]:
                        start = contiguous_start
                        end = contiguous_prev

                        selection = QtCore.QItemSelection(dataView.model().index(0, col),
                                                          dataView.model().index(dataView.model().rowCount() - 1, col))
                        total_selection.merge(selection, QtCore.QItemSelectionModel.Select)
                    elif (col != contiguous_prev) + 1:
                        start = contiguous_start
                        end = contiguous_prev

                        contiguous_start = col
                    else:
                        contiguous_prev = col

                selection = QtCore.QItemSelection(dataView.model().index(0, start),
                                                  dataView.model().index(dataView.model().rowCount() - 1, end))
                total_selection.merge(selection, QtCore.QItemSelectionModel.Select)

                dataView.selectionModel().select(total_selection, QtCore.QItemSelectionModel.Select)


            else:

                # Find rightmost column with a selected cell
                maximum = max([ix.column() for ix in self.selectedIndexes()])
                print('A')
                rows = []
                # Loop over selected cells
                x = self.selectionModel().selectedIndexes()
                print('B')
                for ix in x:
                    if ix.column() == maximum:
                        for seg in range(self.rowSpan(ix.row(), ix.column())):
                            rows.append(ix.row() + seg)
                print('C')
                # Selection
                total_selection = QtCore.QItemSelection()
                rows = sorted(list(set(rows)))
                contiguous_start = rows[0]
                contiguous_prev = rows[0]

                for row in rows:
                    if row == rows[-1]:
                        start = contiguous_start
                        end = contiguous_prev

                        selection = QtCore.QItemSelection(dataView.model().index(row, 0),
                                                          dataView.model().index(row, dataView.model().columnCount() - 1))
                        total_selection.merge(selection, QtCore.QItemSelectionModel.Select)
                    elif (row != contiguous_prev) + 1:
                        start = contiguous_start
                        end = contiguous_prev

                        contiguous_start = row
                    else:
                        contiguous_prev = row
                selection = QtCore.QItemSelection(dataView.model().index(start, 0),
                                                  dataView.model().index(end, dataView.model().columnCount() - 1))
                total_selection.merge(selection, QtCore.QItemSelectionModel.Select)

                dataView.selectionModel().select(total_selection, QtCore.QItemSelectionModel.Select)

            dataView.setSelectionMode(initialSelectionMode)
        self.selectAbove()

    # Take the current set of selected cells and make it so that any spanning cell above a selected cell is selected too
    # This should happen after every selection change
    def selectAbove(self):
        for ix in self.selectedIndexes():
            if self.orientation == Qt.Horizontal:
                # Loop over the rows above this one
                for row in range(ix.row()):
                    ix2 = self.model().index(row, ix.column())
                    self.setSelection(self.visualRect(ix2), QtCore.QItemSelectionModel.Select)
            else:
                # Loop over the columns left of this one
                for col in range(ix.column()):
                    ix2 = self.model().index(ix.row(), col)
                    self.setSelection(self.visualRect(ix2), QtCore.QItemSelectionModel.Select)

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

        # Find spans for horizontal HeaderView
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

        # Find spans for vertical HeaderView
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

    # Return the size of the header needed to match the corresponding DataTableView
    def sizeHint(self):

        # Horizontal HeaderView
        if self.orientation == Qt.Horizontal:
            # Width of DataTableView
            width = self.table.sizeHint().width() + self.verticalHeader().width()
            # Height
            height = 2 * self.frameWidth()  # Account for border & padding
            for i in range(self.model().rowCount()):
                height += self.rowHeight(i)

        # Vertical HeaderView
        else:
            # Height of DataTableView
            height = self.table.sizeHint().height() + self.horizontalHeader().height()
            # Width
            width = 2 * self.frameWidth()  # Account for border & padding
            for i in range(self.model().columnCount()):
                width += self.columnWidth(i)
        return QSize(width, height)

    # This is needed because otherwise when the horizontal header is a single row it will add whitespace to be bigger
    def minimumSizeHint(self):
        if self.orientation == Qt.Horizontal:
            return QSize(0, self.sizeHint().height())
        else:
            return QSize(self.sizeHint().width(), 0)


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

    n = 60
    df6 = pd.DataFrame([[1 for i in range(n)]], columns=["x" * i for i in range(n, 0, -1)])

    pokemon = pd.read_csv(r'C:\_MyFiles\Programming\Python Projects\pandasgui\pandasgui\sample_data\pokemon.csv')
    sample = pd.read_csv('sample_data/sample.csv')

    tuples = [('A', 'one', 'x'), ('A', 'one', 'y'), ('A', 'two', 'x'), ('A', 'two', 'y'),
              ('B', 'one', 'x'), ('B', 'one', 'y'), ('B', 'two', 'x'), ('B', 'two', 'y')]
    index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second', 'third'])
    multidf = pd.DataFrame(pd.np.random.randn(8, 8), index=index[:8], columns=index[:8])

    ser = pd.Series(pd.np.random.randn(8), index=index[:8])

    tab_df = multidf.describe(include='all').T
    tab_df.insert(loc=0, column='Type', value=multidf.dtypes)

    pivot_table = pokemon.pivot_table(values='HP', index='Generation')
    df7 = pd.read_csv(r"C:\Users\Adam-PC\Desktop\pivot tut\SalesOrders.csv").describe(include='all')

    df8 = pd.read_csv(r'C:\Users\Adam-PC\Desktop\large_wafer_data.csv')

    view = DataFrameViewer(df8)
    view.show()

    # view2 = DataTableView(df)
    # view2.setModel(DataTableModel(df))
    # view2.show()
    sys.exit(app.exec_())
