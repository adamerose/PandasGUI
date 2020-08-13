import sys

import plotly.express as px
from PyQt5 import QtCore, QtGui, QtWidgets
import pandas as pd

from pandasgui.utility import DotDict, flatten_multiindex, get_logger
from pandasgui.widgets.plotly_viewer import PlotlyViewer
from pandasgui.widgets.spinner import Spinner
from pandasgui.widgets.dialogs import Dragger

logger = get_logger(__name__)


class Grapher(QtWidgets.QWidget):
    def __init__(self, df):
        super().__init__()
        self.df = df.copy()

        self.df.columns = flatten_multiindex(self.df.columns)
        if issubclass(type(self.df.index), pd.core.indexes.multi.MultiIndex):
            self.df = self.df.reset_index()

        self.prev_kwargs = ({})  # This is for carrying plot arg selections forward to new plot types

        self.setWindowTitle("Graph Builder")
        self.workers = []
        self.current_worker = None

        # Dropdown to select plot type
        self.plot_type_picker = QtWidgets.QListWidget()
        self.plot_type_picker.addItems([x["name"] for x in schemas.values()])

        # UI setup
        self.figure_viewer = PlotlyViewer()
        self.figure_viewer.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                         QtWidgets.QSizePolicy.Expanding)

        self.dragger = Dragger(sources=self.df.columns, destinations=[])

        self.spinner = Spinner()
        self.spinner.setParent(self.figure_viewer)

        self.layout = QtWidgets.QGridLayout()
        self.layout.addWidget(self.plot_type_picker, 0, 0)
        self.layout.addWidget(self.dragger, 1, 0)
        self.layout.addWidget(self.figure_viewer, 0, 1, 2, 1)
        self.layout.setColumnStretch(0,0)
        self.layout.setColumnStretch(1,1)

        self.setLayout(self.layout)

        # Signals
        self.plot_type_picker.itemSelectionChanged.connect(self.update_dragger)
        self.dragger.finished.connect(self.update_plot)

        # Initial selection
        self.plot_type_picker.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.plot_type_picker.setCurrentRow(0)
        self.update_dragger()

        # Show a blank axis initially
        self.figure_viewer.set_figure(px.scatter())

    def update_dragger(self):
        current_schema = schemas[self.plot_type_picker.selectedItems()[0].text()]

        self.dragger.set_destinations(current_schema.args.keys())

    def update_plot(self):
        self.spinner.start()
        current_schema = schemas[self.plot_type_picker.selectedItems()[0].text()]

        kwargs = {"data_frame": self.df}
        for key, val in self.dragger.get_data().items():
            if len(val) == 0:
                continue
            elif len(val) == 1:
                kwargs[key] = val[0]
            elif len(val) > 1:
                kwargs[key] = val
            else:
                raise ValueError

        print(kwargs)

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


schemas = DotDict(
    {
        # Basic
        "scatter": {
            "name": "scatter",
            "args": {
                "x": {},
                "y": {},
                "color": {},
                "size": {},
                "facet_row": {},
                "facet_col": {},
            },
            "function": px.scatter,
            "category": "Basic",
        },
        "line": {
            "name": "line",
            "args": {
                "x": {},
                "y": {},
                "line_group": {},
                "color": {},
                "facet_row": {},
                "facet_col": {},
            },
            "function": px.line,
            "category": "Basic",
        },
        "area": {
            "name": "area",
            "args": {
                "x": {},
                "y": {},
                "line_group": {},
                "color": {},
                "facet_row": {},
                "facet_col": {},
            },
            "function": px.area,
            "category": "Basic",
        },
        "bar": {
            "name": "bar",
            "args": {"x": {}, "y": {}, "color": {}, "facet_row": {}, "facet_col": {}},
            "function": px.bar,
            "category": "Basic",
        },
        "histogram": {
            "name": "histogram",
            "args": {"x": {}, "y": {}, "color": {}, "facet_row": {}, "facet_col": {}},
            "function": px.histogram,
            "category": "Basic",
        },
        "box": {
            "name": "box",
            "args": {"x": {}, "y": {}, "color": {}, "facet_row": {}, "facet_col": {}},
            "function": px.box,
            "category": "Basic",
        },
        "violin": {
            "name": "violin",
            "args": {"x": {}, "y": {}, "color": {}, "facet_row": {}, "facet_col": {}},
            "function": px.violin,
            "category": "1D Distributions",
        },
        # Proportion
        "pie": {
            "name": "pie",
            "args": {"names": {}, "values": {}, },
            "function": px.pie,
            "category": "Proportion",
        },
        "treemap": {
            "name": "treemap",
            "args": {"names": {}, "values": {}, },
            "function": px.treemap,
            "category": "Proportion",
        },
        "funnel": {
            "name": "funnel",
            "args": {"x": {}, "y": {}, "color": {}, "facet_row": {}, "facet_col": {}},
            "function": px.funnel,
            "category": "Proportion",
        },
        # 2D Distributions
        "density_heatmap": {
            "name": "density_heatmap",
            "args": {"x": {}, "y": {}, "z": {}, "facet_row": {}, "facet_col": {}},
            "function": px.density_heatmap,
            "category": "2D Distributions",
        },
        "density_contour": {
            "name": "density_contour",
            "args": {"x": {}, "y": {}, "z": {}, "facet_row": {}, "facet_col": {}},
            "function": px.density_contour,
            "category": "2D Distributions",
        },
        # 3-Dimensional
        "scatter_3d": {
            "name": "scatter_3d",
            "args": {"x": {}, "y": {}, "z": {}, "color": {}, },
            "function": px.scatter_3d,
            "category": "3-Dimensional",
        },
        "line_3d": {
            "name": "line_3d",
            "args": {"x": {}, "y": {}, "z": {}, "color": {}, },
            "function": px.line_3d,
            "category": "3-Dimensional",
        },
        # Multidimensional
        "scatter_matrix": {
            "name": "scatter_matrix",
            "args": {"dimensions": {}, "color": {}, },  # List of columns
            "function": px.scatter_matrix,
            "category": "Multidimensional",
        },
        "parallel_coordinates": {
            "name": "parallel_coordinates",
            "args": {"dimensions": {}, "color": {}, },  # List of columns
            "function": px.parallel_coordinates,
            "category": "Multidimensional",
        },
        "parallel_categories": {
            "name": "parallel_categories",
            "args": {"dimensions": {}, "color": {}, },  # List of columns
            "function": px.parallel_categories,
            "category": "Multidimensional",
        },
        # Tile Maps
        "scatter_mapbox": {
            "name": "scatter_mapbox",
            "args": {"lat": {}, "lon": {}, "color": {}, "size": {}, },
            "function": px.scatter_mapbox,
            "category": "Tile Maps",
        },
        "line_mapbox": {
            "name": "line_mapbox",
            "args": {"lat": {}, "lon": {}, "color": {}, },
            "function": px.line_mapbox,
            "category": "Tile Maps",
        },
        "density_mapbox": {
            "name": "density_mapbox",
            "args": {"lat": {}, "lon": {}, "z": {}, },
            "function": px.density_mapbox,
            "category": "Tile Maps",
        },
        # Outline Maps
        "scatter_geo": {
            "name": "scatter_geo",
            "args": {"lat": {}, "lon": {}, "color": {}, "size": {}, },
            "function": px.scatter_geo,
            "category": "Outline Maps",
        },
        "line_geo": {
            "name": "line_geo",
            "args": {"lat": {}, "lon": {}, "color": {}, },
            "function": px.line_geo,
            "category": "Outline Maps",
        },
        "choropleth": {
            "name": "choropleth",
            "args": {"lat": {}, "lon": {}, },
            "function": px.choropleth,
            "category": "Outline Maps",
        },
        # Polar Charts
        "scatter_polar": {
            "name": "scatter_polar",
            "args": {"r": {}, "theta": {}, "color": {}, },
            "function": px.scatter_polar,
            "category": "Polar Charts",
        },
        "line_polar": {
            "name": "line_polar",
            "args": {"r": {}, "theta": {}, "color": {}, },
            "function": px.line_polar,
            "category": "Polar Charts",
        },
        "bar_polar": {
            "name": "bar_polar",
            "args": {"r": {}, "theta": {}, "color": {}, },
            "function": px.bar_polar,
            "category": "Polar Charts",
        },
    }
)


def clear_layout(layout):
    for i in reversed(range(layout.count())):
        layout.itemAt(i).widget().setParent(None)


if __name__ == "__main__":
    from pandasgui.utility import fix_ipython, fix_pyqt
    from pandasgui.datasets import iris, pokemon

    fix_ipython()
    fix_pyqt()
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    gb2 = Grapher(pokemon)
    gb2.show()

    app.exec_()
