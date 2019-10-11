import os, sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl
import plotly
import tempfile

instance_list = []

# If QtWebEngineWidgets is imported while a QApplication instance already exists it will fail, so we have to
try:
    from PyQt5 import QtWebEngineWidgets
except ImportError as e:
    if e.msg == "QtWebEngineWidgets must be imported before a QCoreApplication instance is created":
        print("Killing QApplication to reimport QtWebEngineWidgets")
        from PyQt5 import sip

        app = QApplication.instance()
        app.quit()
        sip.delete(app)
        del app
        from PyQt5 import QtWebEngineWidgets

        # Without remaking the QApplication you will get an unrecoverable crash on the next attempted usage of it
        app = QApplication([])
    else:
        raise e


class PlotlyViewer(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, fig):
        # Create a QApplication instance or use the existing one if it exists
        self.app = QApplication.instance() if QApplication.instance() else QApplication(sys.argv)

        super().__init__()

        # This ensures there is always a reference to this widget and it doesn't get garbage collected
        global instance_list
        instance_list.append(self)

        # Store the Plotly html in a temp file to load into the webview.
        # NOTE - QWebEngineView.setHtml doesn't work with data over 2 MB, that's why I use a temp file instead
        self.temp_file = tempfile.TemporaryFile(mode='w', suffix='.html')
        self.temp_file.write(fig.to_html())
        self.setWindowTitle("Plotly Viewer")

        self.load(QUrl.fromLocalFile(self.temp_file.name))

        self.resize(640, 480)
        self.show()


def view(fig, block=False):
    pv = PlotlyViewer(fig)

    if block:
        pv.app.exec_()


if __name__ == "__main__":
    import numpy as np
    import plotly.graph_objs as go
    from pandasgui.utility import fix_ipython

    fix_ipython()

    fig = go.Figure()
    fig.add_scatter(x=np.random.rand(100), y=np.random.rand(100), mode='markers',
                    marker={'size': 30, 'color': np.random.rand(100), 'opacity': 0.6,
                            'colorscale': 'Viridis'});

    view(fig)
