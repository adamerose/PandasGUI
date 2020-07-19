"""Dialog box widgets for various GUI functions"""

import re
import sys

import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from pandasgui.utility import flatten_multiindex


class DialogGeneric(QtWidgets.QDialog):
    """
    This widget allows the user to pick columns from DataFrames and pass the choices to a wrapper class with getters

    Args:
        dataframes:
        destination_names:
        destination_options:
        parent:
        default:
    """

    def __init__(
        self, dataframes, destination_names, title, parent=None, default_df=None
    ):

        super().__init__(parent)

        self.dataframes = dataframes
        self.setWindowTitle(title)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # Create column picker
        self.columnPicker = Dragger(destination_names=destination_names)

        # Create DataFrame picker dropdown
        self.dataframePicker = QtWidgets.QComboBox()
        # Fill the dataframe picker with the names of dataframes
        for df_name in dataframes.keys():
            self.dataframePicker.addItem(df_name)

        # Set default selection and trigger currentIndexChanged
        index = self.dataframePicker.findText(default_df)
        if index != -1:
            self.dataframePicker.setCurrentIndex(index)
        else:
            self.dataframePicker.setCurrentIndex(0)
        self.dataframeChanged()

        # Connect signals
        self.dataframePicker.currentIndexChanged.connect(self.dataframeChanged)

        # Add button
        btnFinish = QtWidgets.QPushButton("Finish")
        btnFinish.clicked.connect(self.finish)
        btnReset = QtWidgets.QPushButton("Reset")
        btnReset.clicked.connect(self.initColumnPicker)
        buttonLayout = QtWidgets.QHBoxLayout()
        spacer = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        buttonLayout.addSpacerItem(spacer)
        buttonLayout.addWidget(btnReset)
        buttonLayout.addWidget(btnFinish)

        # Add all to layout
        layout.addWidget(self.dataframePicker)
        layout.addWidget(self.columnPicker)
        layout.addLayout(buttonLayout)

        self.resize(640, 480)

    def finish(self):
        print("Finish (This should be overridden)")

    def getDestinationItems(self):
        return self.columnPicker.getDestinationItems()

    def getDataFrameName(self):
        return self.dataframePicker.itemText(self.dataframePicker.currentIndex())

    def getDataFrame(self):
        df_name = self.dataframePicker.itemText(self.dataframePicker.currentIndex())
        return self.dataframes[df_name]["dataframe"]

    def dataframeChanged(self):
        print("dfchanged")
        # Get the name of the selected dataframe from the dataframePicker
        selected_df_name = self.dataframePicker.itemText(
            self.dataframePicker.currentIndex()
        )
        self.selected_df = self.dataframes[selected_df_name]["dataframe"].copy()

        self.initColumnPicker()

    def initColumnPicker(self):
        self.columnPicker.clearDestinationItems()
        column_names = list(self.selected_df.columns)
        self.columnPicker.setSourceItems(column_names)


# Widget for dragging options source_names into multiple destination lists (DestList) for usage in
# the dialog function. For example the destinations could be XVariable, Y-Variables, ColorBy for the ScatterPlot dialog
class Dragger(QtWidgets.QWidget):
    def __init__(
        self, sources: iter = ("Default Cols",), destinations: iter = ("Default Dest",)
    ):
        super().__init__()

        # Set up widgets and layout
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        self.columnSource = RegexSourceList(sources)
        self.destinations = []
        for name in destinations:
            self.destinations.append(DestList(name))

        # Add items to layout
        self.destLayout = QtWidgets.QVBoxLayout()
        for dest in self.destinations:
            self.destLayout.addWidget(dest)
        layout.addWidget(self.columnSource)
        layout.addLayout(self.destLayout)

    def setSourceItems(self, items=None):
        self.columnSource.setItems(items)

    def resetItems(self):
        # Clear list
        self.columnSource.setItems([])

    def clearDestinationItems(self):
        # Clear tree
        for dest in self.destinations:
            dest.clear()

    # Return a dict of the items in the destination trees
    def getDestinationItems(self):
        items = {}

        for dest in self.destinations:
            items[dest.title] = dest.getItems()
        return items


# Though the content is a flat list this is implemented as a QTreeWidget for some additional functionality like column
# titles and multiple columns
class DestList(QtWidgets.QTreeWidget):
    def __init__(self, title="Variable", parent=None):
        super().__init__(parent)
        self.title = title
        self.setHeaderLabels([title])

        # Tree settings
        self.setDragDropMode(self.DragDrop)
        self.setSelectionMode(self.ExtendedSelection)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setAcceptDrops(True)

        # Remove items by double clicking them
        self.doubleClicked.connect(self.removeSelectedItems)

    def removeSelectedItems(self):
        for item in self.selectedItems():
            self.invisibleRootItem().removeChild(item)

    def getItems(self):
        """
        Returns:
            [str]: a list of the items in the tree
        """
        items = []
        for i in range(self.topLevelItemCount()):
            treeItem = self.topLevelItem(i)
            items.append(treeItem.text(0))
        return items


class RegexSourceList(QtWidgets.QWidget):
    def __init__(self, item_list, parent=None):
        super().__init__(parent=parent)
        self.item_list = item_list

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.searchBox = QtWidgets.QLineEdit()
        self.list = SourceList(parent=parent)
        self.setItems(item_list)

        self.searchBox.textChanged.connect(self.filter)

        layout.addWidget(self.searchBox)
        layout.addWidget(self.list)

    def filter(self):
        filteredItems = [
            item
            for item in self.item_list
            if re.search(self.searchBox.text().lower(), item.lower())
        ]
        self.list.setItems(filteredItems)

    def setItems(self, items):
        self.item_list = items
        self.list.setItems(items)


class SourceList(QtWidgets.QListWidget):
    """
    A QListWidget that shows the list of column names for a dataframe given as columnNames
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Settings
        self.setDragDropMode(self.DragDrop)
        self.setSelectionMode(self.ExtendedSelection)
        self.setDefaultDropAction(QtCore.Qt.CopyAction)
        self.setAcceptDrops(True)

    # Allow dropping to this list but keep it unchanging by resetting it every time this happens. So the item will just
    # be removed from the DestList it was dragged from.
    def dropEvent(self, event):
        itemsTextList = self.getItems()

        # Default action
        QtWidgets.QListWidget.dropEvent(self, event)

        self.setItems(itemsTextList)

    def getItems(self):
        return [str(self.item(i).text()) for i in range(self.count())]

    # This gets called when an item gets dragged from DestList to SourceList or vice versa
    def setItems(self, items):
        self.clear()
        for name in items:
            self.addItem(name)


# %% Specific dialogs that inherit GenericDialog


###
class PivotDialog(DialogGeneric):
    def __init__(self, dataframes, default_df=None, parent=None):
        super().__init__(
            dataframes,
            destination_names=["index", "columns", "values"],
            default_df=default_df,
            title="Pivot",
            parent=parent,
        )

        self.show()

    def finish(self):
        dict = self.getDestinationItems()
        df = self.getDataFrame()
        df_name = self.getDataFrameName()

        try:
            index = dict["index"]
            columns = dict["columns"]
            values = dict["values"]

            from pandasgui import show

            pivot_table = df.pivot_table(values, index, columns)

            self.gui.add_dataframe(df_name + "_pivot", pivot_table, parent_name=df_name)

        except Exception as e:
            print(e)


##


class Categorizer(QtWidgets.QDialog):
    def __init__(self, df, column):
        super().__init__()

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.df = df
        from pandasgui import show

        self.column_name = column
        self.names = QtWidgets.QLineEdit()
        self.names.textChanged.connect(self.makePicker)

        self.picker = Dragger(["col1", "col2", "col3"], df[column].astype(str).unique())

        # Add button
        btnFinish = QtWidgets.QPushButton("Finish")
        btnFinish.clicked.connect(self.finish)
        btnReset = QtWidgets.QPushButton("Reset")
        btnReset.clicked.connect(self.finish)
        buttonLayout = QtWidgets.QHBoxLayout()
        spacer = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        buttonLayout.addSpacerItem(spacer)
        buttonLayout.addWidget(btnReset)
        buttonLayout.addWidget(btnFinish)

        # Add all to layout
        self.layout.addLayout(buttonLayout)
        self.layout.addWidget(self.names)
        self.layout.addWidget(self.picker)
        self.show()

    def makePicker(self):
        self.layout.removeWidget(self.picker)
        self.df[self.column_name].astype(str).unique()
        self.picker = Dragger(
            self.names.text().split(","), self.df[self.column_name].astype(str).unique()
        )
        print(self.df[self.column_name].astype(str).unique())
        self.layout.addWidget(self.picker)

    def finish(self):
        dict = self.picker.getDestinationItems()

        try:
            print(self.picker.getDestinationItems())
            mapping = {
                "Columbia": "South-America",
                "Ecuador": "South-America",
                "Peru": "South-America",
                "South-Africa": "Africa",
                "Namibia": "Africa",
            }

            results = self.picker.getDestinationItems()
            mapping = {}
            for key in results.keys():
                for value in results[key]:
                    mapping[value] = key

            print(mapping)
            self.df[self.column_name + " Categorized"] = (
                self.df[self.column_name].astype(str).replace(mapping)
            )
            from pandasgui import show

            show(self.df)

        except Exception as e:
            print(e)


class ScatterDialog(DialogGeneric):
    def __init__(self, dataframes, default_df=None, parent=None):
        super().__init__(
            dataframes,
            destination_names=["X Variable", "Y Variable", "Color By"],
            default_df=default_df,
            title="Scatter Plot",
            parent=parent,
        )

        self.show()

    def finish(self):
        dict = self.getDestinationItems()
        df = self.getDataFrame()

        try:
            x = dict["X Variable"][0]
            y = dict["Y Variable"][0]
            c = dict["Color By"][0]
        except IndexError:
            c = None


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    test = Dragger(sources=["a", "b"], destinations=["x", "y", "z"])
    test.show()
    sys.exit(app.exec_())
