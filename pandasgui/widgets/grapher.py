import inspect
import sys
from typing import NewType, Union, List, Callable, Iterable
from dataclasses import dataclass
import pandasgui
import os
import plotly.express as px
import plotly

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

import pandas as pd
from pandasgui.store import PandasGuiStore, PandasGuiDataFrameStore, HistoryItem, SETTINGS_STORE
from pandasgui.widgets.collapsible_panel import CollapsiblePanel

from pandasgui.widgets.figure_viewer import FigureViewer
from pandasgui.utility import flatten_df, flatten_iter, kwargs_string, nunique, unique, eval_title
from pandasgui.widgets.func_ui import FuncUi, ColumnArg, Schema, BooleanArg

import logging

logger = logging.getLogger(__name__)

import plotly.graph_objs as go
from plotly.validators.scatter.marker import SymbolValidator

# Available symbol names for a given version of Plotly
_extended_symbols = SymbolValidator().values[0::2][1::3]
plotly_markers = [symbol for symbol in _extended_symbols if symbol[-3:] != "dot"]


class Grapher(QtWidgets.QWidget):
    def __init__(self, pgdf: PandasGuiDataFrameStore):
        super().__init__()

        self.pgdf = PandasGuiDataFrameStore.cast(pgdf)

        self.setWindowTitle("Graph Builder")

        # Dropdown to select plot type
        self.type_picker = QtWidgets.QListWidget()
        self.type_picker.setViewMode(self.type_picker.IconMode)
        self.type_picker.setWordWrap(False)
        self.type_picker.setSpacing(20)
        self.type_picker.setResizeMode(self.type_picker.Adjust)
        self.type_picker.setDragDropMode(self.type_picker.NoDragDrop)
        self.type_picker.setStyleSheet("QListView::item {border: 2px solid transparent; padding: 3px;}"
                                       "QListView::item:selected {background: none; border: 2px solid #777;}")

        self.type_picker.sizeHint = lambda: QtCore.QSize(500, 250)

        self.error_console = QtWidgets.QTextEdit()
        self.error_console.setReadOnly(True)
        self.error_console_wrapper = CollapsiblePanel("Grapher Console")
        self.error_console_wrapper.setContent(self.error_console)
        self.error_console_wrapper.setChecked(False)

        for schema in schemas:
            icon = QtGui.QIcon(schema.icon_path)
            text = schema.label
            item = QtWidgets.QListWidgetItem(icon, text)
            self.type_picker.addItem(item)

        # UI setup
        self.figure_viewer = FigureViewer(store=self.pgdf.store)
        self.figure_viewer.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                         QtWidgets.QSizePolicy.Expanding)

        df = flatten_df(self.pgdf.df)

        self.dragger = FuncUi(df=df, schema=Schema())

        self.plot_splitter = QtWidgets.QSplitter(Qt.Horizontal)
        self.plot_splitter.setHandleWidth(3)
        self.left_panel = QtWidgets.QGridLayout()
        self.left_panel.addWidget(self.type_picker, 0, 0)
        self.left_panel.addWidget(self.dragger, 1, 0)

        # QGrid for first half of splitter
        self.selection_grid = QtWidgets.QWidget()
        self.selection_grid.setLayout(self.left_panel)
        self.plot_splitter.addWidget(self.selection_grid)

        # Figure Viewer for the second half of splitter
        self.figure_viewer.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.plot_splitter.addWidget(self.figure_viewer)
        self.plot_splitter.setStretchFactor(1, 1)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.plot_splitter)
        self.layout.addWidget(self.error_console_wrapper)
        self.setLayout(self.layout)


        self.dragger.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.plot_splitter.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.type_picker.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.error_console.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)


        # Initial selection
        self.type_picker.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.type_picker.setCurrentRow(0)
        self.on_type_changed()

        # Show a blank axis initially
        self.fig = plotly.graph_objs.Figure()
        self.figure_viewer.set_figure(self.fig)

        # Signals
        self.type_picker.itemSelectionChanged.connect(self.on_type_changed)
        self.dragger.finished.connect(self.on_dragger_finished)
        self.dragger.valuesChanges.connect(self.on_dragger_finished)
        self.dragger.saving.connect(self.on_dragger_saving)

    def on_type_changed(self):
        if len(self.type_picker.selectedItems()) == 0:
            return

        self.selected_plot_label = self.type_picker.selectedItems()[0].text()
        self.current_schema = next(filter(lambda schema: schema.label == self.selected_plot_label, schemas))
        arg_list = [arg.arg_name for arg in self.current_schema.args]

        self.dragger.set_schema(self.current_schema)

    def on_dragger_saving(self):
        options = QtWidgets.QFileDialog.Options()
        # using native widgets so it matches the PNG download button

        filename, _ = QtWidgets.QFileDialog().getSaveFileName(self, "Save plot to", "", "HTML Files (*.html)",
                                                              options=options)
        if filename:
            if filename[-5:] != ".html":
                filename += ".html"
            self.fig.write_html(filename)
            self.pgdf.add_history_item("Grapher",
                                       f"fig.write_html('{filename})'")

    def on_dragger_finished(self):
        # df = flatten_df(self.pgdf.df)
        kwargs = self.dragger.get_data()
        # Replace empty strings with None
        kwargs = {k: (None if v == '' else v) for k, v in kwargs.items()}

        # TODO: move this to jotly
        # render_mode = self.pgdf.settings.render_mode.value
        # if kwargs.get("render_mode", "") == "":
        #     if self.current_schema.name in ("line", "line_polar", "scatter", "scatter_polar"):
        #         kwargs["render_mode"] = render_mode

        # TODO: move this to jotly
        # # delayed evaluation of string to use kwargs
        # title_format = self.pgdf.settings.title_format.value
        # if title_format:
        #     # user might have provided a title
        #     title = kwargs.get("title", "")
        #     if "{title}" in title:
        #         # user is just adding to the default title
        #         kwargs["title"] = title.replace("{title}", title_format)
        #         kwargs["title"] = eval_title(self.pgdf, self.current_schema.name, kwargs)
        #     elif title == "":
        #         # nothing provided
        #         kwargs["title"] = title_format
        #         kwargs["title"] = eval_title(self.pgdf, self.current_schema.name, kwargs)

        print(kwargs)
        func = self.current_schema.function

        try:
            self.fig = func(data_frame=self.pgdf.df, **kwargs)
            self.figure_viewer.set_figure(self.fig)
            self.error_console.setText("")
            self.error_console_wrapper.setTitle("Grapher Console")
        except Exception as e:
            import traceback
            self.error_console.setText(traceback.format_exc())
            self.error_console_wrapper.setTitle("*** Grapher Console ***")



def clear_layout(layout):
    for i in reversed(range(layout.count())):
        layout.itemAt(i).widget().setParent(None)


from pandasgui import jotly

schemas = [Schema(name='histogram',
                  label='Histogram',
                  function=jotly.histogram,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-histogram.svg')),

           Schema(name='scatter',
                  label='Scatter',
                  function=jotly.scatter,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-scatter.svg')),
           Schema(name='line',
                  label='Line',
                  function=jotly.line,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-line.svg')),
           Schema(name='bar',
                  label='Bar',
                  function=jotly.bar,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-bar.svg')),
           Schema(name='box',
                  label='Box',
                  function=jotly.box,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-box.svg')),
           Schema(name='violin',
                  label='Violin',
                  function=jotly.violin,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-violin.svg')),
           Schema(name='scatter_3d',
                  label='Scatter 3D',
                  function=jotly.scatter_3d,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-scatter3d.svg')),
           Schema(name='density_heatmap',
                  label='Heatmap',
                  function=jotly.density_heatmap,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-heatmap.svg')),
           Schema(name='density_contour',
                  label='Contour',
                  function=jotly.density_contour,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-contour.svg')),
           Schema(name='pie',
                  label='Pie',
                  function=jotly.pie,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-pie.svg')),
           Schema(name='scatter_matrix',
                  label='Splom',
                  function=jotly.scatter_matrix,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/trace-type-splom.svg')),
           Schema(name='word_cloud',
                  label='Word Cloud',
                  function=jotly.word_cloud,
                  icon_path=os.path.join(pandasgui.__path__[0], 'resources/images/draggers/word-cloud.svg'))
           ]

if __name__ == "__main__":
    from pandasgui.utility import fix_ipython, fix_pyqt
    from pandasgui.datasets import iris, pokemon

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    gb2 = Grapher(pokemon)
    gb2.show()

    app.exec_()
