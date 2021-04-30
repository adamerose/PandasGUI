import inspect
import sys
from typing import NewType, Union, List, Callable, Iterable
from dataclasses import dataclass

from PyQt5.QtWidgets import QStyleOptionViewItem

import pandasgui
import os
import plotly.express as px
import plotly

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

import pandas as pd
from pandasgui.store import PandasGuiStore, PandasGuiDataFrameStore, HistoryItem, SETTINGS_STORE
from pandasgui.widgets.collapsible_panel import CollapsiblePanel

from pandasgui.utility import flatten_df, flatten_iter, kwargs_string, nunique, unique
from pandasgui.widgets.func_ui import FuncUi, ColumnArg, Schema, BooleanArg

import logging

logger = logging.getLogger(__name__)


class TypePicker(QtWidgets.QListWidget):
    def __init__(self, orientation=Qt.Horizontal):
        super().__init__()
        self.orientation = orientation
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setWordWrap(False)
        self.setSpacing(0)
        self.setWrapping(False)
        self.setUniformItemSizes(True)
        if self.orientation == Qt.Vertical:
            self.setFlow(QtWidgets.QListView.TopToBottom)
            self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        else:
            self.setFlow(QtWidgets.QListView.LeftToRight)
            self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.setIconSize(QtCore.QSize(50, 50))

    def viewOptions(self) -> 'QStyleOptionViewItem':
        options = super().viewOptions()
        options.decorationPosition = QStyleOptionViewItem.Top
        options.displayAlignment = Qt.AlignCenter
        return options

    def sizeHint(self):
        if self.orientation == Qt.Vertical:
            width = self.sizeHintForColumn(0) + 5
            if not self.verticalScrollBar().visibleRegion().isEmpty():
                width += self.verticalScrollBar().sizeHint().width()
            height = super().sizeHint().height()

            return QtCore.QSize(width, height)
        else:
            height = self.sizeHintForRow(0) + 5
            if not self.horizontalScrollBar().visibleRegion().isEmpty():
                height += self.horizontalScrollBar().sizeHint().height()
            width = super().sizeHint().width()

            return QtCore.QSize(width, height)

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        if self.orientation == Qt.Vertical:
            self.setFixedWidth(self.sizeHint().width())
        else:
            self.setFixedHeight(self.sizeHint().height())
        super().resizeEvent(e)


class Reshaper(QtWidgets.QWidget):
    def __init__(self, pgdf: PandasGuiDataFrameStore):
        super().__init__()

        self.pgdf = PandasGuiDataFrameStore.cast(pgdf)

        self.setWindowTitle("Graph Builder")

        # Dropdown to select plot type
        self.type_picker = TypePicker()

        self.error_console = QtWidgets.QTextEdit()
        self.error_console.setReadOnly(True)
        self.error_console_wrapper = CollapsiblePanel("Reshaper Console")
        self.error_console_wrapper.setContent(self.error_console)
        self.error_console_wrapper.setChecked(False)

        for schema in schemas:
            icon = QtGui.QIcon(schema.icon_path)
            text = schema.label
            item = QtWidgets.QListWidgetItem(icon, text)
            self.type_picker.addItem(item)

        df = flatten_df(self.pgdf.df)

        self.func_ui = FuncUi(df=df, schema=Schema())

        # Layouts
        self.plot_splitter = QtWidgets.QSplitter(Qt.Horizontal)
        self.plot_splitter.setHandleWidth(3)

        self.plot_splitter.addWidget(self.func_ui)

        self.plot_splitter.setStretchFactor(1, 1)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.type_picker)
        self.layout.addWidget(self.plot_splitter)
        self.layout.addWidget(self.error_console_wrapper)
        self.setLayout(self.layout)

        # Size policies
        self.func_ui.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.plot_splitter.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.error_console.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)

        # Initial selection
        self.type_picker.setCurrentRow(0)
        self.on_type_changed()

        # Signals
        self.type_picker.itemSelectionChanged.connect(self.on_type_changed)
        self.func_ui.finished.connect(self.on_dragger_finished)
        self.func_ui.saving.connect(self.on_dragger_saving)

    def on_type_changed(self):
        if len(self.type_picker.selectedItems()) == 0:
            return

        self.selected_plot_label = self.type_picker.selectedItems()[0].text()
        self.current_schema = next(filter(lambda schema: schema.label == self.selected_plot_label, schemas))
        arg_list = [arg.arg_name for arg in self.current_schema.args]

        self.func_ui.set_schema(self.current_schema)

    def on_dragger_saving(self):
        options = QtWidgets.QFileDialog.Options()
        # using native widgets so it matches the PNG download button

        filename, _ = QtWidgets.QFileDialog().getSaveFileName(self, "Save plot to", "", "HTML Files (*.html)",
                                                              options=options)
        if filename:
            if filename[-5:] != ".html":
                filename += ".html"
            self.fig.write_html(filename)
            self.pgdf.add_history_item("Reshaper",
                                       f"fig.write_html('{filename})'")

    def on_dragger_finished(self):
        kwargs = self.func_ui.get_data()
        func = self.current_schema.function

        try:
            self.result = func(data_frame=self.pgdf.df, **kwargs)
            from pandasgui import show
            self.pgdf.store.add_dataframe(self.result)

            self.error_console.setText("")
            self.error_console_wrapper.setTitle("Reshaper Console")
        except Exception as e:
            import traceback
            self.error_console.setText(traceback.format_exc())
            self.error_console_wrapper.setTitle("*** Reshaper Console ***")

    def set_state(self, plot_type, dct):
        self.type_picker.setCurrentIndex(self.type_picker.model().index(
            [schema.name for schema in schemas].index(plot_type), 0
        ))
        self.on_type_changed()
        print(self.current_schema)
        self.func_ui.set_data(dct)


def clear_layout(layout):
    for i in reversed(range(layout.count())):
        layout.itemAt(i).widget().setParent(None)


from pandasgui import jotly

schemas = [Schema(name="pivot",
                  label="Pivot",
                  function=jotly.pivot,
                  icon_path=os.path.join(pandasgui.__path__[0], "resources/images/draggers/pivot.svg"),
                  ),
           Schema(name="melt",
                  label="Melt",
                  function=jotly.melt,
                  icon_path=os.path.join(pandasgui.__path__[0], "resources/images/draggers/stack.svg"),
                  ), ]

if __name__ == "__main__":
    from pandasgui.utility import fix_ipython, fix_pyqt
    from pandasgui.datasets import iris, pokemon

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    gb = Reshaper(pokemon)
    gb.show()

    # gb.set_state('scatter', {'y': 'Attack', 'x': 'Defense'})

    app.exec_()
