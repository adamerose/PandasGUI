from PyQt5 import QtCore, QtWidgets
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from pandasgui.functions import flatten_multiindex
import sys

class baseDialog(QtWidgets.QDialog):
    def __init__(self, dataframes, parent=None):
        super().__init__(parent)

        self.dataframes = dataframes

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # Create DataFrame picker dropdown
        self.dataframePicker = QtWidgets.QComboBox()
        for df_name in dataframes.keys():
            self.dataframePicker.addItem(df_name)
        self.dataframePicker.currentIndexChanged.connect(self.initColumnPicker)

        # Build column picker
        self.columnPicker = columnPicker([])
        self.initColumnPicker()

        # Add button
        btnFinish = QtWidgets.QPushButton("Plot")
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

    def initColumnPicker(self):
        selected_dataframe = self.dataframePicker.itemText(self.dataframePicker.currentIndex())

        self.dataframe = self.dataframes[selected_dataframe]['dataframe'].copy()
        self.dataframe.columns = flatten_multiindex(self.dataframe.columns)
        column_names = self.dataframe.columns

        self.columnPicker.resetValues(column_names)


    def finish(self):
        dict = self.columnPicker.getDestinationItems()
        x = dict['X Variable'][0]
        y = dict['Y Variable'][0]
        try:
            c = dict['Color By'][0]
        except IndexError:
            c = None

        print(x,y,c)

        df = pd.read_csv('sample_data/pokemon.csv')
        sns.scatterplot(x,y,c,data=df)
        plt.show()

class pivotDialog(baseDialog):
    def __init__(self):
        pass


class columnPicker(QtWidgets.QWidget):
    def __init__(self, column_names, categories=None):
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

        # List settings
        self.columnSource.setDragDropMode(QtWidgets.QListWidget.DragDrop)
        # Add column names
        for name in column_names:
            self.columnSource.addItem(name)

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

        # Select first section
        self.columnDestination.setCurrentItem(self.columnDestination.topLevelItem(0))

    def resetValues(self, column_names):

        # Clear list
        self.columnSource.clear()

        # Add column names
        for name in column_names:
            self.columnSource.addItem(name)

        # Clear tree
        for i in range(self.columnDestination.topLevelItemCount()):
            section = self.columnDestination.topLevelItem(i)
            for j in reversed(range(section.childCount())):
                section.removeChild(section.child(j))

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

    ## PyQt
    app = QtWidgets.QApplication(sys.argv)

    # win = baseDialog(dataframes)
    win = columnPicker(list(pokemon.columns))

    win.show()
    app.exec_()
