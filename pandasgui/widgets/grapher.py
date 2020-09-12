import sys
from typing import NewType, Union, List, Callable, Iterable
from dataclasses import dataclass
import pandasgui
import os
import plotly.express as px

from PyQt5 import QtCore, QtGui, QtWidgets
import pandas as pd
from pandasgui.store import Store, PandasGuiDataFrame

from pandasgui.utility import flatten_df, get_logger
from pandasgui.widgets.plotly_viewer import PlotlyViewer
from pandasgui.widgets.spinner import Spinner
from pandasgui.widgets.dragger import Dragger, ColumnArg, Schema

logger = get_logger(__name__)


class Grapher(QtWidgets.QWidget):
    def __init__(self, pgdf: PandasGuiDataFrame):
        super().__init__()

        self.pgdf = PandasGuiDataFrame.cast(pgdf)

        self.setWindowTitle("Graph Builder")
        self.workers = []
        self.current_worker = None

        # Dropdown to select plot type
        self.plot_type_picker = QtWidgets.QListWidget()

        for schema in schemas:
            icon = QtGui.QIcon(schema.icon_path)
            text = schema.label
            item = QtWidgets.QListWidgetItem(icon, text)
            self.plot_type_picker.addItem(item)

        # UI setup
        self.figure_viewer = PlotlyViewer()
        self.figure_viewer.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                         QtWidgets.QSizePolicy.Expanding)

        df = flatten_df(self.pgdf.dataframe)
        self.dragger = Dragger(sources=df.columns, destinations=[],
                               source_types=df.dtypes.values.astype(str))

        self.spinner = Spinner()
        self.spinner.setParent(self.figure_viewer)

        self.layout = QtWidgets.QGridLayout()
        self.layout.addWidget(self.plot_type_picker, 0, 0)
        self.layout.addWidget(self.dragger, 1, 0)
        self.layout.addWidget(self.figure_viewer, 0, 1, 2, 1)
        self.layout.setColumnStretch(0, 0)
        self.layout.setColumnStretch(1, 1)

        self.setLayout(self.layout)

        # Signals
        self.plot_type_picker.itemSelectionChanged.connect(self.on_type_changed)
        self.dragger.finished.connect(self.on_dragger_finished)

        # Initial selection
        self.plot_type_picker.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.plot_type_picker.setCurrentRow(0)
        self.on_type_changed()

        # Show a blank axis initially
        self.figure_viewer.set_figure(px.scatter())

    # Update the dragger destinations according to the new schema when it is changed
    def on_type_changed(self):
        selected_plot_label = self.plot_type_picker.selectedItems()[0].text()
        current_schema = next(filter(lambda schema: schema.label == selected_plot_label, schemas))
        arg_list = [arg.arg_name for arg in current_schema.args]

        self.dragger.set_destinations(arg_list)

    def on_dragger_finished(self):
        self.spinner.start()
        selected_plot_label = self.plot_type_picker.selectedItems()[0].text()
        current_schema = next(filter(lambda x: x.label == selected_plot_label, schemas))

        df = flatten_df(self.pgdf.dataframe)
        kwargs = {"data_frame": df}
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
        self.current_worker = Worker(func, kwargs)
        self.current_worker.finished.connect(self.worker_callback)
        self.current_worker.finished.connect(self.current_worker.deleteLater)
        self.current_worker.start()
        self.workers.append(self.current_worker)

    @QtCore.pyqtSlot(object)
    def worker_callback(self, fig):
        self.figure_viewer.set_figure(fig)
        self.spinner.stop()


# https://stackoverflow.com/questions/9957195/updating-gui-elements-in-multithreaded-pyqt
class Worker(QtCore.QThread):
    finished = QtCore.pyqtSignal(object)

    def __init__(self, func, kwargs):
        d = {k: v for k, v in kwargs.items() if k != "data_frame"}
        logger.debug(f"Creating Worker. {func.__name__} {d}")
        QtCore.QThread.__init__(self)
        self.func = func
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(**self.kwargs)
            d = {k: v for k, v in self.kwargs.items() if k != "data_frame"}
            logger.debug(f"Finished Worker run. {self.func.__name__} {d}")
            self.finished.emit(result)
        except Exception as e:
            logger.error(e)
            self.finished.emit(None)


def clear_layout(layout):
    for i in reversed(range(layout.count())):
        layout.itemAt(i).widget().setParent(None)


# ========================================================================
# Schema


def line(**kwargs):
    key_cols = []
    for arg in [a for a in ['x', 'color', 'facet_row', 'facet_col'] if a in kwargs.keys()]:
        key_cols_subset = kwargs[arg]
        if type(key_cols_subset) == list:
            key_cols += key_cols_subset
        elif type(key_cols_subset) == str:
            key_cols += [key_cols_subset]
        else:
            raise TypeError

    df = kwargs['data_frame'].groupby(key_cols).mean().reset_index()
    kwargs['data_frame'] = df
    return px.line(**kwargs)


def bar(**kwargs):
    key_cols = []
    for arg in [a for a in ['x', 'color', 'facet_row', 'facet_col'] if a in kwargs.keys()]:
        key_cols_subset = kwargs[arg]
        if type(key_cols_subset) == list:
            key_cols += key_cols_subset
        elif type(key_cols_subset) == str:
            key_cols += [key_cols_subset]
        else:
            raise TypeError

    df = kwargs['data_frame'].groupby(key_cols).mean().reset_index()
    kwargs['data_frame'] = df
    return px.bar(**kwargs)


def scatter_matrix(**kwargs):
    fig = px.scatter_matrix(**kwargs)
    fig.update_traces(diagonal_visible=False)
    return fig


def contour(**kwargs):
    fig = px.density_contour(**kwargs)
    fig.update_traces(contours_coloring="fill", contours_showlabels=True)
    return fig


schemas = [Schema(name='histogram',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='color'),
                        ColumnArg(arg_name='facet_row'),
                        ColumnArg(arg_name='facet_col')],
                  label='Histogram',
                  function=px.histogram,
                  icon_path=os.path.join(pandasgui.__path__[0], 'images/plotly/trace-type-histogram.svg')),
           Schema(name='scatter',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='y'),
                        ColumnArg(arg_name='color'),
                        ColumnArg(arg_name='facet_row'),
                        ColumnArg(arg_name='facet_col')],
                  label='Scatter',
                  function=px.scatter,
                  icon_path=os.path.join(pandasgui.__path__[0], 'images/plotly/trace-type-scatter.svg')),
           Schema(name='line',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='y'),
                        ColumnArg(arg_name='color'),
                        ColumnArg(arg_name='facet_row'),
                        ColumnArg(arg_name='facet_col')],
                  label='Line',
                  function=line,
                  icon_path=os.path.join(pandasgui.__path__[0], 'images/plotly/trace-type-line.svg')),
           Schema(name='bar',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='y'),
                        ColumnArg(arg_name='color'),
                        ColumnArg(arg_name='facet_row'),
                        ColumnArg(arg_name='facet_col')],
                  label='Bar',
                  function=bar,
                  icon_path=os.path.join(pandasgui.__path__[0], 'images/plotly/trace-type-bar.svg')),
           Schema(name='box',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='y'),
                        ColumnArg(arg_name='color'),
                        ColumnArg(arg_name='facet_row'),
                        ColumnArg(arg_name='facet_col')],
                  label='Box',
                  function=px.box,
                  icon_path=os.path.join(pandasgui.__path__[0], 'images/plotly/trace-type-box.svg')),
           Schema(name='violin',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='y'),
                        ColumnArg(arg_name='color'),
                        ColumnArg(arg_name='facet_row'),
                        ColumnArg(arg_name='facet_col')],
                  label='Violin',
                  function=px.violin,
                  icon_path=os.path.join(pandasgui.__path__[0], 'images/plotly/trace-type-violin.svg')),
           Schema(name='scatter_3d',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='y'),
                        ColumnArg(arg_name='z'),
                        ColumnArg(arg_name='color')],
                  label='Scatter 3D',
                  function=px.scatter_3d,
                  icon_path=os.path.join(pandasgui.__path__[0], 'images/plotly/trace-type-scatter3d.svg')),
           Schema(name='density_heatmap',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='y'),
                        ColumnArg(arg_name='z'),
                        ColumnArg(arg_name='facet_row'),
                        ColumnArg(arg_name='facet_col')],
                  label='Heatmap',
                  function=px.density_heatmap,
                  icon_path=os.path.join(pandasgui.__path__[0], 'images/plotly/trace-type-heatmap.svg')),
           Schema(name='density_contour',
                  args=[ColumnArg(arg_name='x'),
                        ColumnArg(arg_name='y'),
                        ColumnArg(arg_name='z'),
                        ColumnArg(arg_name='facet_row'),
                        ColumnArg(arg_name='facet_col')],
                  label='Contour',
                  function=contour,
                  icon_path=os.path.join(pandasgui.__path__[0], 'images/plotly/trace-type-contour.svg')),
           Schema(name='pie',
                  args=[ColumnArg(arg_name='names'),
                        ColumnArg(arg_name='values')],
                  label='Pie',
                  function=px.pie,
                  icon_path=os.path.join(pandasgui.__path__[0], 'images/plotly/trace-type-pie.svg')),
           Schema(name='scatter_matrix',
                  args=[ColumnArg(arg_name='dimensions'),
                        ColumnArg(arg_name='color')],
                  label='Scatter Matrix',
                  function=scatter_matrix,
                  icon_path=os.path.join(pandasgui.__path__[0], 'images/plotly/trace-type-splom.svg'))
           ]

if __name__ == "__main__":
    from pandasgui.utility import fix_ipython, fix_pyqt
    from pandasgui.datasets import iris, pokemon

    fix_ipython()
    fix_pyqt()
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    gb2 = Grapher(pokemon)
    gb2.show()

    app.exec_()
