# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\_MyFiles\Programming\Python Projects\pandasgui\qtdesigner\scatter.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class scatterDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.show()

    def initUI(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.columnPicker = columnPicker()


class columnPicker(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.show()

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        # Make tree
        self.columnDestination = QtWidgets.QTreeWidget()
        self.columnDestination.setDragDropMode(QtWidgets.QTreeWidget.InternalMove)
        self.columnDestination.root
        # Add tree sections
        sections = ['X Variable', 'Y Variable', 'Color By']
        for name in sections:
            treeItem = QtWidgets.QTreeWidgetItem(self.columnDestination, [name])
            treeItem.setFlags(treeItem.flags() & ~QtCore.Qt.ItemIsDragEnabled)

        # Add items to layout
        layout.addWidget(self.columnDestination)

        # Select first section
        self.columnDestination.setCurrentItem(self.columnDestination.topLevelItem(0))

        # Add to items to selection section
        self.addTreeItem('test1')
        self.addTreeItem('test2')

    def addTreeItem(self, label):
        # Add to tree
        destinationSection = self.columnDestination.selectedItems()[0]
        treeItem = QtWidgets.QTreeWidgetItem(destinationSection, [label])
        destinationSection.setExpanded(True)
        treeItem.setFlags(treeItem.flags() & ~QtCore.Qt.ItemIsDropEnabled)

import sys
app = QtWidgets.QApplication(sys.argv)
win = columnPicker()
app.exec_()