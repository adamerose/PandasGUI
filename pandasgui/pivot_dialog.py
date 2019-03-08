from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidgetItem

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from pandasgui.functions import flatten_multiindex
import sys

class PivotDialog(QtWidgets.QDialog):
    def __init__(self, dataframes, gui=None, default=None):
        super().__init__(gui)
        self.core = DialogCore(dataframes, destination_names=['index','columns','values'], parent=self, default=default)

        self.show()

    def finish(self):
        dict = self.core.getChoices()
        df = self.core.getDataFrame()
        df_name = self.core.getDataFrameName()

        try:
            index = dict['index']
            columns = dict['columns']
            values = dict['values']


            from pandasgui import show
            pivot_table = df.pivot_table(values, index, columns)

            self.gui.add_dataframe(df_name+"_pivot", pivot_table, parent_name = df_name)

        except Exception as e:
            print(e)

class DialogCore(QtWidgets.QWidget):
    def __init__(self, dataframes, destination_names=['Default'], parent=None, default=None):
        super().__init__(parent)

        self.dataframes = dataframes

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # Create DataFrame picker dropdown
        self.dataframePicker = QtWidgets.QComboBox()
        for df_name in dataframes.keys():
            self.dataframePicker.addItem(df_name)
        # Set default selection
        index = self.dataframePicker.findText(default)
        if index!=-1:
            self.dataframePicker.setCurrentIndex(index)
        # Connect signal
        self.dataframePicker.currentIndexChanged.connect(self.initColumnPicker)

        # Build column picker
        self.columnPicker = ColumnPicker([],destination_names=destination_names)
        self.initColumnPicker()

        # Add button
        btnFinish = QtWidgets.QPushButton("Finish")
        btnFinish.clicked.connect(self.finish)
        btnReset = QtWidgets.QPushButton("Reset")
        btnReset.clicked.connect(self.initColumnPicker)
        buttonLayout = QtWidgets.QHBoxLayout()
        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        buttonLayout.addSpacerItem(spacer)
        buttonLayout.addWidget(btnReset)
        buttonLayout.addWidget(btnFinish)

        # Add all to layout
        layout.addWidget(self.dataframePicker)
        layout.addWidget(self.columnPicker)
        layout.addLayout(buttonLayout)
        self.resize(640,480)

        self.show()

    def finish(self):
        self.parent().finish()

    def initColumnPicker(self):
        selected_dataframe = self.dataframePicker.itemText(self.dataframePicker.currentIndex())
        print(selected_dataframe)
        self.dataframe = self.dataframes[selected_dataframe]['dataframe'].copy()
        self.dataframe.columns = flatten_multiindex(self.dataframe.columns)
        column_names = self.dataframe.columns

        self.columnPicker.resetValues(column_names)

    def getChoices(self):
        return self.columnPicker.getDestinationItems()

    def getDataFrameName(self):
        return self.dataframePicker.itemText(self.dataframePicker.currentIndex())

    def getDataFrame(self):
        df_name = self.dataframePicker.itemText(self.dataframePicker.currentIndex())
        return self.dataframes[df_name]['dataframe']

# List of column names and multiple lists (as QTreeWidgets) to drag them to
class ColumnPicker(QtWidgets.QWidget):
    def __init__(self, column_names, destination_names=['Default']):
        super().__init__()

        # Set up widgets and layout
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        self.columnSource = SourceList(column_names)
        self.destinations = []
        for name in destination_names:
            self.destinations.append(DestTree(name))


        # Add items to layout
        self.destLayout = QtWidgets.QVBoxLayout()
        for dest in self.destinations:
            self.destLayout.addWidget(dest)
        layout.addWidget(self.columnSource)
        layout.addLayout(self.destLayout)

    def resetValues(self, column_names):

        # Clear list
        self.columnSource.columnNames = column_names
        self.columnSource.resetItems()

        # Clear tree
        for dest in self.destinations:
            dest.clear()

    def moveSelectedRight(self, index):
        sourceItems = self.columnSource.selectedItems()

        for item in sourceItems:
            self.addTreeItem(item.text())

            # Remove from list
            self.columnSource.removeItemWidget(item)

    # Takes a list of QTreeWidgetItem items and adds them to the QListWidget
    def moveSelectedLeft(self):

        items = self.columnDestination.selectedItems()


    def addTreeItem(self, label):
        # Add to tree
        destinationSection = self.columnDestination.selectedItems()[0]
        treeItem = QtWidgets.QTreeWidgetItem(destinationSection, [label])
        destinationSection.setExpanded(True)
        treeItem.setFlags(treeItem.flags() & ~QtCore.Qt.ItemIsDropEnabled)

        print(self.getDestinationItems())

    # Takes a list of QTreeWidgetItem items and removes them from the tree
    def removeTreeItems(self, items):
        for item in items:
            item.parent().removeChild(item)

    def addListItem(self, label):
        pass

    def removeListItem(self, label):
        pass

    # Return a dict of the items in the destination tree
    def getDestinationItems(self):
        items = {}

        for dest in self.destinations:
            items[dest.title] = dest.getItems()
        return items


class DestTree(QtWidgets.QTreeWidget):
    def __init__(self, title='Variable', parent=None):
        super().__init__(parent)
        self.title = title

        # Tree settings
        self.setHeaderLabels([title])
        # self.columnDestination.setSelectionBehavior(self.columnDestination.SelectRows)

        self.setDragDropMode(self.DragDrop)
        self.setSelectionMode(self.ExtendedSelection)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setAcceptDrops(True)

        self.doubleClicked.connect(self.removeSelectedItems)

    def removeSelectedItems(self):
        for item in self.selectedItems():
            self.invisibleRootItem().removeChild(item)

    def dropEvent(self, event):
        QtWidgets.QTreeWidget.dropEvent(self, event)

        # Loop over tree items
        for i in range(self.topLevelItemCount()):
            # Don't allow dropping items inside other items
            treeItem = self.topLevelItem(i)
            treeItem.setFlags(treeItem.flags() & ~QtCore.Qt.ItemIsDropEnabled)

            # Set 2nd column
            treeItem.setData(1,Qt.DisplayRole,"test")

        if type(event.source())==SourceList:
            event.source().resetItems()

        print(self.getItems())

    # Return a list of strings of the items in the tree
    def getItems(self):
        items = []
        for i in range(self.topLevelItemCount()):
            treeItem = self.topLevelItem(i)
            items.append(treeItem.text(0))
        return items

class SourceList(QtWidgets.QListWidget):
    def __init__(self, columnNames=[], parent=None):
        super().__init__(parent)
        self.columnNames = columnNames

        self.resetItems()

        # Settings
        self.setDragDropMode(self.DragDrop)
        self.setSelectionMode(self.ExtendedSelection)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setAcceptDrops(True)

    def dropEvent(self, event):
        print('asf')
        QtWidgets.QListWidget.dropEvent(self, event)

        self.resetItems()

    def resetItems(self):
        self.clear()
        for name in self.columnNames:
            self.addItem(name)

if __name__=='__main__':

    dataframes = {}

    pokemon = pd.read_csv('sample_data/pokemon.csv')
    dataframes['pokemon'] = {}
    dataframes['pokemon']['dataframe'] = pokemon

    sample = pd.read_csv('sample_data/sample.csv')
    dataframes['sample'] = {}
    dataframes['sample']['dataframe'] = sample

    ## PyQt
    app = QtWidgets.QApplication(sys.argv)

    win = PivotDialog(dataframes)
    # win = Tree()
    win.show()
    app.exec_()
