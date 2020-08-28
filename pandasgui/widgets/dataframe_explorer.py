import sys

import pandas as pd
from PyQt5 import QtWidgets

from pandasgui.utility import get_logger
from pandasgui.widgets.dataframe_viewer import DataFrameViewer
from pandasgui.widgets.grapher import Grapher
from pandasgui.widgets.detachable_tab_widget import DetachableTabWidget
from pandasgui.widgets.filter_viewer import FilterViewer
from pandasgui.store import PandasGuiDataFrame

logger = get_logger(__name__)


class DataFrameExplorer(DetachableTabWidget):
    def __init__(self, pgdf: PandasGuiDataFrame):
        super().__init__()

        pgdf = PandasGuiDataFrame.cast(pgdf)
        pgdf.dataframe_explorer = self
        self.pgdf = pgdf

        # DataFrame tab
        self.dataframe_tab = DataFrameViewer(pgdf)
        self.addTab(self.dataframe_tab, "DataFrame")

        # Filters tab
        self.filters_tab = FilterViewer(pgdf)
        self.addTab(self.filters_tab, "Filters")

        # Statistics tab
        self.statistics_tab = self.make_statistics_tab(pgdf)
        self.addTab(self.statistics_tab, "Statistics")

        # Grapher tab
        graph_maker = Grapher(pgdf)
        self.addTab(graph_maker, "Grapher")

    def __reduce__(self):
        # This is so dataclasses.asdict doesn't complain about this being unpicklable
        return "DataFrameExplorer"


    def make_statistics_tab(self, pgdf: PandasGuiDataFrame):
        stats_df = pd.DataFrame(
            {
                "Type": pgdf.dataframe.dtypes.replace("object", "string").astype(str),
                "Count": pgdf.dataframe.count(),
                "N Unique": pgdf.dataframe.nunique(),
                "Mean": pgdf.dataframe.mean(numeric_only=True),
                "StdDev": pgdf.dataframe.std(numeric_only=True),
                "Min": pgdf.dataframe.min(numeric_only=True),
                "Max": pgdf.dataframe.max(numeric_only=True),
            }
        )

        stats_pgdf = PandasGuiDataFrame(stats_df.reset_index())
        w = DataFrameViewer(stats_pgdf)
        w.setAutoFillBackground(True)
        return w


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    from pandasgui.datasets import pokemon

    # Create and show widget
    dfe = DataFrameExplorer(pokemon)
    dfe.show()

    sys.exit(app.exec_())
