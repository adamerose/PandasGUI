import os
import re
import sys

from PyQt5 import QtCore, QtGui, QtWidgets, sip
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QModelIndex
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
from pandasgui.utility import nunique, unique

from pandasgui.constants import CATEGORICAL_THRESHOLD
from pandasgui.store import PandasGuiDataFrameStore
import typing
import pandasgui

import logging
logger = logging.getLogger(__name__)


class Completer(QtWidgets.QCompleter):

    def pathFromIndex(self, index):
        # This way it'll reevaluate
        path = QtWidgets.QCompleter.pathFromIndex(self, index)

        # if we use a space + double quote or backtick, whatever was before has already
        # been autocompleted, so we split on that.
        # space tells us we are at beginning of value
        text = self.widget().text()

        lst = re.split('([ ,][`"])', str(text))

        if len(lst) > 1:
            end_at = -1
            if lst[-2] in (' `', ' "'):  # dropping the delimiter from list since it is already in path
                end_at = -2
            path = '%s %s' % (''.join(lst[:end_at]), path)

        return path

    def splitPath(self, path):
        s_lst = re.split('([ ,][`"])', path)
        s_path = str(s_lst[-1])

        # on values, we split on [space]" or [space]` but need to prepend that in the return
        try:
            if s_lst[-2] in (' `', ' "') and s_path == "":
                s_path = s_lst[-2][-1]
        except IndexError:
            pass
        return [s_path]


class FilterViewer(QtWidgets.QWidget):
    def __init__(self, pgdf: PandasGuiDataFrameStore):
        super().__init__()
        pgdf = PandasGuiDataFrameStore.cast(pgdf)
        pgdf.filter_viewer = self
        self.pgdf = pgdf

        self.list_view = self.ListView()
        self.list_model = self.ListModel(pgdf)
        self.list_view.setModel(self.list_model)

        # autocompletion for QLineEdit
        columns = self.pgdf.df_unfiltered.columns
        valid_values = [f"`{col}`" for col in columns]
        categoricals = columns[self.pgdf.df_unfiltered.dtypes == "category"]
        low_cardinality = columns[nunique(self.pgdf.df_unfiltered) < CATEGORICAL_THRESHOLD]

        # make unique the column names
        all_categoricals = list(set(categoricals) | set(low_cardinality))

        for col in all_categoricals:
            if col in categoricals:
                in_dataset = [f'"{val}"' for val in self.pgdf.df_unfiltered[col].cat.categories]
            else:
                in_dataset = [f'"{val}"' for val in unique(self.pgdf.df_unfiltered[col])]
            valid_values.extend(in_dataset)

        self.completer = Completer(valid_values)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)

        self.text_input = QtWidgets.QLineEdit()
        self.text_input.setCompleter(self.completer)
        self.text_input.setPlaceholderText("Enter query expression (backtick ` for available columns)")
        self.text_input_label = QtWidgets.QLabel('''<a style="color: #1e81cc;" href="https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.query.html">What's a query expression?</a>''')
        self.text_input_label.linkActivated.connect(lambda link: QDesktopServices.openUrl(QUrl(link)))
        self.text_input.setValidator(None)

        self.submit_button = QtWidgets.QPushButton("Add Filter")
        self.autocomplete_check = QtWidgets.QCheckBox("Autocomplete")
        self.autocomplete_check.setChecked(True)

        # Signals
        self.text_input.returnPressed.connect(self.add_filter)
        self.submit_button.clicked.connect(self.add_filter)
        self.autocomplete_check.clicked.connect(self.autocomplete)

        # Layout
        self.new_filter_layout = QtWidgets.QHBoxLayout()
        self.new_filter_layout.addWidget(self.text_input)
        self.new_filter_layout.addWidget(self.submit_button)
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.new_filter_layout)
        self.layout.addWidget(self.text_input_label)
        self.layout.addWidget(self.autocomplete_check)
        self.layout.addWidget(self.list_view)
        self.setLayout(self.layout)

    def minimumSizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(280, 100)

    def autocomplete(self):
        if self.autocomplete_check.isChecked():
            self.text_input.setCompleter(self.completer)
        else:
            self.text_input.setCompleter(None)

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
                elided_text = fm.elidedText("No filters defined", QtCore.Qt.ElideRight, self.viewport().width())
                painter.drawText(self.viewport().rect(), QtCore.Qt.AlignCenter, elided_text)
                painter.restore()

    class ListModel(QtCore.QAbstractListModel):
        def __init__(self, pgdf: PandasGuiDataFrameStore):
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
                path = os.path.join(pandasgui.__path__[0], "resources/images/alert.svg")
                return QtGui.QIcon(path)

        def rowCount(self, parent=None):
            return len(self.pgdf.filters)

        def flags(self, index):
            return (QtCore.Qt.ItemIsEditable |
                    QtCore.Qt.ItemIsEnabled |
                    QtCore.Qt.ItemIsSelectable |
                    QtCore.Qt.ItemIsUserCheckable)

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
    pokemon = PandasGuiDataFrameStore(pokemon)
    pokemon.add_filter('Generation > 3', enabled=False)
    pokemon.add_filter('Attack > 50', enabled=True)
    pokemon.add_filter('Defense < 30', enabled=True)
    fv = FilterViewer(pokemon)
    stacked_widget.addWidget(fv)
    stacked_widget.show()
    app.exec_()
