import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from pandasgui.store import PandasGuiDataFrameStore, SETTINGS_STORE
import pandasgui

import logging

from pandasgui.utility import resize_widget
from pandasgui.widgets.python_highlighter import PythonHighlighter

logger = logging.getLogger(__name__)


class CodeHistoryViewer(QtWidgets.QFrame):
    def __init__(self, pgdf: PandasGuiDataFrameStore):
        super().__init__()
        pgdf = PandasGuiDataFrameStore.cast(pgdf)
        pgdf.filter_viewer = self
        self.pgdf = pgdf

        resize_widget(self, 0.5, 0.5)

        self.textbox = QtWidgets.QPlainTextEdit()
        self.textbox.setReadOnly(True)
        self.textbox.setLineWrapMode(self.textbox.NoWrap)
        self.highlighter = PythonHighlighter(self.textbox.document(),
                                             dark=SETTINGS_STORE.theme.value == 'dark')

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.textbox)
        self.setLayout(self.layout)

        self.setWindowTitle(f"Code Export ({self.pgdf.name})")

        self.refresh()

    def refresh(self):
        code_history = self.pgdf.code_export()
        self.textbox.setPlainText(code_history)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.hide()


if __name__ == "__main__":
    # Create a QtWidgets.QApplication instance or use the existing one if it exists
    app = QtWidgets.QApplication(sys.argv)
    from pandasgui.datasets import pokemon

    pokemon = PandasGuiDataFrameStore.cast(pokemon)
    pokemon.parse_all_dates()
    pokemon.sort_column(0)
    fv = CodeHistoryViewer(pokemon)
    fv.show()
    app.exec_()
