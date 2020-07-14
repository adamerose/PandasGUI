from pandasgui.utility import fix_ipython, fix_pyqt
from threading import Thread
from pandasgui.widgets.plotly_viewer import PlotlyViewer
from pandasgui.utility import flatten_multiindex
from pandasgui.datasets import pokemon
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


# from plotly.offline import plot
# fig = px.histogram(pokemon, x="HP")
# plot(px.histogram(pokemon, x="HP"))

def clear_layout(layout):
    for i in reversed(range(layout.count())):
        layout.itemAt(i).widget().setParent(None)


class DotDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, dct):
        for key, value in dct.items():
            if hasattr(value, 'keys'):
                value = DotDict(value)
            self[key] = value


class GraphBuilder(QtWidgets.QWidget):

    def __init__(self, df):
        super().__init__()

        df = df.copy()
        df.columns = flatten_multiindex(df.columns)
        self.df = df

        self.schemas = DotDict({
            'histogram': {
                'name': 'Histogram',
                'function': self.histogram,
                'args': {
                    'x': {'type': str,
                          'required': True},
                    'color': {'type': str,
                              'required': False}
                }},

            'scatter': {'name': 'Scatter Plot',
                        'function': self.scatter,
                        'args': {
                            'x': {'type': str,
                                  'required': True},
                            'y': {'type': str,
                                  'required': True},
                            'color': {'type': str,
                                      'required': False}
                        }},

            'box': {'name': 'Box Plot',
                    'function': self.box,
                    'args': {
                        'x': {'type': str,
                              'required': True},
                        'y': {'type': str,
                              'required': False},
                        'color': {'type': str,
                                  'required': False}
                    }},
            'line': {'name': 'Line Plot',
                     'function': self.line,
                     'args': {
                         'x': {'type': str,
                               'required': True},
                         'y': {'type': str,
                               'required': False},
                         'color': {'type': str,
                                   'required': False}
                     }},
            'bar': {'name': 'Bar Plot',
                    'function': self.bar,
                    'args': {
                        'x': {'type': str,
                              'required': True},
                        'y': {'type': str,
                              'required': False},
                        'color': {'type': str,
                                  'required': False}
                    }}
        })

        self.setWindowTitle("Graph Builder")
        self.workers = []

        # Dropdown to select plot type
        self.plot_type_picker = QtWidgets.QComboBox()
        self.plot_type_picker.addItems([x['name'] for x in self.schemas.values()])
        self.plot_type_picker.currentIndexChanged.connect(self.build_ui)

        # UI setup
        self.figure_viewer = PlotlyViewer()
        self.figure_viewer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.schema_layout = QtWidgets.QVBoxLayout()
        self.schema_layout_outer = QtWidgets.QVBoxLayout()
        self.schema_layout_outer.addWidget(self.plot_type_picker)
        self.schema_layout_outer.addLayout(self.schema_layout)
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
        self.current_schema = next(x for x in self.schemas.values() if x["name"] == self.plot_type_picker.currentText())
        clear_layout(self.schema_layout)

        for key, val in self.current_schema.args.items():
            l = QtWidgets.QLabel(key)
            w = QtWidgets.QComboBox()
            self.current_schema.args[key]['widget'] = w
            w.addItems([""] + list(self.df.columns))
            w.currentIndexChanged.connect(self.update_plot)
            self.schema_layout.addWidget(l)
            self.schema_layout.addWidget(w)

        self.update_plot()

    def update_plot(self):
        self.spinner.start()

        # Get dict of user selected values from widgets for current schema
        kwargs = {}
        for key, arg in self.current_schema.args.items():
            value = arg.widget.currentText()
            if value:
                kwargs[key] = value

        # Remove Nones and blanks
        kwargs = {k: v for k, v in kwargs.items() if v not in [None, ""]}

        # Verify that all required plot arguments were provided...
        if all([arg_key in kwargs.keys() for arg_key, arg_val in self.current_schema.args.items() if
                arg_val.required]):
            func = self.current_schema.function
            w = Worker(func, kwargs)
            w.finished.connect(self.worker_callback)
            w.start()
            self.workers.append(w)
        else:
            logging.info("Invalid arguments to histogram: " + str(kwargs))
            self.spinner.stop()

    @QtCore.pyqtSlot(object)
    def worker_callback(self, fig):
        self.figure_viewer.set_figure(fig)
        self.spinner.stop()

    def histogram(self, **kwargs):
        return px.histogram(data_frame=self.df, **kwargs)

    def scatter(self, **kwargs):
        return px.scatter(data_frame=self.df, **kwargs)

    def box(self, **kwargs):
        return px.box(data_frame=self.df, **kwargs)

    def line(self, **kwargs):
        return px.line(data_frame=self.df, **kwargs)

    def bar(self, **kwargs):
        return px.bar(data_frame=self.df, **kwargs)


# https://stackoverflow.com/questions/9957195/updating-gui-elements-in-multithreaded-pyqt
class Worker(QtCore.QThread):
    finished = QtCore.pyqtSignal(object)

    def __init__(self, func, kwargs):
        QtCore.QThread.__init__(self)
        self.func = func
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(**self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            logging.info(e.with_traceback())


if __name__ == "__main__":
    fix_ipython()
    fix_pyqt()

    # Create a QApplication instance or use the existing one if it exists
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    gb = GraphBuilder(pokemon)
    # gb = QtWidgets.QComboBox()
    gb.show()
    app.exec_()
