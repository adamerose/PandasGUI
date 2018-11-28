from PyQt5 import QtCore, QtWidgets, QtGui
import pandas as pd
import sys
import pyqt_fix

'''

QtCore.QAbstractTableModel

Required methods:
    rowCount(self, index, role):
        Returns the number of rows under the given parent. When the parent is valid it means that 
        rowCount is returning the number of children of parent.
        
    columnCount(self, index, role):
        Returns the number of columns under the given parent. When the parent is valid it means that 
        rowCount is returning the number of children of parent.
    
    data(self, QModelIndex index, int role = Qt.DisplayRole):
        Returns the data stored under the given role for the item referred to by the index.
        
        Data() gets called for ever role
        
        
Recommended method:    
    headerData(self, int section, Qt.Orientation orientation, int role = Qt.DisplayRole)
        Returns the data for the given role and section in the header with the specified orientation.
        For horizontal headers, the section number corresponds to the column number. Similarly, for vertical headers, 
        the section number corresponds to the row number.
 
 
 Note - QtCore.QAbstractItemModel has more requirements
     When subclassing QAbstractItemModel, at the very least you must implement 
     index(), parent(), rowCount(), columnCount(), and data(). 
     These functions are used in all read-only models, and form the basis of editable models.


    
'''



class PaletteTableModel(QtCore.QAbstractTableModel):

    def __init__(self, colors=[[]], parent=None):
        super().__init__(parent)
        self.colors = colors

    def rowCount(self, parent):
        return len(self.colors)

    def columnCount(self, parent):
        return len(self.colors[0])

    def data(self, index, role):

        if (role == QtCore.Qt.DisplayRole) | (role == QtCore.Qt.EditRole) | (role == QtCore.Qt.ToolTipRole):
            row = index.row()
            column = index.column()

            color = self.colors[row][column]
            hexcode = color.name()
            return hexcode

        if role == QtCore.Qt.DecorationRole:
            row = index.row()
            column = index.column()

            color = self.colors[row][column]

            pixmap = QtGui.QPixmap(26, 26)
            pixmap.fill(color)

            icon = QtGui.QIcon(pixmap)

            return icon

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return "Column {}".format(section)
            else:
                return "Row {}".format(section)

    def flags(self, index):
        ''' Set flag to allow items editable (and enabled / selectable but those are on by default'''
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def setData(self, index, value, role = QtCore.Qt.EditRole):
        ''' When an item is edited check if it is valid, if it is, return True and emit dataChanged'''
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()

            color = QtGui.QColor(value)

            if color.isValid():
                self.colors[row][column] = color
                self.dataChanged.emit(index,index)
                return True
            else:
                return False
    #
    # def insertRows(self, position, rows, parent=QtCore.QModelIndex()):
    #     self.beginInsertRows(QtCore.QModelIndex(), position, position+rows-1)
    #
    #     for i in range(rows):
    #
    #         defaultValues = [QtGui.QColor('#000000') for i in range(self.columnCount(None))]
    #         self.colors.insert(position, defaultValues)
    #
    #     self.endInsertRows()
    #     return True
    #
    # def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
    #     self.beginRemoveRows(QtCore.QModelIndex(), position, position+rows-1)
    #
    #     for i in range(rows):
    #         self.colors.pop(position)
    #
    #     self.endRemoveRows()


class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        layout = QtWidgets.QVBoxLayout()

        rows=4
        columns=3
        # Create a PaletteListModel and show it in 3 views
        tableData1 = [ [QtGui.QColor('#FFFF00') for i in range(columns)] for j in range(rows)]

        model = PaletteTableModel(tableData1)

        listView = QtWidgets.QListView()
        listView.setModel(model)

        tableView = QtWidgets.QTableView()
        tableView.setModel(model)

        treeView = QtWidgets.QTreeView()
        treeView.setModel(model)

        columnView = QtWidgets.QColumnView()
        columnView.setModel(model)

        comboBox = QtWidgets.QComboBox()
        comboBox.setModel(model)

        # Add widgets to main window and show it
        for item in [listView, treeView, tableView, columnView, comboBox]:
            layout.addWidget(item)
        self.setLayout(layout)
        self.show()

        model.insertRows(2, 5)
        model.removeRows(2, 3)


if __name__ == '__main__':
    print(QtWidgets.QStyleFactory.keys())
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Windows")

    window = Window()
    sys.exit(app.exec_())
