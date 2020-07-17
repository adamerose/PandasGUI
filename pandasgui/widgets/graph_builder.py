from threading import Thread
from pandasgui.widgets.plotly_viewer import PlotlyViewer
from pandasgui.utility import flatten_multiindex
from pandasgui.datasets import pokemon, iris
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QThread
import plotly.express as px
from PyQt5.QtWidgets import QApplication
import sys
from jsonschema import validate
import pandas as pd
from dataclasses import dataclass
from pandasgui.widgets import QtWaitingSpinner
import time
import logging

logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG, format='%(message)s')


class GraphBuilder(QtWidgets.QWidget):

    def __init__(self, df, name='a'):
        super().__init__()
        self.name = name
        df = df.copy()
        df.columns = flatten_multiindex(df.columns)

        self.df = df
        self.prev_kwargs = {}  # This is for carrying plot arg selections forward to new plottypes

        self.setWindowTitle("Graph Builder")
        self.schema_widgets = {}
        self.workers = []
        self.current_worker = None

        # Dropdown to select plot type
        self.plot_type_picker = QtWidgets.QComboBox()
        self.plot_type_picker.addItems(
            [x['name'] for x in schemas.values()])
        self.plot_type_picker.currentIndexChanged.connect(self.build_ui)

        # UI setup
        self.figure_viewer = PlotlyViewer()
        self.figure_viewer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.reset_button = QtWidgets.QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_selections)

        self.schema_layout = QtWidgets.QVBoxLayout()
        self.schema_layout_outer = QtWidgets.QVBoxLayout()
        self.schema_layout_outer.addWidget(self.plot_type_picker)
        self.schema_layout_outer.addLayout(self.schema_layout)
        self.schema_layout_outer.addWidget(self.reset_button)
        self.schema_layout_outer.addStretch()

        self.spinner = QtWaitingSpinner()
        self.spinner.setParent(self.figure_viewer)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.schema_layout_outer)
        self.layout.addWidget(self.figure_viewer)
        self.setLayout(self.layout)

        # Initial selection
        self.plot_type_picker.setCurrentIndex(0)
        self.build_ui()

    def build_ui(self):
        self.current_schema = next(x for x in schemas.values(
        ) if x["name"] == self.plot_type_picker.currentText())
        clear_layout(self.schema_layout)

        for key, val in self.current_schema.args.items():
            l = QtWidgets.QLabel(key)
            w = QtWidgets.QComboBox()
            self.schema_widgets[key] = w
            w.addItems([""] + list(self.df.columns))
            w.currentIndexChanged.connect(self.update_plot)
            self.schema_layout.addWidget(l)
            self.schema_layout.addWidget(w)

        self.update_plot()

    def update_plot(self):
        self.spinner.start()

        # Get dict of user selected values from widgets for current schema
        kwargs = {}
        for arg_name in self.current_schema.args.keys():
            arg_value = self.schema_widgets[arg_name].currentText()
            if arg_value:
                kwargs[arg_name] = arg_value

        logger.debug(self.name+'1 '+str(kwargs))
        logger.debug(self.name+str(self.current_schema))
        # On plot type change (all selections reset to blank) fill them with previous selections
        if not any(kwargs.values()):
            for arg_name in self.prev_kwargs.keys():
                if arg_name in self.current_schema.args.keys():
                    kwargs[arg_name] = self.prev_kwargs[arg_name]
                    widget = self.schema_widgets[arg_name]
                    widget.blockSignals(True)
                    widget.setCurrentText(kwargs[arg_name])
                    widget.blockSignals(False)

        self.prev_kwargs = kwargs

        logger.debug('2 '+str(kwargs))
        # Copy because sometimes df gets deleted somehow?
        kwargs['data_frame'] = self.df.copy()
        func = self.current_schema.function
        self.current_worker = Worker(func, kwargs)
        self.current_worker.finished.connect(self.worker_callback)
        self.current_worker.finished.connect(self.current_worker.deleteLater)
        self.current_worker.start()
        self.workers.append(self.current_worker)

    @QtCore.pyqtSlot(object)
    def worker_callback(self, fig):
        logger.debug(self.name+"worker_callback")
        self.figure_viewer.set_figure(fig)
        self.spinner.stop()

    def reset_selections(self):
        logger.debug(self.name+"reset_selections")
        for arg_name in self.current_schema.args.keys():
            widget = self.schema_widgets[arg_name]
            widget.blockSignals(True)
            widget.setCurrentIndex(0)
            widget.blockSignals(False)
            self.prev_kwargs = {}
        self.update_plot()


# https://stackoverflow.com/questions/9957195/updating-gui-elements-in-multithreaded-pyqt
class Worker(QtCore.QThread):
    finished = QtCore.pyqtSignal(object)

    def __init__(self, func, kwargs):
        d = {k: v for k, v in kwargs.items() if k != 'data_frame'}
        logger.debug(f"Creating Worker. {func.__name__} {d}")
        QtCore.QThread.__init__(self)
        self.func = func
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(**self.kwargs)
            d = {k: v for k, v in self.kwargs.items() if k != 'data_frame'}
            logger.debug(f"Finished Worker run. {self.func.__name__} {d}")
            self.finished.emit(result)
        except Exception as e:
            logger.error(e, exc_info=True)


class DotDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, dct):
        for key, value in dct.items():
            if hasattr(value, 'keys'):
                value = DotDict(value)
            self[key] = value


schemas = DotDict({
    # Basic
    "scatter": {
        "name": "scatter",
        "args": {
            "x": {},
            "y": {},
            "color": {},
            "size": {},
            "facet_row": {},
            "facet_col": {}
        },
        "function": px.scatter,
        "category": "Basic"},
    "line": {
        "name": "line",
        "args": {
            "x": {},
            "y": {},
            "line_group": {},
            "color": {},
            "facet_row": {},
            "facet_col": {}
        },
        "function": px.line,
        "category": "Basic"},
    "area": {
        "name": "area",
        "args": {
            "x": {},
            "y": {},
            "line_group": {},
            "color": {},
            "facet_row": {},
            "facet_col": {}
        },
        "function": px.area,
        "category": "Basic"},
    "bar": {
        "name": "bar",
        "args": {
            "x": {},
            "y": {},
            "color": {},
            "facet_row": {},
            "facet_col": {}
        },
        "function": px.bar,
        "category": "Basic"},
    "histogram": {
        "name": "histogram",
        "args": {
            "x": {},
            "y": {},
            "color": {},
            "facet_row": {},
            "facet_col": {}
        },
        "function": px.histogram,
        "category": "Basic"},
    "box": {
        "name": "box",
        "args": {
            "x": {},
            "y": {},
            "color": {},
            "facet_row": {},
            "facet_col": {}
        },
        "function": px.box,
        "category": "Basic"},
    "violin": {
        "name": "violin",
        "args": {
            "x": {},
            "y": {},
            "color": {},
            "facet_row": {},
            "facet_col": {}
        },
        "function": px.violin,
        "category": "1D Distributions"},

    # Proportion
    "pie": {
        "name": "pie",
        "args": {
            "names": {},
            "values": {},
        },
        "function": px.pie,
        "category": "Proportion"},
    "treemap": {
        "name": "treemap",
        "args": {
            "names": {},
            "values": {},
        },
        "function": px.treemap,
        "category": "Proportion"},
    "funnel": {
        "name": "funnel",
        "args": {
            "x": {},
            "y": {},
            "color": {},
            "facet_row": {},
            "facet_col": {}
        },
        "function": px.funnel,
        "category": "Proportion"},

    # 2D Distributions
    "density_heatmap": {
        "name": "density_heatmap",
        "args": {
            "x": {},
            "y": {},
            "z": {},
            "facet_row": {},
            "facet_col": {}
        },
        "function": px.density_heatmap,
        "category": "2D Distributions"},
    "density_contour": {
        "name": "density_contour",
        "args": {
            "x": {},
            "y": {},
            "z": {},
            "facet_row": {},
            "facet_col": {}
        },
        "function": px.density_contour,
        "category": "2D Distributions"},

    # 3-Dimensional
    "scatter_3d": {
        "name": "scatter_3d",
        "args": {
            "x": {},
            "y": {},
            "z": {},
            "color": {},

        },
        "function": px.scatter_3d,
        "category": "3-Dimensional"},
    "line_3d": {
        "name": "line_3d",
        "args": {
            "x": {},
            "y": {},
            "z": {},
            "color": {},

        },
        "function": px.line_3d,
        "category": "3-Dimensional"},

    # Multidimensional
    "scatter_matrix": {
        "name": "scatter_matrix",
        "args": {
            "dimensions": {},  # List of columns
            "color": {},

        },
        "function": px.scatter_matrix,
        "category": "Multidimensional"},
    "parallel_coordinates": {
        "name": "parallel_coordinates",
        "args": {
            "dimensions": {},  # List of columns
            "color": {},

        },
        "function": px.parallel_coordinates,
        "category": "Multidimensional"},
    "parallel_categories": {
        "name": "parallel_categories",
        "args": {
            "dimensions": {},  # List of columns
            "color": {},

        },
        "function": px.parallel_categories,
        "category": "Multidimensional"},

    # Tile Maps
    "scatter_mapbox": {
        "name": "scatter_mapbox",
        "args": {
            "lat": {},
            "lon": {},
            "color": {},
            "size": {},

        },
        "function": px.scatter_mapbox,
        "category": "Tile Maps"},
    "line_mapbox": {
        "name": "line_mapbox",
        "args": {
            "lat": {},
            "lon": {},
            "color": {},

        },
        "function": px.line_mapbox,
        "category": "Tile Maps"},
    "density_mapbox": {
        "name": "density_mapbox",
        "args": {
            "lat": {},
            "lon": {},
            "z": {},

        },
        "function": px.density_mapbox,
        "category": "Tile Maps"},

    # Outline Maps
    "scatter_geo": {
        "name": "scatter_geo",
        "args": {
            "lat": {},
            "lon": {},
            "color": {},
            "size": {},

        },
        "function": px.scatter_geo,
        "category": "Outline Maps"},
    "line_geo": {
        "name": "line_geo",
        "args": {
            "lat": {},
            "lon": {},
            "color": {},

        },
        "function": px.line_geo,
        "category": "Outline Maps"},
    "choropleth": {
        "name": "choropleth",
        "args": {
            "lat": {},
            "lon": {},

        },
        "function": px.choropleth,
        "category": "Outline Maps"},

    # Polar Charts
    "scatter_polar": {
        "name": "scatter_polar",
        "args": {
            "r": {},
            "theta": {},
            "color": {},

        },
        "function": px.scatter_polar,
        "category": "Polar Charts"},
    "line_polar": {
        "name": "line_polar",
        "args": {
            "r": {},
            "theta": {},
            "color": {},

        },
        "function": px.line_polar,
        "category": "Polar Charts"},
    "bar_polar": {
        "name": "bar_polar",
        "args": {
            "r": {},
            "theta": {},
            "color": {},

        },
        "function": px.bar_polar,
        "category": "Polar Charts"}
})


def clear_layout(layout):
    for i in reversed(range(layout.count())):
        layout.itemAt(i).widget().setParent(None)


if __name__ == "__main__":
    from pandasgui.utility import fix_ipython, fix_pyqt
    fix_ipython()
    fix_pyqt()
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    gb = GraphBuilder(pokemon, "pokemon")
    gb.show()

    gb2 = GraphBuilder(iris, "iris")
    gb2.show()

    app.exec_()
