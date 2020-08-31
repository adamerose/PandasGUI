import sys

import plotly.express as px
from PyQt5 import QtCore, QtGui, QtWidgets
import pandas as pd
from pandasgui.store import Store, PandasGuiDataFrame

from pandasgui.utility import flatten_multiindex, get_logger
from pandasgui.widgets.plotly_viewer import PlotlyViewer
from pandasgui.widgets.spinner import Spinner
from pandasgui.widgets.dialogs import Dragger
from pandasgui.widgets.grapher_plotting import schemas

logger = get_logger(__name__)


class Grapher(QtWidgets.QWidget):
    def __init__(self, pgdf: PandasGuiDataFrame):
        super().__init__()

        pgdf = PandasGuiDataFrame.cast(pgdf)

        self.df = pgdf.dataframe.copy()

        self.df.columns = flatten_multiindex(self.df.columns)
        if issubclass(type(self.df.index), pd.core.indexes.multi.MultiIndex):
            self.df = self.df.reset_index()

        self.prev_kwargs = ({})  # This is for carrying plot arg selections forward to new plot types

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

        self.dragger = Dragger(sources=self.df.columns, destinations=[], source_types=self.df.dtypes.values.astype(str))

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
        self.plot_type_picker.itemSelectionChanged.connect(self.update_dragger)
        self.dragger.finished.connect(self.update_plot)

        # Initial selection
        self.plot_type_picker.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.plot_type_picker.setCurrentRow(0)
        self.update_dragger()

        # Show a blank axis initially
        self.figure_viewer.set_figure(px.scatter())

    def update_dragger(self):
        selected_plot_label = self.plot_type_picker.selectedItems()[0].text()
        current_schema = next(filter(lambda schema: schema.label == selected_plot_label, schemas))
        arg_list = [arg.arg_name for arg in current_schema.args]
        #
        # if self.show_all:
        #     arg_list = [arg.arg_name for arg in current_schema.args]
        # else:
        #     arg_list = [arg.arg_name for arg in current_schema.args if not arg.advanced]

        self.dragger.set_destinations(arg_list)

    def update_plot(self):
        self.spinner.start()
        selected_plot_label = self.plot_type_picker.selectedItems()[0].text()
        current_schema = next(filter(lambda x: x.label == selected_plot_label, schemas))

        kwargs = {"data_frame": self.df}
        for key, val in self.dragger.get_data().items():
            if type(val) == list and len(val) == 0:
                continue
            elif type(val) == list and len(val) == 1:
                kwargs[key] = val[0]
            elif type(val) == list and len(val) > 1:
                kwargs[key] = val
            else:
                kwargs[key] = val

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
