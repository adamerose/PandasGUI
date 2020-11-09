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
from pandasgui.widgets.dragger import Dragger, Schema, ColumnArg, OptionListArg

import logging
logger = logging.getLogger(__name__)

class Reshaper(QtWidgets.QWidget):
    def __init__(self, pgdf: PandasGuiDataFrame):
        super().__init__()

        self.pgdf = PandasGuiDataFrame.cast(pgdf)

        self.setWindowTitle("Reshaper")

        # Dropdown to select reshape type
        self.reshape_type_picker = QtWidgets.QListWidget()
        self.reshape_type_picker.setViewMode(self.reshape_type_picker.IconMode)
        self.reshape_type_picker.setWordWrap(True)
        self.reshape_type_picker.setSpacing(20)
        self.reshape_type_picker.setResizeMode(self.reshape_type_picker.Adjust)
        self.reshape_type_picker.setDragDropMode(self.reshape_type_picker.NoDragDrop)

        for schema in schemas:
            icon = QtGui.QIcon(schema.icon_path)
            text = schema.label
            item = QtWidgets.QListWidgetItem(icon, text)
            self.reshape_type_picker.addItem(item)

        df = flatten_df(self.pgdf.dataframe)
        self.dragger = Dragger(sources=df.columns, destinations=[],
                               source_types=df.dtypes.values.astype(str))

        self.layout = QtWidgets.QGridLayout()
        self.layout.addWidget(self.reshape_type_picker, 0, 0)
        self.layout.addWidget(self.dragger, 1, 0)
        self.layout.setColumnStretch(0, 0)
        self.layout.setColumnStretch(1, 1)
        self.dragger.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.reshape_type_picker.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

        self.setLayout(self.layout)

        # Signals
        self.reshape_type_picker.itemSelectionChanged.connect(self.on_type_changed)
        self.dragger.finished.connect(self.on_dragger_finished)

        # Initial selection
        self.reshape_type_picker.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.reshape_type_picker.setCurrentRow(0)
        self.on_type_changed()

    def on_type_changed(self):
        if len(self.reshape_type_picker.selectedItems()) == 0:
            return

        self.selected_plot_label = self.reshape_type_picker.selectedItems()[0].text()
        self.current_schema = next(filter(lambda schema: schema.label == self.selected_plot_label, schemas))
        arg_list = [arg.arg_name for arg in self.current_schema.args]

        self.dragger.set_destinations(arg_list)

    def on_dragger_finished(self):
        self.selected_plot_label = self.reshape_type_picker.selectedItems()[0].text()
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

@track_history
def pivot(pgdf: PandasGuiDataFrame,
          index: Iterable = None,
          columns: Iterable = None,
          values: Iterable = None,
          aggfunc: Callable = 'mean'):
    df = pgdf.dataframe
    return df.pivot_table(index=index,
                          columns=columns,
                          values=values,
                          aggfunc=aggfunc)


@track_history
def melt(pgdf: PandasGuiDataFrame,
          id_vars: Iterable = None,
          value_vars: Iterable = None):
    df = pgdf.dataframe
    return df.melt(id_vars=id_vars,
                   value_vars=value_vars)


schemas = [
    Schema(name="pivot",
           label="Pivot",
           function=pivot,
           icon_path=os.path.join(pandasgui.__path__[0], "resources/images/pivot.png"),
           args=[
               ColumnArg(arg_name="index"),
               ColumnArg(arg_name="columns"),
               ColumnArg(arg_name="values"),
               OptionListArg(arg_name="aggfunc", values=['count', 'mean', 'median']),
           ]),
    Schema(name="melt",
           label="Melt",
           function=melt,
           icon_path=os.path.join(pandasgui.__path__[0], "resources/images/stack.png"),
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
