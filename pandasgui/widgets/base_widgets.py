from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt


class QTreeWidget(QtWidgets.QTreeWidget):
    # Autosize columns
    def showEvent(self, event: QtGui.QShowEvent):
        for i in range(self.columnCount()):
            self.resizeColumnToContents(i)
        event.accept()
