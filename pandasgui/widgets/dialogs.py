import sys

import plotly.express as px
from PyQt5 import QtCore, QtGui, QtWidgets
import pandas as pd
import pandasgui
import os
from typing import Union, List, Iterable, Callable

from pandasgui.store import Store, PandasGuiDataFrame, track_history

from pandasgui.utility import flatten_df
from pandasgui.widgets.spinner import Spinner
from pandasgui.widgets.func_ui import FuncUi, Schema, ColumnArg, OptionListArg

import logging
logger = logging.getLogger(__name__)

class InputDialog(QtWidgets.QDialog):
    """
    Example usage:
    dialog = InputDialog("Add Column", {"Column Title": str, "Column Formula": str})
    column_title, column_formula = dialog
    """
    def __init__(self, title, schema, parent=None):
        super().__init__(parent)

        layout = QtWidgets.QFormLayout(self)

        self.fields = []
        for field_name, field_type in schema.items():
            if field_type == str:
                widget = QtWidgets.QLineEdit(self)
            if field_type == bool:
                pass  # TODO
            self.fields.append(widget)
            layout.addRow(field_name, self.first)


        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self);

        layout.addRow("Second text", self.second)
        layout.addWidget(buttonBox)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return (self.first.text(), self.second.text())

if __name__ == '__main__':

    import sys
    app = QtWidgets.QApplication(sys.argv)
    dialog = InputDialog()
    if dialog.exec():
        print(dialog.getInputs())
    exit(0)
