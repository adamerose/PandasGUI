# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\_MyFiles\Programming\Python Projects\pandasgui\qtdesigner\scatter.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from functions import flatten_multiindex

class scatterDialog(QtWidgets.QDialog):
    def __init__(self, dataframes):
        super().__init__()
        self.show()

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.dataframePicker = QtWidgets.QComboBox()
        for df_name in dataframes.keys():
            self.dataframePicker.addItem(df_name)

        selected_column = self.dataframePicker.itemText(self.dataframePicker.currentIndex())
        self.dataframe = dataframes[selected_column]['dataframe'].copy()
        self.dataframe.columns = flatten_multiindex(self.dataframe.columns)
        column_names = self.dataframe.columns
        print(column_names)
        self.columnPicker = columnPicker(column_names)

        btnFinish = QtWidgets.QPushButton("Plot")
        btnFinish.clicked.connect(self.finish)
        layout.addWidget(self.dataframePicker)
        layout.addWidget(self.columnPicker)
        layout.addWidget(btnFinish)

    def finish(self):
        dict = self.columnPicker.getDestinationItems()
        x = dict['X Variable'][0]
        y = dict['Y Variable'][0]
        c = dict['Color By'][0]

        print(x,y,c)

        df = pd.read_csv('sample_data/pokemon.csv')
        sns.scatterplot(x,y,c,data=df)
        plt.show()

class columnPicker(QtWidgets.QWidget):
    def __init__(self, column_names):
        super().__init__()
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        self.columnSource = QtWidgets.QListWidget()
        self.columnDestination = QtWidgets.QTreeWidget()

        # Add buttons
        btnLayout = QtWidgets.QVBoxLayout()
        btnMoveRight = QtWidgets.QPushButton(">")
        btnMoveRight.clicked.connect(self.moveRight)
        btnMoveLeft = QtWidgets.QPushButton("<")
        btnLayout.addWidget(btnMoveRight)
        btnLayout.addWidget(btnMoveLeft)

        # Add column names
        for name in column_names:
            self.columnSource.addItem(name)

        # List settings
        self.columnSource.setDragDropMode(QtWidgets.QListWidget.DragDrop)

        # Tree settings
        self.columnDestination.setHeaderLabels(['Column Name'])
        self.columnDestination.setDragDropMode(QtWidgets.QTreeWidget.InternalMove)
        root = self.columnDestination.invisibleRootItem()
        root.setFlags(root.flags() & ~QtCore.Qt.ItemIsDropEnabled)

        # Add tree sections
        sections = ['X Variable', 'Y Variable', 'Color By']
        for name in sections:
            treeItem = QtWidgets.QTreeWidgetItem(self.columnDestination, [name])
            treeItem.setFlags(treeItem.flags() & ~QtCore.Qt.ItemIsDragEnabled)
            treeItem.setExpanded(True)
            # This doesn't work. https://bugreports.qt.io/browse/QTBUG-59354
            # treeItem.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.DontShowIndicator)


        # Add items to layout
        layout.addWidget(self.columnSource)
        layout.addLayout(btnLayout)
        layout.addWidget(self.columnDestination)

        self.show()

        # Select first section
        self.columnDestination.setCurrentItem(self.columnDestination.topLevelItem(0))

    def moveRight(self):
        sourceItems = self.columnSource.selectedItems()

        for item in sourceItems:
            self.addTreeItem(item.text())

            # Remove from list
            self.columnSource.removeItemWidget(item)

    def addTreeItem(self, label):
        # Add to tree
        destinationSection = self.columnDestination.selectedItems()[0]
        treeItem = QtWidgets.QTreeWidgetItem(destinationSection, [label])
        destinationSection.setExpanded(True)
        treeItem.setFlags(treeItem.flags() & ~QtCore.Qt.ItemIsDropEnabled)

        print(self.getDestinationItems())

    def removeTreeItem(self, section, label):
        pass

    def addListItem(self, label):
        pass

    def removeListItem(self, label):
        pass

    def getDestinationItems(self):
        items = {}

        for i in range(self.columnDestination.topLevelItemCount()):
            section = self.columnDestination.topLevelItem(i)
            section_name = section.text(0)
            items[section_name] = []
            for j in range(section.childCount()):
                child = section.child(j)
                child_name = child.text(0)
                items[section_name].append(child_name)
        return items


if __name__=='__main__':

    dataframes = {}

    pokemon = pd.read_csv('sample_data/pokemon.csv')
    dataframes['pokemon'] = {}
    dataframes['pokemon']['dataframe'] = pokemon

    sample = pd.read_csv('sample_data/sample.csv')
    dataframes['sample'] = {}
    dataframes['sample']['dataframe'] = sample

    import sys
    app = QtWidgets.QApplication(sys.argv)
    win = scatterDialog(dataframes)
    app.exec_()
