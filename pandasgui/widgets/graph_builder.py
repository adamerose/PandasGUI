from pandasgui.utility import fix_ipython, fix_pyqt

from pandasgui.widgets.bokeh_viewer import BokehViewer
from pandasgui.widgets.plotly_viewer import PlotlyViewer
from pandasgui.utility import flatten_multiindex
from pandasgui.datasets import pokemon
from PyQt5 import QtWidgets
import plotly.express as px

# from plotly.offline import plot
# fig = px.histogram(pokemon, x="HP")
# plot(px.histogram(pokemon, x="HP"))

class GraphBuilder(QtWidgets.QWidget):
    def __init__(self, df):
        df.columns = flatten_multiindex(df.columns)

        super().__init__()
        self.setWindowTitle("Graph Builder")
        self.df = df.copy()

        self.picker = QtWidgets.QComboBox()
        self.picker.addItems(df.columns)
        self.picker.currentIndexChanged.connect(self.update_plot)
        self.figure_viewer = PlotlyViewer()

        self.layout = QtWidgets.QVBoxLayout()

        self.layout.addWidget(self.picker)
        self.layout.addWidget(self.figure_viewer)

        self.setLayout(self.layout)
        self.update_plot()

    def update_plot(self):
        col = self.picker.currentText()
        fig = px.histogram(self.df, x=col)
        # if self.df[col].dtype.name in ['object', 'bool', 'category']:
        self.figure_viewer.set_figure(fig)

if __name__ == "__main__":
    fix_ipython()
    fix_pyqt()
    from PyQt5.QtWidgets import QApplication
    import sys

    # Create a QApplication instance or use the existing one if it exists
    app = QApplication(sys.argv)
    gb = GraphBuilder(pokemon)
