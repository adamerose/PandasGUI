import sys
import threading
import os

import numpy as np
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from pandasgui.utility import get_logger
from pandasgui.store import Store, PandasGuiDataFrame
import pandasgui

logger = get_logger(__name__)


class DataFrameViewer(QtWidgets.QWidget):
    def __init__(self, pgdf: PandasGuiDataFrame):
        super().__init__()

        pgdf = PandasGuiDataFrame.cast(pgdf)
        pgdf.dataframe_viewer = self

        self.pgdf = pgdf

        # Indicates whether the widget has been shown yet. Set to True in
        self._loaded = False

        # Set up DataFrame TableView and Model
        self.dataView = DataTableView(parent=self)

        # Create headers
        self.columnHeader = HeaderView(parent=self, orientation=Qt.Horizontal)
        self.indexHeader = HeaderView(parent=self, orientation=Qt.Vertical)

        self.columnHeaderNames = HeaderNamesView(parent=self, orientation=Qt.Horizontal)
        self.indexHeaderNames = HeaderNamesView(parent=self, orientation=Qt.Vertical)

        # Set up layout
        self.gridLayout = QtWidgets.QGridLayout()
        self.setLayout(self.gridLayout)

        # Link scrollbars
        # Scrolling in data table also scrolls the headers
        self.dataView.horizontalScrollBar().valueChanged.connect(
            self.columnHeader.horizontalScrollBar().setValue
        )
        self.dataView.verticalScrollBar().valueChanged.connect(
            self.indexHeader.verticalScrollBar().setValue
        )
        # Scrolling in headers also scrolls the data table
        self.columnHeader.horizontalScrollBar().valueChanged.connect(
            self.dataView.horizontalScrollBar().setValue
        )
        self.indexHeader.verticalScrollBar().valueChanged.connect(
            self.dataView.verticalScrollBar().setValue
        )

        self.dataView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dataView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Disable scrolling on the headers. Even though the scrollbars are hidden, scrolling by dragging desyncs them
        self.indexHeader.horizontalScrollBar().valueChanged.connect(lambda: None)

        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)

        # Add items to 4x4 grid layout
        self.gridLayout.addWidget(self.columnHeader, 0, 1, 1, 2)
        self.gridLayout.addWidget(self.indexHeader, 1, 0, 2, 2)
        self.gridLayout.addWidget(self.dataView, 2, 2, 1, 1)
        self.gridLayout.addWidget(self.dataView.horizontalScrollBar(), 3, 2, 1, 1)
        self.gridLayout.addWidget(self.dataView.verticalScrollBar(), 2, 3, 1, 1)
        self.gridLayout.addWidget(self.columnHeaderNames, 0, 3, 1, 1)
        self.gridLayout.addWidget(self.indexHeaderNames, 0, 0, 1, 1, Qt.AlignBottom)

        # These expand when the window is enlarged instead of having the grid squares spread out
        self.gridLayout.setColumnStretch(4, 1)
        self.gridLayout.setRowStretch(4, 1)

        self.gridLayout.addItem(
            QtWidgets.QSpacerItem(
                0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
            ),
            0,
            0,
            1,
            1,
        )

        # Do this at top so sizeHints are calculated correctly
        self.set_styles()
        self.updateGeometry()

    def set_styles(self):
        self.setStyleSheet("background-color: #FFF;")
        for header in [
            self.indexHeader,
            self.columnHeader,
            self.indexHeaderNames,
            self.columnHeaderNames,
        ]:
            header.setStyleSheet(
                "background-color: #F5F5F5;"
                "selection-color: black;"
                "selection-background-color: #DDD;"
                "border: 1px solid lightgrey;"
            )

        self.dataView.setStyleSheet(
            "background-color: white;"
            "alternate-background-color: #FAFAFA;"
            "selection-color: black;"
            "selection-background-color: #BBDEFB;"
        )
        for item in [
            self.dataView,
            self.columnHeader,
            self.indexHeader,
            self.indexHeaderNames,
            self.columnHeaderNames,
        ]:
            item.setContentsMargins(0, 0, 0, 0)
            item.setStyleSheet(item.styleSheet() + "border: 0px solid black;")
            item.setItemDelegate(NoFocusDelegate())

        for item in [self.indexHeaderNames, self.columnHeaderNames]:
            item.setStyleSheet(item.styleSheet() + "color: #666;")

    def __reduce__(self):
        # This is so dataclasses.asdict doesn't complain about this being unpicklable
        return "DataFrameViewer"

    def showEvent(self, event: QtGui.QShowEvent):
        """
        Initialize column and row sizes on the first time the widget is shown
        """
        if not self._loaded:
            # Set column widths
            for column_index in range(self.columnHeader.model().columnCount()):
                self.auto_size_column(column_index)

            # Set row heights
            # Just sets a single uniform row height based on the first N rows for performance.
            N = 100
            default_row_height = 30
            for row_index in range(self.indexHeader.model().rowCount())[:N]:
                self.auto_size_row(row_index)
                height = self.indexHeader.rowHeight(row_index)
                default_row_height = max(default_row_height, height)

            # Set limit for default row height
            default_row_height = min(default_row_height, 100)

            self.indexHeader.verticalHeader().setDefaultSectionSize(default_row_height)
            self.dataView.verticalHeader().setDefaultSectionSize(default_row_height)

        self._loaded = True
        event.accept()

    def auto_size_column(self, column_index):
        """
        Set the size of column at column_index to fit its contents
        """
        padding = 30

        self.columnHeader.resizeColumnToContents(column_index)
        width = self.columnHeader.columnWidth(column_index)

        # Iterate over the column's rows and check the width of each to determine the max width for the column
        # Only check the first N rows for performance. If there is larger content in cells below it will be cut off
        N = 100
        for i in range(self.dataView.model().rowCount())[:N]:
            mi = self.dataView.model().index(i, column_index)
            text = self.dataView.model().data(mi)
            w = self.dataView.fontMetrics().boundingRect(text).width()

            width = max(width, w)

        width += padding

        # add maximum allowable column width so column is never too big.
        max_allowable_width = 500
        width = min(width, max_allowable_width)

        self.columnHeader.setColumnWidth(column_index, width)
        self.dataView.setColumnWidth(column_index, width)

        self.dataView.updateGeometry()
        self.columnHeader.updateGeometry()

    def auto_size_row(self, row_index):
        """
        Set the size of row at row_index to fix its contents
        """
        padding = 20

        self.indexHeader.resizeRowToContents(row_index)
        height = self.indexHeader.rowHeight(row_index)

        # Iterate over the row's columns and check the width of each to determine the max height for the row
        # Only check the first N columns for performance.
        N = 100
        for i in range(min(N, self.dataView.model().columnCount())):
            mi = self.dataView.model().index(row_index, i)
            cell_width = self.columnHeader.columnWidth(i)
            text = self.dataView.model().data(mi)
            # Gets row height at a constrained width (the column width).
            # This constrained width, with the flag of Qt.TextWordWrap
            # gets the height the cell would have to be to fit the text.
            constrained_rect = QtCore.QRect(0, 0, cell_width, 0)
            h = (
                self.dataView.fontMetrics()
                .boundingRect(constrained_rect, Qt.TextWordWrap, text)
                .height()
            )
            height = max(height, h)

        height += padding

        self.indexHeader.setRowHeight(row_index, height)
        self.dataView.setRowHeight(row_index, height)

        self.dataView.updateGeometry()
        self.indexHeader.updateGeometry()

    def keyPressEvent(self, event):

        QtWidgets.QWidget.keyPressEvent(self, event)

        if event.matches(QtGui.QKeySequence.Copy):
            self.dataView.copy()
        if event.matches(QtGui.QKeySequence.Paste):
            self.dataView.paste()
        # if event.key() == Qt.Key_P and (event.modifiers() & Qt.ControlModifier):
        #     print("Ctrl + P")
        # if event.key() == Qt.Key_D and (event.modifiers() & Qt.ControlModifier):
        #     print("Ctrl + D")


# Remove dotted border on cell focus.  https://stackoverflow.com/a/55252650/3620725
class NoFocusDelegate(QtWidgets.QStyledItemDelegate):
    def paint(
        self,
        painter: QtGui.QPainter,
        item: QtWidgets.QStyleOptionViewItem,
        ix: QtCore.QModelIndex,
    ):
        if item.state & QtWidgets.QStyle.State_HasFocus:
            item.state = item.state ^ QtWidgets.QStyle.State_HasFocus
        super().paint(painter, item, ix)


class DataTableModel(QtCore.QAbstractTableModel):
    """
    Model for DataTableView to connect for DataFrame data
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.pgdf: PandasGuiDataFrame = parent.pgdf

    def headerData(self, section, orientation, role=None):
        # Headers for DataTableView are hidden. Header data is shown in HeaderView
        pass

    def columnCount(self, parent=None):
        return self.pgdf.dataframe.columns.shape[0]

    def rowCount(self, parent=None):
        return len(self.pgdf.dataframe)

    # Returns the data from the DataFrame
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if (
            role == QtCore.Qt.DisplayRole
            or role == QtCore.Qt.EditRole
            or role == QtCore.Qt.ToolTipRole
        ):
            row = index.row()
            col = index.column()
            cell = self.pgdf.dataframe.iloc[row, col]

            # Need to check type since a cell might contain a list or Series, then .isna returns a Series not a bool
            cell_is_na = pd.isna(cell)
            if type(cell_is_na) == bool and cell_is_na:
                return ""

            # Float formatting
            if isinstance(cell, (float, np.floating)):
                if not role == QtCore.Qt.ToolTipRole:
                    return "{:.4f}".format(cell)

            return str(cell)

        elif role == QtCore.Qt.ToolTipRole:
            row = index.row()
            col = index.column()
            cell = self.pgdf.dataframe.iloc[row, col]

            return str(cell)

    def flags(self, index):
        if self.parent().pgdf.settings.editable:
            return (
                QtCore.Qt.ItemIsEditable
                | QtCore.Qt.ItemIsEnabled
                | QtCore.Qt.ItemIsSelectable
            )
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def setData(self, index, value, role=None):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            col = index.column()
            try:
                self.pgdf.edit_data(row, col, value)
            except Exception as e:
                logger.exception(e)
                return False
            return True


class DataTableView(QtWidgets.QTableView):
    """
    Displays the DataFrame data as a table
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.pgdf: PandasGuiDataFrame = parent.pgdf

        # Create and set model
        model = DataTableModel(parent)
        self.setModel(model)

        # Hide the headers. The DataFrame headers (index & columns) will be displayed in the DataFrameHeaderViews
        self.horizontalHeader().hide()
        self.verticalHeader().hide()

        # Link selection to headers
        self.selectionModel().selectionChanged.connect(self.on_selectionChanged)

        # Settings
        # self.setWordWrap(True)
        # self.resizeRowsToContents()
        self.setAlternatingRowColors(True)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

    def on_selectionChanged(self):
        """
        Runs when cells are selected in the main table. This logic highlights the correct cells in the vertical and
        horizontal headers when a data cell is selected
        """
        columnHeader = self.parent().columnHeader
        indexHeader = self.parent().indexHeader

        # The two blocks below check what columns or rows are selected in the data table and highlights the
        # corresponding ones in the two headers. The if statements check for focus on headers, because if the user
        # clicks a header that will auto-select all cells in that row or column which will trigger this function
        # and cause and infinite loop

        if not columnHeader.hasFocus():
            selection = self.selectionModel().selection()
            columnHeader.selectionModel().select(
                selection,
                QtCore.QItemSelectionModel.Columns
                | QtCore.QItemSelectionModel.ClearAndSelect,
            )

        if not indexHeader.hasFocus():
            selection = self.selectionModel().selection()
            indexHeader.selectionModel().select(
                selection,
                QtCore.QItemSelectionModel.Rows
                | QtCore.QItemSelectionModel.ClearAndSelect,
            )

    def copy(self):
        """
        Copy the selected cells to clipboard in an Excel-pasteable format
        """

        # Get the bounds using the top left and bottom right selected cells
        indexes = self.selectionModel().selection().indexes()
        rows = [ix.row() for ix in indexes]
        cols = [ix.column() for ix in indexes]

        df = self.pgdf.dataframe.iloc[
            min(rows) : max(rows) + 1, min(cols) : max(cols) + 1
        ]

        # Special case for single-cell copy since df.to_clipboard appends extra newline
        if df.shape == (1, 1):
            clipboard = QtWidgets.QApplication.instance().clipboard()
            value = str(df.iloc[0, 0])
            clipboard.setText(value)
        else:
            # If I try to use Pyperclip without starting new thread large selections give access denied error
            threading.Thread(
                target=lambda df: df.to_clipboard(index=False, header=False), args=(df,)
            ).start()

    def paste(self):
        df_to_paste = pd.read_clipboard(sep=",|\t", header=None)

        # Get the bounds using the top left and bottom right selected cells
        indexes = self.selectionModel().selection().indexes()
        rows = [ix.row() for ix in indexes]
        cols = [ix.column() for ix in indexes]

        self.pgdf.paste_data(min(rows), min(cols), df_to_paste)

        # Select the range of cells that were pasted
        self.selectionModel().clearSelection()
        temp = self.selectionMode()
        self.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

        for i in range(df_to_paste.shape[0]):
            for j in range(df_to_paste.shape[1]):
                self.selectionModel().select(
                    self.model().index(min(rows) + i, min(cols) + j),
                    QtCore.QItemSelectionModel.Select,
                )

        self.setSelectionMode(temp)

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

        return QtCore.QSize(width, height)


class HeaderModel(QtCore.QAbstractTableModel):
    def __init__(self, parent, orientation):
        super().__init__(parent)
        self.orientation = orientation
        self.pgdf: PandasGuiDataFrame = parent.pgdf

    def columnCount(self, parent=None):
        if self.orientation == Qt.Horizontal:
            return self.pgdf.dataframe.columns.shape[0]
        else:  # Vertical
            return self.pgdf.dataframe.index.nlevels

    def rowCount(self, parent=None):
        if self.orientation == Qt.Horizontal:
            return self.pgdf.dataframe.columns.nlevels
        elif self.orientation == Qt.Vertical:
            return self.pgdf.dataframe.index.shape[0]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        row = index.row()
        col = index.column()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.ToolTipRole:

            if self.orientation == Qt.Horizontal:

                if type(self.pgdf.dataframe.columns) == pd.MultiIndex:
                    return str(self.pgdf.dataframe.columns.values[col][row])
                else:
                    return str(self.pgdf.dataframe.columns.values[col])

            elif self.orientation == Qt.Vertical:

                if type(self.pgdf.dataframe.index) == pd.MultiIndex:
                    return str(self.pgdf.dataframe.index.values[row][col])
                else:
                    return str(self.pgdf.dataframe.index.values[row])

        if role == QtCore.Qt.DecorationRole:
            if self.pgdf.sort_is_ascending:
                icon = QtGui.QIcon(
                    os.path.join(pandasgui.__path__[0], "images/sort-ascending.png")
                )
            else:
                icon = QtGui.QIcon(
                    os.path.join(pandasgui.__path__[0], "images/sort-descending.png")
                )

            if (
                col == self.pgdf.column_sorted
                and row == self.rowCount() - 1
                and self.orientation == Qt.Horizontal
            ):
                return icon

    # The headers of this table will show the level names of the MultiIndex
    def headerData(self, section, orientation, role=None):
        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole]:

            if self.orientation == Qt.Horizontal and orientation == Qt.Vertical:
                if type(self.pgdf.dataframe.columns) == pd.MultiIndex:
                    return str(self.pgdf.dataframe.columns.names[section])
                else:
                    return str(self.pgdf.dataframe.columns.name)
            elif self.orientation == Qt.Vertical and orientation == Qt.Horizontal:
                if type(self.pgdf.dataframe.index) == pd.MultiIndex:
                    return str(self.pgdf.dataframe.index.names[section])
                else:
                    return str(self.pgdf.dataframe.index.name)
            else:
                return None  # These cells should be hidden anyways


class HeaderView(QtWidgets.QTableView):
    """
    Displays the DataFrame index or columns depending on orientation
    """

    def __init__(self, parent: DataFrameViewer, orientation):
        super().__init__(parent)
        self.pgdf: PandasGuiDataFrame = parent.pgdf

        # Setup
        self.orientation = orientation
        self.table = parent.dataView
        self.setModel(HeaderModel(parent, orientation))
        # These are used during column resizing
        self.header_being_resized = None
        self.resize_start_position = None
        self.initial_header_size = None

        # Events
        self.clicked.connect(self.on_clicked)

        # Handled by self.eventFilter()
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.viewport().installEventFilter(self)

        # Settings
        self.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum
            )
        )
        self.setWordWrap(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

        font = QtGui.QFont()
        font.setBold(True)
        self.setFont(font)

        # Link selection to DataTable
        self.selectionModel().selectionChanged.connect(self.on_selectionChanged)
        self.set_spans()
        self.init_size()

        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Set initial size
        self.resize(self.sizeHint())

    def on_clicked(self, ix: QtCore.QModelIndex):
        # When a header is clicked, sort the DataFrame by that column
        if self.orientation == Qt.Horizontal:
            self.pgdf.sort_column(ix.column())

    # Header
    def on_selectionChanged(self):
        """
        Runs when cells are selected in the Header. This selects columns in the data table when the header is clicked,
        and then calls selectAbove()
        """
        # Check focus so we don't get recursive loop, since headers trigger selection of data cells and vice versa
        if self.hasFocus():
            dataView = self.parent().dataView

            # Set selection mode so selecting one row or column at a time adds to selection each time
            if (
                self.orientation == Qt.Horizontal
            ):  # This case is for the horizontal header
                # Get the header's selected columns
                selection = self.selectionModel().selection()

                # Removes the higher levels so that only the lowest level of the header affects the data table selection
                last_row_ix = self.pgdf.dataframe.columns.nlevels - 1
                last_col_ix = self.model().columnCount() - 1
                higher_levels = QtCore.QItemSelection(
                    self.model().index(0, 0),
                    self.model().index(last_row_ix - 1, last_col_ix),
                )
                selection.merge(higher_levels, QtCore.QItemSelectionModel.Deselect)

                # Select the cells in the data view
                dataView.selectionModel().select(
                    selection,
                    QtCore.QItemSelectionModel.Columns
                    | QtCore.QItemSelectionModel.ClearAndSelect,
                )
            if self.orientation == Qt.Vertical:
                selection = self.selectionModel().selection()

                last_row_ix = self.model().rowCount() - 1
                last_col_ix = self.pgdf.dataframe.index.nlevels - 1
                higher_levels = QtCore.QItemSelection(
                    self.model().index(0, 0),
                    self.model().index(last_row_ix, last_col_ix - 1),
                )
                selection.merge(higher_levels, QtCore.QItemSelectionModel.Deselect)

                dataView.selectionModel().select(
                    selection,
                    QtCore.QItemSelectionModel.Rows
                    | QtCore.QItemSelectionModel.ClearAndSelect,
                )

        self.selectAbove()

    # Take the current set of selected cells and make it so that any spanning cell above a selected cell is selected too
    # This should happen after every selection change
    def selectAbove(self):
        if self.orientation == Qt.Horizontal:
            if self.pgdf.dataframe.columns.nlevels == 1:
                return
        else:
            if self.pgdf.dataframe.index.nlevels == 1:
                return

        for ix in self.selectedIndexes():
            if self.orientation == Qt.Horizontal:
                # Loop over the rows above this one
                for row in range(ix.row()):
                    ix2 = self.model().index(row, ix.column())
                    self.setSelection(
                        self.visualRect(ix2), QtCore.QItemSelectionModel.Select
                    )
            else:
                # Loop over the columns left of this one
                for col in range(ix.column()):
                    ix2 = self.model().index(ix.row(), col)
                    self.setSelection(
                        self.visualRect(ix2), QtCore.QItemSelectionModel.Select
                    )

    # Fits columns to contents but with a minimum width and added padding
    def init_size(self):
        padding = 30

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
            self.resizeColumnsToContents()
            for col in range(self.model().columnCount()):
                width = self.columnWidth(col)
                self.setColumnWidth(col, width + padding)

    # This sets spans to group together adjacent cells with the same values
    def set_spans(self):

        df = self.pgdf.dataframe
        self.clearSpans()
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

    def over_header_edge(self, mouse_position, margin=3):

        # Return the index of the column this x position is on the right edge of
        if self.orientation == Qt.Horizontal:
            x = mouse_position
            if self.columnAt(x - margin) != self.columnAt(x + margin):
                if self.columnAt(x + margin) == 0:
                    # We're at the left edge of the first column
                    return None
                else:
                    return self.columnAt(x - margin)
            else:
                return None

        # Return the index of the row this y position is on the top edge of
        elif self.orientation == Qt.Vertical:
            y = mouse_position
            if self.rowAt(y - margin) != self.rowAt(y + margin):
                if self.rowAt(y + margin) == 0:
                    # We're at the top edge of the first row
                    return None
                else:
                    return self.rowAt(y - margin)
            else:
                return None

    def eventFilter(self, object: QtCore.QObject, event: QtCore.QEvent):

        # If mouse is on an edge, start the drag resize process
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if self.orientation == Qt.Horizontal:
                mouse_position = event.pos().x()
            else:
                mouse_position = event.pos().y()

            if self.over_header_edge(mouse_position) is not None:
                self.header_being_resized = self.over_header_edge(mouse_position)
                self.resize_start_position = mouse_position
                if self.orientation == Qt.Horizontal:
                    self.initial_header_size = self.columnWidth(
                        self.header_being_resized
                    )
                elif self.orientation == Qt.Vertical:
                    self.initial_header_size = self.rowHeight(self.header_being_resized)
                return True
            else:
                self.header_being_resized = None

        # End the drag process
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            self.header_being_resized = None

        # Auto size the column that was double clicked
        if event.type() == QtCore.QEvent.MouseButtonDblClick:
            if self.orientation == Qt.Horizontal:
                mouse_position = event.pos().x()
            else:
                mouse_position = event.pos().y()

            # Find which column or row edge the mouse was over and auto size it
            if self.over_header_edge(mouse_position) is not None:
                header_index = self.over_header_edge(mouse_position)
                if self.orientation == Qt.Horizontal:
                    self.parent().auto_size_column(header_index)
                elif self.orientation == Qt.Vertical:
                    self.parent().auto_size_row(header_index)
                return True

        # Handle active drag resizing
        if event.type() == QtCore.QEvent.MouseMove:
            if self.orientation == Qt.Horizontal:
                mouse_position = event.pos().x()
            elif self.orientation == Qt.Vertical:
                mouse_position = event.pos().y()

            # If this is None, there is no drag resize happening
            if self.header_being_resized is not None:

                size = self.initial_header_size + (
                    mouse_position - self.resize_start_position
                )
                if size > 10:
                    if self.orientation == Qt.Horizontal:
                        self.setColumnWidth(self.header_being_resized, size)
                        self.parent().dataView.setColumnWidth(
                            self.header_being_resized, size
                        )
                    if self.orientation == Qt.Vertical:
                        self.setRowHeight(self.header_being_resized, size)
                        self.parent().dataView.setRowHeight(
                            self.header_being_resized, size
                        )

                    self.updateGeometry()
                    self.parent().dataView.updateGeometry()
                return True

            # Set the cursor shape
            if self.over_header_edge(mouse_position) is not None:
                if self.orientation == Qt.Horizontal:
                    self.viewport().setCursor(QtGui.QCursor(Qt.SplitHCursor))
                elif self.orientation == Qt.Vertical:
                    self.viewport().setCursor(QtGui.QCursor(Qt.SplitVCursor))
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
        return QtCore.QSize(width, height)

    # This is needed because otherwise when the horizontal header is a single row it will add whitespace to be bigger
    def minimumSizeHint(self):
        if self.orientation == Qt.Horizontal:
            return QtCore.QSize(0, self.sizeHint().height())
        else:
            return QtCore.QSize(self.sizeHint().width(), 0)


class HeaderNamesModel(QtCore.QAbstractTableModel):
    def __init__(self, parent, orientation):
        super().__init__(parent)
        self.orientation = orientation
        self.pgdf: PandasGuiDataFrame = parent.pgdf

    def columnCount(self, parent=None):
        if self.orientation == Qt.Horizontal:
            return 1
        elif self.orientation == Qt.Vertical:
            return self.pgdf.dataframe.index.nlevels

    def rowCount(self, parent=None):
        if self.orientation == Qt.Horizontal:
            return self.pgdf.dataframe.columns.nlevels
        elif self.orientation == Qt.Vertical:
            return 1

    def data(self, index, role=QtCore.Qt.DisplayRole):
        row = index.row()
        col = index.column()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.ToolTipRole:

            if self.orientation == Qt.Horizontal:
                val = self.pgdf.dataframe.columns.names[row]
                if val is None:
                    val = ""
                return str(val)

            elif self.orientation == Qt.Vertical:
                val = self.pgdf.dataframe.index.names[col]
                if val is None:
                    val = "index"
                return str(val)

        if role == QtCore.Qt.DecorationRole:
            if self.pgdf.sort_is_ascending:
                icon = QtGui.QIcon(
                    os.path.join(pandasgui.__path__[0], "images/sort-ascending.png")
                )
            else:
                icon = QtGui.QIcon(
                    os.path.join(pandasgui.__path__[0], "images/sort-descending.png")
                )

            if col == self.pgdf.index_sorted and self.orientation == Qt.Vertical:
                return icon


class HeaderNamesView(QtWidgets.QTableView):
    def __init__(self, parent: DataFrameViewer, orientation):
        super().__init__(parent)
        self.pgdf: PandasGuiDataFrame = parent.pgdf

        # Setup
        self.orientation = orientation
        self.setModel(HeaderNamesModel(parent, orientation))

        self.clicked.connect(self.on_clicked)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

        self.horizontalHeader().hide()
        self.verticalHeader().hide()

        self.setSelectionMode(self.NoSelection)

        font = QtGui.QFont()
        font.setBold(True)
        self.setFont(font)
        self.init_size()

    def on_clicked(self, ix: QtCore.QModelIndex):
        # When the index header name is clicked, sort the index by that level
        if self.orientation == Qt.Vertical:
            self.pgdf.sort_index(ix.column())

    def init_size(self):
        # Match vertical header name widths to vertical header
        if self.orientation == Qt.Vertical:
            for ix in range(self.model().columnCount()):
                self.setColumnWidth(ix, self.columnWidth(ix))

    def sizeHint(self):
        if self.orientation == Qt.Horizontal:
            width = self.columnWidth(0)
            height = self.parent().columnHeader.sizeHint().height()
        else:  # Vertical
            width = self.parent().indexHeader.sizeHint().width()
            height = self.rowHeight(0)

        return QtCore.QSize(width, height)

    def minimumSizeHint(self):
        return self.sizeHint()

    def rowHeight(self, row: int) -> int:
        return self.parent().columnHeader.rowHeight(row)

    def columnWidth(self, column: int) -> int:
        if self.orientation == Qt.Horizontal:
            if all(name is None for name in self.pgdf.dataframe.columns.names):
                return 0
            else:
                return super().columnWidth(column)
        else:
            return self.parent().indexHeader.columnWidth(column)


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
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    from pandasgui.datasets import pokemon, mi_manufacturing

    from pandasgui.datasets import simple

    # df = simple.set_index(['first', 'second', 'third']).unstack().sort_values(('fourth', 'bar'))
    df2 = simple.set_index(["first", "second", "third"]).unstack().sort_index(1)

    # view = DataFrameViewer(df)
    # view.show()
    view2 = DataFrameViewer(df2)
    view2.show()

    app.exec_()
