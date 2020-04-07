import os, sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl
import tempfile
from bokeh.resources import CDN
# TODO: use local static JS instead of loading from CDN
from bokeh.embed import file_html


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


class BokehViewer(QtWebEngineWidgets.QWebEngineView):
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

        self.update(fig)

        self.setWindowTitle("Bokeh Viewer")
        self.resize(640, 480)
        self.show()

    def update(self, fig):
        html = file_html(fig, resources=CDN, title="my fig")
        self.temp_file.seek(0)
        self.temp_file.truncate()
        self.temp_file.write(html)
        self.temp_file.seek(0)
        self.load(QUrl.fromLocalFile(self.temp_file.name))


if __name__ == "__main__":
    from bokeh.plotting import figure
    from pandasgui.utility import fix_ipython
    fix_ipython()

    fig = figure(sizing_mode = 'stretch_both')
    fig.circle([1, 2, 3, 4], [3, 4, 5, 6], size=20)

    bv = BokehViewer(fig)
