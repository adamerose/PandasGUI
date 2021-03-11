from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt


class QTreeWidget(QtWidgets.QTreeWidget):
    # Autosize columns
    def showEvent(self, event: QtGui.QShowEvent):
        for i in range(self.columnCount()):
            self.resizeColumnToContents(i)
        event.accept()


class QTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __lt__(self, otherItem):
        column = self.treeWidget().sortColumn()

        try:
            return float(self.text(column)) < float(otherItem.text(column))
        except ValueError:
            return self.text(column) < otherItem.text(column)
