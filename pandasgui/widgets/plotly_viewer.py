import os, sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl
from plotly.io import to_html
import tempfile

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
    def __init__(self, fig=None):
        super().__init__()

        if fig:
            self.set_figure(fig)

        self.resize(700, 600)
        self.setWindowTitle("Plotly Viewer")

    def set_figure(self, fig):
        config = {'responsive': True}
        self.temp_file = tempfile.TemporaryFile(mode='w', suffix='.html')
        self.temp_file.write(to_html(fig, config=config))
        self.temp_file.seek(0)
        self.load(QUrl.fromLocalFile(self.temp_file.name))

if __name__ == "__main__":
    # Create a QApplication instance or use the existing one if it exists
    app = QApplication(sys.argv)

    import numpy as np
    import plotly.graph_objs as go
    from pandasgui.utility import fix_ipython, fix_pyqt
    fix_ipython()
    fix_pyqt()

    fig = go.Figure()
    fig.add_scatter(x=np.random.rand(100), y=np.random.rand(100), mode='markers',
                    marker={'size': 30, 'color': np.random.rand(100), 'opacity': 0.6,
                            'colorscale': 'Viridis'});

    pv = PlotlyViewer(fig)
    # app.exec_()