import os
import sys
import tempfile

from plotly.io import to_html
from PyQt5 import QtCore, QtGui, QtWidgets, sip
from PyQt5.QtCore import Qt

import logging
logger = logging.getLogger(__name__)

# https://stackoverflow.com/a/64743807/3620725
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-logging --log-level=3"


# Since pandasgui might be imported after other packages already created a QApplication,
# we need to hack around this import restriction on QtWebEngineWidgets
# https://stackoverflow.com/a/57436077/3620725
try:
    from PyQt5 import QtWebEngineWidgets
except ImportError as e:
    if e.msg == "QtWebEngineWidgets must be imported before a QCoreApplication instance is created":
        logger.info("Reinitialized existing QApplication instance to allow import of QtWebEngineWidgets.")

        app = QtWidgets.QApplication.instance()
        app.quit()
        sip.delete(app)
        from PyQt5 import QtWebEngineWidgets

        app.__init__(sys.argv)
    else:
        raise e


class PlotlyViewer(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, fig=None):
        super().__init__()

        self.page().profile().downloadRequested.connect(self.on_downloadRequested)

        # https://stackoverflow.com/a/8577226/3620725
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False)
        self.set_figure(fig)

        self.resize(700, 600)
        self.setWindowTitle("Plotly Viewer")



    def set_figure(self, fig=None):
        self.temp_file.seek(0)

        if fig:
            self.temp_file.write(to_html(fig, config={"responsive": True}))
        else:
            self.temp_file.write("")

        self.temp_file.truncate()
        self.temp_file.seek(0)
        self.load(QtCore.QUrl.fromLocalFile(self.temp_file.name))

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.temp_file.close()
        os.unlink(self.temp_file.name)
        super().closeEvent(event)

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(400, 400)

    # https://stackoverflow.com/questions/55963931/how-to-download-csv-file-with-qwebengineview-and-qurl
    def on_downloadRequested(self, download):
        dialog = QtWidgets.QFileDialog()
        dialog.setDefaultSuffix(".png")
        path, _ = dialog.getSaveFileName(self, "Save File", os.path.join(os.getcwd(), "newplot.png"), "*.png")
        if path:
            download.setPath(path)
            download.accept()

if __name__ == "__main__":
    # Create a QtWidgets.QApplication instance or use the existing one if it exists
    app = QtWidgets.QApplication(sys.argv)

    import numpy as np
    import plotly.graph_objs as go
    from pandasgui.utility import fix_ipython, fix_pyqt

    fix_ipython()
    fix_pyqt()

    fig = go.Figure()
    fig.add_scatter(
        x=np.random.rand(100),
        y=np.random.rand(100),
        mode="markers",
        marker={
            "size": 30,
            "color": np.random.rand(100),
            "opacity": 0.6,
            "colorscale": "Viridis",
        },
    )

    pv = PlotlyViewer(fig)
    pv.show()
    app.exec_()
