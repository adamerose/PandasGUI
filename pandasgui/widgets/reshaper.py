import sys

import plotly.express as px
from PyQt5 import QtCore, QtGui, QtWidgets
import pandas as pd
import pandasgui
import os
from typing import Union, List, Iterable, Callable

from pandasgui.store import PandasGuiStore, PandasGuiDataFrameStore

from pandasgui.utility import flatten_df, kwargs_string, nunique
from pandasgui.widgets.spinner import Spinner
from pandasgui.widgets.dragger import Dragger, Schema, ColumnArg, OptionListArg

import logging

logger = logging.getLogger(__name__)


class Reshaper(QtWidgets.QWidget):
    def __init__(self, pgdf: PandasGuiDataFrameStore):
        super().__init__()

        self.pgdf = PandasGuiDataFrameStore.cast(pgdf)

        self.setWindowTitle("Reshaper")

        # Dropdown to select reshape type
        self.type_picker = QtWidgets.QListWidget()
        self.type_picker.setViewMode(self.type_picker.IconMode)
        self.type_picker.setWordWrap(False)
        self.type_picker.setSpacing(20)
        self.type_picker.setResizeMode(self.type_picker.Adjust)
        self.type_picker.setDragDropMode(self.type_picker.NoDragDrop)
        self.type_picker.setStyleSheet("QListView::item {border: 2px solid transparent; padding: 3px;}"
                                               "QListView::item:selected {background: none; border: 2px solid #777;}")

        for schema in schemas:
            icon = QtGui.QIcon(schema.icon_path)
            text = schema.label
            item = QtWidgets.QListWidgetItem(icon, text)
            self.type_picker.addItem(item)

        df = flatten_df(self.pgdf.df)
        self.dragger = Dragger(sources=df.columns, schema=Schema(),
                               source_nunique=nunique(df).apply('{: >6}'.format).values,
                               source_types=df.dtypes.values.astype(str))

        # Layout
        self.layout = QtWidgets.QGridLayout()
        self.layout.addWidget(self.type_picker, 0, 0)
        self.layout.addWidget(self.dragger, 1, 0)
        self.layout.setColumnStretch(0, 0)
        self.layout.setColumnStretch(1, 1)
        self.dragger.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.type_picker.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

        self.setLayout(self.layout)

        # Signals
        self.type_picker.itemSelectionChanged.connect(self.on_type_changed)
        self.dragger.finished.connect(self.on_dragger_finished)

        # Initial selection
        self.type_picker.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.type_picker.setCurrentRow(0)
        self.on_type_changed()

    def on_type_changed(self):
        if len(self.type_picker.selectedItems()) == 0:
            return

        self.selected_plot_label = self.type_picker.selectedItems()[0].text()
        self.current_schema = next(filter(lambda schema: schema.label == self.selected_plot_label, schemas))
        arg_list = [arg.arg_name for arg in self.current_schema.args]

        self.dragger.set_schema(self.current_schema)

    def on_dragger_finished(self):
        self.selected_plot_label = self.type_picker.selectedItems()[0].text()
        self.current_schema = next(filter(lambda x: x.label == self.selected_plot_label, schemas))

        kwargs = {"pgdf": self.pgdf}
        for key, val in self.dragger.get_data().items():
            if type(val) == list and len(val) == 0:
                continue
            elif type(val) == list and len(val) == 1:
                kwargs[key] = val[0]
            elif type(val) == list and len(val) > 1:
                kwargs[key] = val
            else:
                kwargs[key] = val
        func = self.current_schema.function
        try:
            new_df = func(**kwargs)
            new_df_name = self.pgdf.name + "_" + self.current_schema.name
            self.pgdf.store.add_dataframe(new_df, new_df_name)
        except Exception as e:
            logger.exception(e)


# ========================================================================
# Schema

def pivot(pgdf, **kwargs):
    df = pgdf.df.pivot_table(**kwargs)
    pgdf.add_history_item("Reshaper",
                          f"df.pivot_table({kwargs_string(kwargs)})")
    return df


def melt(pgdf, **kwargs):
    df = pgdf.df.melt(**kwargs)
    pgdf.add_history_item("Reshaper",
                          f"df.melt({kwargs_string(kwargs)})")
    return df


schemas = [
    Schema(name="pivot",
           label="Pivot",
           function=pivot,
           icon_path=os.path.join(pandasgui.__path__[0], "resources/images/draggers/pivot.svg"),
           args=[
               ColumnArg(arg_name="index"),
               ColumnArg(arg_name="columns"),
               ColumnArg(arg_name="values"),
               OptionListArg(arg_name="aggfunc", values=['count', 'mean', 'median']),
           ]),
    Schema(name="melt",
           label="Melt",
           function=melt,
           icon_path=os.path.join(pandasgui.__path__[0], "resources/images/draggers/stack.svg"),
           args=[
               ColumnArg(arg_name="id_vars"),
               ColumnArg(arg_name="value_vars"),
           ]),
]

if __name__ == "__main__":
    from pandasgui.utility import fix_ipython, fix_pyqt
    from pandasgui.datasets import pokemon

    fix_ipython()
    fix_pyqt()
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    gb2 = Reshaper(pokemon)
    gb2.show()

    app.exec_()
