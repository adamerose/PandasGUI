from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal


class QTreeWidget(QtWidgets.QTreeWidget):
    onDropSignal = pyqtSignal()

    # Autosize columns
    def showEvent(self, event: QtGui.QShowEvent):
        self.autosize_columns()
        event.accept()

    def autosize_columns(self):
        for i in range(self.columnCount()):
            self.resizeColumnToContents(i)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        super().dropEvent(event)
        self.onDropSignal.emit()

class QTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __lt__(self, otherItem):
        column = self.treeWidget().sortColumn()

        try:
            return float(self.text(column)) < float(otherItem.text(column))
        except ValueError:
            return self.text(column) < otherItem.text(column)
