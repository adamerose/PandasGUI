import os
import sys
import tempfile
from plotly.io import to_html
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

from pandasgui.utility import get_logger

logger = get_logger(__name__)
# If QtWebEngineWidgets is imported while a QtWidgets.QApplication instance already exists it will fail, so we have to hack it
try:
    from PyQt5 import QtWebEngineWidgets
except ImportError as e:
    if (
        e.msg
        == "QtWebEngineWidgets must be imported before a QCoreApplication instance is created"
    ):
        logger.info("Killing QtWidgets.QApplication to reimport QtWebEngineWidgets")
        from PyQt5 import QtWidgets

        app = QtWidgets.QtWidgets.QApplication.instance()
        if app is not None:
            import sip

            app.quit()
            sip.delete(app)
        import sys
        from PyQt5 import QtCore, QtWebEngineWidgets

        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
        app = QtWidgets.QtWidgets.QApplication(sys.argv)
        from PyQt5 import QtWebEngineWidgets
    else:
        raise e


class PlotlyViewer(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, fig=None):
        super().__init__()

        # https://stackoverflow.com/a/8577226/3620725
        self.temp_file = tempfile.TemporaryFile(mode="w", suffix=".html", delete=False)
        self.set_figure(fig)

        self.resize(700, 600)
        self.setWindowTitle("Plotly Viewer")

    def set_figure(self, fig=None):
        self.temp_file.seek(0)

        if fig:
            self.temp_file.write(to_html(fig, config={"responsive": True}))
            # self.temp_file.write("<html><body>hello</body></html>")
        else:
            self.temp_file.write("")

        self.temp_file.truncate()
        self.temp_file.seek(0)
        self.load(QtCore.QUrl.fromLocalFile(self.temp_file.name))

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        os.unlink(self.temp_file.name)
        self.temp_file.close()


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
    # app.exec_()
