import sys

import plotly.express as px
from PyQt5 import QtCore, QtGui, QtWidgets
import pandas as pd
import pandasgui
import os
from typing import Union, List, Iterable, Callable

from pandasgui.store import Store, PandasGuiDataFrame, track_history

from pandasgui.utility import flatten_df, get_logger
from pandasgui.widgets.spinner import Spinner
from pandasgui.widgets.dragger import Dragger, Schema, ColumnArg, OptionListArg

logger = get_logger(__name__)


class Reshaper(QtWidgets.QWidget):
    def __init__(self, pgdf: PandasGuiDataFrame):
        super().__init__()

        self.pgdf = PandasGuiDataFrame.cast(pgdf)

        self.setWindowTitle("Reshaper")

        self.reshape_type_picker = QtWidgets.QListWidget()
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

        self.setLayout(self.layout)

        # Signals
        self.reshape_type_picker.itemSelectionChanged.connect(self.on_type_changed)
        self.dragger.finished.connect(self.on_dragger_finished)

        # Initial selection
        self.reshape_type_picker.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.reshape_type_picker.setCurrentRow(0)
        self.on_type_changed()

    # Update the dragger destinations according to the new schema when it is changed
    def on_type_changed(self):
        selected_plot_label = self.reshape_type_picker.selectedItems()[0].text()
        current_schema = next(filter(lambda schema: schema.label == selected_plot_label, schemas))
        arg_list = [arg.arg_name for arg in current_schema.args]

        self.dragger.set_destinations(arg_list)

    def on_dragger_finished(self):
        selected_plot_label = self.reshape_type_picker.selectedItems()[0].text()
        current_schema = next(filter(lambda x: x.label == selected_plot_label, schemas))

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
        func = current_schema.function
        try:
            new_df = func(**kwargs)
            new_df_name = self.pgdf.name + "_" + current_schema.name
            self.pgdf.store.add_dataframe(new_df, new_df_name)
        except Exception as e:
            logger.exception(e)


# ========================================================================
# Schema

@track_history
def pivot(pgdf: PandasGuiDataFrame,
          keys: Iterable = None,
          categories: Iterable = None,
          values: Iterable = None,
          aggregation: Callable = 'mean'):
    df = pgdf.dataframe
    return df.pivot_table(index=keys,
                          columns=categories,
                          values=values,
                          aggfunc=aggregation)


@track_history
def stack(pgdf: PandasGuiDataFrame,
          stack: Iterable = None,
          keep: Iterable = None):
    df = pgdf.dataframe
    return df.melt(id_vars=keep,
                   value_vars=stack)


schemas = [
    Schema(name="pivot",
           label="Pivot",
           function=pivot,
           icon_path=os.path.join(pandasgui.__path__[0], "images/pivot.png"),
           args=[
               ColumnArg(arg_name="keys"),
               ColumnArg(arg_name="categories"),
               ColumnArg(arg_name="values"),
               OptionListArg(arg_name="aggregation", values=['count', 'mean', 'median']),
           ]),
    Schema(name="stack",
           label="Stack",
           function=stack,
           icon_path=os.path.join(pandasgui.__path__[0], "images/stack.png"),
           args=[
               ColumnArg(arg_name="stack"),
               ColumnArg(arg_name="keep"),
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
