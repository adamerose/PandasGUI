from PyQt5 import QtCore, QtWidgets, QtGui
import pandas as pd
import sys

# This fixes lack of stack trace on PyQt exceptions
import pyqt_fix


class DataFrameModel(QtCore.QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), parent=None):
        super().__init__(parent=parent)
        self.df = df

    def __str__(self):
        return str(self.df)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.df.columns.tolist()[section]
            elif orientation == QtCore.Qt.Vertical:
                return self.df.index.tolist()[section]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if (role == QtCore.Qt.DisplayRole) | (role == QtCore.Qt.EditRole) | (role == QtCore.Qt.ToolTipRole):
            if index.isValid():
                return str(self.df.iloc[index.row(), index.column()])

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.df.index)

    def __len__(self):
        return self.rowCount()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.df.columns)

    def sort(self, column, order):
        colname = self.df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self.df.sort_values(colname, ascending=order == QtCore.Qt.AscendingOrder, inplace=True)
        self.df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()

    def flags(self, index):
        ''' Set flag to allow items editable
        (and enabled / selectable but those are on by default)'''
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        ''' When an item is edited check if it is valid,
            if it is, return True and emit dataChanged'''
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()

            self.df.iloc[row, column] = value
            self.dataChanged.emit(index, index)
            return True
