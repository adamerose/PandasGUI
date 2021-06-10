from PyQt5 import QtGui, QtWidgets


class QTreeWidget(QtWidgets.QTreeWidget):
    # Autosize columns
    def showEvent(self, event: QtGui.QShowEvent):
        self.autosize_columns()
        event.accept()

    def autosize_columns(self):
        for i in range(self.columnCount()):
            self.resizeColumnToContents(i)



class QTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __lt__(self, otherItem):
        column = self.treeWidget().sortColumn()

        try:
            return float(self.text(column)) < float(otherItem.text(column))
        except ValueError:
            return self.text(column) < otherItem.text(column)
