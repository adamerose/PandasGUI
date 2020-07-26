import sys

import pandas as pd
from PyQt5 import QtWidgets

from pandasgui.utility import get_logger
from pandasgui.widgets.dataframe_viewer import DataFrameViewer
from pandasgui.widgets.grapher import Grapher
from pandasgui.widgets.detachable_tab_widget import DetachableTabWidget
from pandasgui.store import Store, PandasGuiDataFrame

logger = get_logger(__name__)


class DataFrameExplorer(DetachableTabWidget):
    def __init__(self, df: PandasGuiDataFrame, editable=True):
        super().__init__()

        self.df = df
        self.editable = editable

        # DataFrame tab
        self.dataframe_tab = DataFrameViewer(self.df, editable=self.editable)
        self.addTab(self.dataframe_tab, "DataFrame")

        # Statistics tab
        self.statistics_tab = self.make_statistics_tab(df)
        self.addTab(self.statistics_tab, "Statistics")

        # Grapher tab
        graph_maker = Grapher(df)
        self.addTab(graph_maker, "Grapher")

    def __reduce__(self):
        # This is so dataclasses.asdict doesn't complain about this being unpicklable
        return "DataFrameExplorer"


    def make_statistics_tab(self, df):
        stats_df = pd.DataFrame(
            {
                "Type": df.dtypes.replace("object", "string").astype(str),
                "Count": df.count(),
                "N Unique": df.nunique(),
                "Mean": df.mean(numeric_only=True),
                "StdDev": df.std(numeric_only=True),
                "Min": df.min(numeric_only=True),
                "Max": df.max(numeric_only=True),
            }
        )

        stats_df = stats_df.reset_index()
        w = DataFrameViewer(stats_df, editable=self.editable)
        w.setAutoFillBackground(True)
        return w


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    from pandasgui.datasets import iris, flights, multi, pokemon

    # Create and show widget
    dfe = DataFrameExplorer(flights)
    dfe.show()

    sys.exit(app.exec_())
