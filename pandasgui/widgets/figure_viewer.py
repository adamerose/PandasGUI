import os
import sys
import tempfile

from PyQt5 import QtCore, QtGui, QtWidgets, sip
import PyQt5
import logging

from pandasgui.store import PandasGuiStoreItem
from pandasgui.utility import get_figure_type

logger = logging.getLogger(__name__)

# https://stackoverflow.com/a/64743807/3620725
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-logging --log-level=3"

# Since pandasgui might be imported after other packages already created a QApplication,
# we need to hack around this import restriction on QtWebEngineWidgets
# https://stackoverflow.com/a/57436077/3620725

if "PyQt5.QtWebEngineWidgets" not in sys.modules:
    app = QtWidgets.QApplication.instance()

    if app is None:
        pass
    else:
        logger.warning("Reinitializing existing QApplication to allow import of QtWebEngineWidgets. "
                       "This may cause problems. "
                       "To avoid this, import pandasgui or PyQt5.QtWebEngineWidgets before a QApplication is created.")
        app.quit()
        sip.delete(app)

        app.__init__(sys.argv + ["--ignore-gpu-blacklist", "--enable-gpu-rasterization"])


class FigureViewer(PyQt5.QtWebEngineWidgets.QWebEngineView, PandasGuiStoreItem):
    def __init__(self, fig=None, store=None):
        super().__init__()
        self.store = store
        self.page().profile().downloadRequested.connect(self.on_downloadRequested)

        # Fix scrollbar sometimes disappearing after Plotly autosizes and leaving behind white space
        self.settings().setAttribute(self.settings().ShowScrollBars, False)
        self.settings().setAttribute(PyQt5.QtWebEngineWidgets.QWebEngineSettings.WebGLEnabled, True)

        # https://stackoverflow.com/a/8577226/3620725
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False)
        self.set_figure(fig)

        self.resize(700, 600)
        self.setWindowTitle("Plotly Viewer")

    def set_figure(self, fig=None):

        self.temp_file.seek(0)
        dark = self.store is not None and self.store.settings.theme.value == "dark"
        fig_type = get_figure_type(fig)

        if fig is None:
            html = ""
        elif fig_type == "plotly":
            from plotly.io import to_html
            if dark:
                fig.update_layout(template="plotly_dark", autosize=True)
            html = to_html(fig, config={"responsive": True})
        elif fig_type == "bokeh":
            from bokeh.resources import CDN
            from bokeh.embed import file_html
            html = file_html(fig, resources=CDN, title="my fig")
        elif fig_type == "matplotlib":
            fig = fig.get_figure() or fig
            import base64
            from io import BytesIO
            tmpfile = BytesIO()
            fig.savefig(tmpfile, format='png')
            encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
            html = '<img src=\'data:image/png;base64,{}\'>'.format(encoded)
        elif fig_type == "altair":
            fig = fig.properties(
                width='container',
                height='container'
            )
            from io import StringIO
            tmp = StringIO()
            fig.save(tmp, format='html')
            html = tmp.getvalue()

        else:
            raise TypeError

        html = html.replace("<style>",
                     "<style>"
                     "body{margin: 0; width:100vw; height:100vh;} "
                     # https://github.com/vega/react-vega/issues/85#issuecomment-795138175
                     ".vega-embed{width:100%; height:100%;} "
                     )

        self.temp_file.write(html)
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

    def pg_widget(self):
        return self

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

    pv = FigureViewer(fig)
    pv.show()
    app.exec_()
