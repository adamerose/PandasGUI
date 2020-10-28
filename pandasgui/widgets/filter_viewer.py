import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets, sip
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QModelIndex
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl

from pandasgui.utility import get_logger
from pandasgui.store import PandasGuiDataFrame
import typing
import pandasgui

logger = get_logger(__name__)


class FilterViewer(QtWidgets.QWidget):
    def __init__(self, pgdf: PandasGuiDataFrame):
        super().__init__()
        pgdf = PandasGuiDataFrame.cast(pgdf)
        pgdf.filter_viewer = self
        self.pgdf = pgdf

        self.list_view = self.ListView()
        self.list_model = self.ListModel(pgdf)
        self.list_view.setModel(self.list_model)

        self.text_input = QtWidgets.QLineEdit()
        self.text_input.setPlaceholderText("Enter query expression")
        self.text_input_label = QtWidgets.QLabel(
            """<a href="https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.query.html">What's a query expression?</a>"""
        )
        self.text_input_label.linkActivated.connect(
            lambda link: QDesktopServices.openUrl(QUrl(link))
        )
        self.text_input.setValidator(None)

        self.submit_button = QtWidgets.QPushButton("Add Filter")

        # Signals
        self.text_input.returnPressed.connect(self.add_filter)
        self.submit_button.clicked.connect(self.add_filter)

        # Layout
        self.new_filter_layout = QtWidgets.QHBoxLayout()
        self.new_filter_layout.addWidget(self.text_input)
        self.new_filter_layout.addWidget(self.submit_button)
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.new_filter_layout)
        self.layout.addWidget(self.text_input_label)
        self.layout.addWidget(self.list_view)
        self.setLayout(self.layout)

    def minimumSizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(280, 100)

    def add_filter(self):
        expr = self.text_input.text()
        if not expr == "":
            self.text_input.setText("")
            self.pgdf.add_filter(expr=expr)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            for row in [x.row() for x in self.list_view.selectedIndexes()]:
                self.pgdf.remove_filter(row)

    class ListView(QtWidgets.QListView):
        def paintEvent(self, event):
            super().paintEvent(event)
            if self.model().rowCount() == 0:
                painter = QtGui.QPainter(self.viewport())
                painter.save()
                col = self.palette().placeholderText().color()
                painter.setPen(col)
                fm = self.fontMetrics()
                elided_text = fm.elidedText(
                    "No filters defined", QtCore.Qt.ElideRight, self.viewport().width()
                )
                painter.drawText(
                    self.viewport().rect(), QtCore.Qt.AlignCenter, elided_text
                )
                painter.restore()

    class ListModel(QtCore.QAbstractListModel):
        def __init__(self, pgdf: PandasGuiDataFrame):
            super().__init__()
            self.pgdf = pgdf

        def data(self, index: QtCore.QModelIndex, role: int):
            row = index.row()
            if role == Qt.DisplayRole or role == Qt.EditRole:
                filt = self.pgdf.filters[row]
                return filt.expr

            if role == Qt.CheckStateRole:
                if self.pgdf.filters[index.row()].failed:
                    return None

                filt = self.pgdf.filters[row]
                if filt.enabled:
                    return Qt.Checked
                else:
                    return Qt.Unchecked

            if role == QtCore.Qt.DecorationRole and self.pgdf.filters[row].failed:
                path = os.path.join(pandasgui.__path__[0], "images/alert.svg")
                return QtGui.QIcon(path)

        def rowCount(self, parent=None):
            return len(self.pgdf.filters)

        def flags(self, index):
            return (
                QtCore.Qt.ItemIsEditable
                | QtCore.Qt.ItemIsEnabled
                | QtCore.Qt.ItemIsSelectable
                | QtCore.Qt.ItemIsUserCheckable
            )

        def setData(self, index, value, role=QtCore.Qt.DisplayRole):
            row = index.row()
            if role == Qt.CheckStateRole:
                self.pgdf.toggle_filter(row)
                return True

            if role == QtCore.Qt.EditRole:
                self.pgdf.edit_filter(row, value)
                return True

            return False


if __name__ == "__main__":
    # Create a QtWidgets.QApplication instance or use the existing one if it exists
    app = QtWidgets.QApplication(sys.argv)
    from pandasgui.datasets import pokemon

    stacked_widget = QtWidgets.QStackedWidget()
    pokemon = PandasGuiDataFrame(pokemon)
    pokemon.add_filter("Generation > 3", enabled=False)
    pokemon.add_filter("Attack > 50", enabled=True)
    pokemon.add_filter("Defense < 30", enabled=True)
    fv = FilterViewer(pokemon)
    stacked_widget.addWidget(fv)
    stacked_widget.show()
    app.exec_()
