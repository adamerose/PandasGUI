"""
Defines the DataFrameViewer class to display DataFrames as a table. The DataFrameViewer is made up of three separate
QTableWidgets... DataTableView for the DataFrame's contents, and two HeaderView widgets for the column and index headers
"""

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, QSize, QRect, Qt, QPoint, QItemSelectionModel
from PyQt5.QtGui import QPainter, QFont, QFontMetrics, QPalette, QBrush, QColor, QTransform
from PyQt5.QtWidgets import QSizePolicy
import pandas as pd
import numpy as np
import datetime
import sys


class DataFrameViewer(QtWidgets.QWidget):
    """
    Displays a DataFrame as a table.

    Args:
        df (DataFrame): The DataFrame to display
    """

    def __init__(self, df):

        super().__init__()
        self._loaded = False

        if not type(df) == pd.DataFrame:
            orig_type = type(df)
            df = df.to_frame()
            print(f'DataFrame was automatically converted from {orig_type} to DataFrame for viewing')


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
        self.dataView.horizontalScrollBar().valueChanged.connect(self.columnHeader.horizontalScrollBar().setValue)
        self.dataView.verticalScrollBar().valueChanged.connect(self.indexHeader.verticalScrollBar().setValue)
        # Scrolling in headers also scrolls the data table
        self.columnHeader.horizontalScrollBar().valueChanged.connect(self.dataView.horizontalScrollBar().setValue)
        self.indexHeader.verticalScrollBar().valueChanged.connect(self.dataView.verticalScrollBar().setValue)

        self.dataView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dataView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Disable scrolling on the headers. Even though the scrollbars are hidden, scrolling by dragging desyncs them
        self.indexHeader.horizontalScrollBar().valueChanged.connect(lambda: None)

        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)

        # Toggle level names
        if not (any(df.columns.names) or df.columns.name):
            self.columnHeader.verticalHeader().setFixedWidth(0)
        if not (any(df.index.names) or df.index.name):
            self.indexHeader.horizontalHeader().setFixedHeight(0)

        # Add items to layout
        self.gridLayout.addWidget(self.columnHeader, 0, 1, 1, 2)
        self.gridLayout.addWidget(self.indexHeader, 1, 0, 2, 2)
        self.gridLayout.addWidget(self.dataView, 2, 2, 1, 1)
        self.gridLayout.addWidget(self.dataView.horizontalScrollBar(), 3, 2, 1, 1)
        self.gridLayout.addWidget(self.dataView.verticalScrollBar(), 2, 3, 1, 1)

        # These expand when the window is enlarged instead of having the grid squares spread out
        self.gridLayout.setColumnStretch(4, 1)
        self.gridLayout.setRowStretch(4, 1)

        # These placeholders will ensure the size of the blank spaces beside our headers
        self.gridLayout.addWidget(TrackingSpacer(ref_x=self.columnHeader.verticalHeader()), 3, 1, 1, 1)
        self.gridLayout.addWidget(TrackingSpacer(ref_y=self.indexHeader.horizontalHeader()), 1, 2, 1, 1)
        self.gridLayout.addItem(QtWidgets.QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding), 0, 0, 1, 1)

        # Styling
        for header in [self.indexHeader, self.columnHeader]:
            header.setStyleSheet("background-color: white;"
                                 "selection-color: black;"
                                 "selection-background-color: #EAEAEA;")

        self.dataView.setStyleSheet("background-color: white;"
                                    "alternate-background-color: #F4F6F6;"
                                    "selection-color: black;"
                                    "selection-background-color: #BBDEFB;")

        for item in [self.dataView, self.columnHeader, self.indexHeader]:
            item.setContentsMargins(0, 0, 0, 0)
            item.setStyleSheet(item.styleSheet() + "border: 0px solid black;")
            item.setItemDelegate(NoFocusDelegate())

    def showEvent(self, event: QtGui.QShowEvent):
        if not self._loaded:
            for column_index in range(self.columnHeader.model().columnCount()):
                self.auto_size_column(column_index)
        self._loaded = True
        event.accept()

    def auto_size_column(self, column_index):
        padding = 20

        self.columnHeader.resizeColumnToContents(column_index)
        width = self.columnHeader.columnWidth(column_index)

        for i in range(min(100, self.dataView.model().rowCount())):
            mi = self.dataView.model().index(i, column_index)
            text = self.dataView.model().data(mi)
            w = self.dataView.fontMetrics().boundingRect(text).width()

            if w > width:
                width = w

        width += padding
        self.columnHeader.setColumnWidth(column_index, width)
        self.dataView.setColumnWidth(column_index, width)

        self.dataView.updateGeometry()
        self.columnHeader.updateGeometry()

    def keyPressEvent(self, event):

        QtWidgets.QWidget.keyPressEvent(self, event)

        if event.matches(QtGui.QKeySequence.Copy):
            print('Ctrl + C')
            self.dataView.copy()
        if event.matches(QtGui.QKeySequence.Paste):
            self.dataView.paste()
            print('Ctrl + V')
        if event.key() == Qt.Key_P and (event.modifiers() & Qt.ControlModifier):
            self.dataView.print()
            print('Ctrl + P')
        if event.key() == Qt.Key_D and (event.modifiers() & Qt.ControlModifier):
            self.debug()
            print('Ctrl + D')

    def debug(self):
        print(self.columnHeader.sizeHint())
        print(self.dataView.sizeHint())
        print(self.dataView.horizontalScrollBar().sizeHint())


# Remove dotted border on cell focus.  https://stackoverflow.com/a/55252650/3620725
class NoFocusDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, QPainter, QStyleOptionViewItem, QModelIndex):
        if QStyleOptionViewItem.state & QtWidgets.QStyle.State_HasFocus:
            QStyleOptionViewItem.state = QStyleOptionViewItem.state ^ QtWidgets.QStyle.State_HasFocus
        super().paint(QPainter, QStyleOptionViewItem, QModelIndex)


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
    Displays the DataFrame data as a table
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

        # Settings
        self.setWordWrap(False)
        self.setAlternatingRowColors(True)

    def on_selectionChanged(self):
        columnHeader = self.parent.columnHeader
        indexHeader = self.parent.indexHeader

        if not columnHeader.hasFocus():
            selection = self.selectionModel().selection()
            columnHeader.selectionModel().select(selection,
                                                 QItemSelectionModel.Columns | QItemSelectionModel.ClearAndSelect)

        if not indexHeader.hasFocus():
            selection = self.selectionModel().selection()
            indexHeader.selectionModel().select(selection,
                                                QItemSelectionModel.Rows | QItemSelectionModel.ClearAndSelect)

    def print(self):
        print(self.model().df)

    def copy(self):
        # Set up clipboard object
        app = QtWidgets.QApplication.instance()
        if not app:
            app = QtWidgets.QApplication(sys.argv)
        clipboard = app.clipboard()

        text = ""

        last_row = None
        indexes = self.selectionModel().selection().indexes()

        for ix in indexes:
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
                if type(self.df.index) == pd.MultiIndex:
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
        # These are used during column resizing
        self.column_being_resized = None
        self.resize_start_position = None
        self.initial_column_width = None

        # Handled by self.eventFilter()
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.viewport().installEventFilter(self)

        # Settings
        self.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum))
        self.setWordWrap(False)
        self.setFont(QtGui.QFont("Times", weight=QtGui.QFont.Bold))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Link selection to DataTable
        self.selectionModel().selectionChanged.connect(self.on_selectionChanged)
        self.setSpans()
        self.initSize()

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

        # Set initial size
        self.resize(self.sizeHint())

    def test(self):
        print('test')

    # Header
    def on_selectionChanged(self):
        # Check focus so we don't get recursive loop, since headers trigger selection of data cells and vice versa
        if self.hasFocus():
            dataView = self.parent.dataView

            # Set selection mode so selecting one row or column at a time adds to selection each time

            if self.orientation == Qt.Horizontal:
                selection = self.selectionModel().selection()

                last_row_ix = self.df.columns.nlevels - 1
                last_col_ix = self.model().columnCount() - 1
                higher_levels = QtCore.QItemSelection(self.model().index(0, 0),
                                                      self.model().index(last_row_ix - 1, last_col_ix))

                selection.merge(higher_levels, QtCore.QItemSelectionModel.Deselect)
                dataView.selectionModel().select(selection,
                                                 QtCore.QItemSelectionModel.Columns | QtCore.QItemSelectionModel.ClearAndSelect)
            if self.orientation == Qt.Vertical:
                selection = self.selectionModel().selection()

                last_row_ix = self.model().rowCount() - 1
                last_col_ix = self.df.index.nlevels - 1
                higher_levels = QtCore.QItemSelection(self.model().index(0, 0),
                                                      self.model().index(last_row_ix, last_col_ix - 1))

                selection.merge(higher_levels, QtCore.QItemSelectionModel.Deselect)
                dataView.selectionModel().select(selection,
                                                 QtCore.QItemSelectionModel.Rows | QtCore.QItemSelectionModel.ClearAndSelect)

        self.selectAbove()

    # Take the current set of selected cells and make it so that any spanning cell above a selected cell is selected too
    # This should happen after every selection change
    def selectAbove(self):
        if self.orientation == Qt.Horizontal:
            if self.df.columns.nlevels == 1:
                return
        else:
            if self.df.index.nlevels == 1:
                return

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
    def initSize(self):
        padding = 20

        if self.orientation == Qt.Horizontal:
            min_size = 100

            self.resizeColumnsToContents()

            for col in range(self.model().columnCount()):
                width = self.columnWidth(col)
                if width + padding < min_size:
                    new_width = min_size
                else:
                    new_width = width + padding

                self.setColumnWidth(col, new_width)
                self.table.setColumnWidth(col, new_width)
        else:
            max_size = 1000
            self.resizeColumnsToContents()
            for col in range(self.model().columnCount()):
                width = self.columnWidth(col)
                self.setColumnWidth(col, width + padding)

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

    # Return the index of the column this x position is on the right edge of
    def over_column_edge(self, x, margin=3):
        if self.columnAt(x - margin) != self.columnAt(x + margin):
            if self.columnAt(x + margin) == 0:
                # We're at the left edge of the first column
                return None
            else:
                return self.columnAt(x - margin)
        else:
            return None

    def eventFilter(self, object: QtCore.QObject, event: QtCore.QEvent):

        # If mouse is on an edge, start the drag resize process
        if event.type() == QtCore.QEvent.MouseButtonPress:
            x = event.pos().x()
            if self.over_column_edge(x) is not None:
                self.column_being_resized = self.over_column_edge(x)
                self.resize_start_position = x
                self.initial_column_width = self.columnWidth(self.column_being_resized)
                return True
            else:
                self.column_being_resized = None

        # End the drag process
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            self.column_being_resized = None

        # Auto size the column that was double clicked
        if event.type() == QtCore.QEvent.MouseButtonDblClick:
            x = event.pos().x()
            if self.over_column_edge(x) is not None:
                column_index = self.over_column_edge(x)
                self.parent.auto_size_column(column_index)
                return True

        # Handle active drag resizing
        if event.type() == QtCore.QEvent.MouseMove:
            x = event.pos().x()

            # If this is None, there is no drag resize happening
            if self.column_being_resized is not None:
                width = self.initial_column_width + (x - self.resize_start_position)
                if width > 10:
                    self.setColumnWidth(self.column_being_resized, width)
                    if self.orientation == Qt.Horizontal:
                        self.parent.dataView.setColumnWidth(self.column_being_resized, width)

                    self.updateGeometry()
                    self.parent.dataView.updateGeometry()
                return True

            # Set the cursor shape
            if self.over_column_edge(x) is not None:
                self.viewport().setCursor(QtGui.QCursor(Qt.SplitHCursor))
            else:
                self.viewport().setCursor(QtGui.QCursor(Qt.ArrowCursor))

        return False

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


# This is a fixed size widget with a size that tracks some other widget
class TrackingSpacer(QtWidgets.QFrame):
    def __init__(self, ref_x=None, ref_y=None):
        super().__init__()
        self.ref_x = ref_x
        self.ref_y = ref_y

    def minimumSizeHint(self):
        width = 0
        height = 0
        if self.ref_x:
            width = self.ref_x.width()
        if self.ref_y:
            height = self.ref_y.height()

        return QtCore.QSize(width, height)


# Examples
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    from pandasgui.datasets import iris, flights, multi, pokemon, multidf

    # view = DataFrameViewer(pokemon)
    # view.show()

    view2 = DataFrameViewer(multidf)
    view2.show()

    sys.exit(app.exec_())
