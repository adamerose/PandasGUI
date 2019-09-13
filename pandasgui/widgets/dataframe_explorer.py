"""DataFrameExplorer"""

from PyQt5 import QtWidgets
import pandas as pd
import sys
import matplotlib.pyplot as plt
import seaborn as sns
from pandasgui.widgets import DataFrameViewer
from pandasgui.widgets import FigureViewer

class DataFrameExplorer(QtWidgets.QTabWidget):
    """
    This is a QTabWidget for analyzing a single DataFrame where the first tab is a DataFrameViewer widget

    Args:
        df (DataFrame): The DataFrame to display
    """

    def __init__(self, df):

        super().__init__()

        df = df.copy()
        self.df = df

        # DataFrame tab
        self.dataframe_tab = DataFrameViewer(self.df)
        self.addTab(self.dataframe_tab, "DataFrame")

        # Statistics tab
        self.statistics_tab = self.make_statistics_tab(df)
        self.addTab(self.statistics_tab, "Statistics")

        # Histogram tab
        if not (type(df.index) == pd.MultiIndex or type(df.columns) == pd.MultiIndex):
            histogram_tab = self.make_histogram_tab(df)
            self.addTab(histogram_tab, "Histogram")

    def make_statistics_tab(self, df):
        stats_df = pd.DataFrame({
            'Type': df.dtypes.replace('object', 'string'),
            'Count': df.count(numeric_only=True),
            'Mean': df.mean(numeric_only=True),
            'StdDev': df.std(numeric_only=True),
            'Min': df.min(numeric_only=True),
            'Max': df.max(numeric_only=True),
        })
        w = DataFrameViewer(stats_df)
        w.setAutoFillBackground(True)
        return w

    def make_histogram_tab(self, df):
        return self.HistogramTab(df)

    class HistogramTab(QtWidgets.QWidget):
        def __init__(self, df):
            super().__init__()

            self.df = df.copy()

            self.picker = QtWidgets.QComboBox()
            self.picker.addItems(df.columns)
            self.picker.currentIndexChanged.connect(self.update_plot)
            self.figure_viewer = FigureViewer()

            self.layout = QtWidgets.QVBoxLayout()

            self.layout.addWidget(self.picker)
            self.layout.addWidget(self.figure_viewer)

            self.setLayout(self.layout)
            self.update_plot()

        def update_plot(self):
            plt.ioff()
            col = self.picker.currentText()

            plt.figure()

            arr = self.df[col].dropna()
            if self.df[col].dtype.name in ['object', 'bool', 'category']:
                ax = sns.countplot(y=arr, color='grey', order=arr.value_counts().iloc[:10].index)

            else:
                ax = sns.distplot(arr, color='black', hist_kws=dict(color='grey', alpha=1))

            self.figure_viewer.setFigure(ax.figure)


# Examples
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    from pandasgui.datasets import iris, flights, multi, pokemon

    # Create and show widget
    dfe = DataFrameExplorer(flights)
    dfe.show()

    sys.exit(app.exec_())
