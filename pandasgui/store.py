from dataclasses import dataclass, field
from typing import Dict, List, Union
import pandas as pd



@dataclass
class Settings:
    editable: bool = True  # Are table cells editable
    block: bool = False


@dataclass
class PandasGuiDataFrame(pd.DataFrame):

    name: str = None
    dataframe_explorer: "DataFrameExplorer" = None
    dataframe_viewer: "DataFrameViewer" = None

    def update_inplace(self, df):
        self._update_inplace(df)

    # Negative number means index level
    column_sorted: int = None
    sort_is_ascending: bool = None

    def sort_by(self, ix: int):
        if ix < 0:
            level = self.index[-ix]
            if ix == self.column_sorted:
                if self.sort_is_ascending:
                    self.sort_index(level=level, ascending=False, kind="mergesort", inplace=True)
                    self.sort_is_ascending = False
                else:
                    self.sort_index(level=level, ascending=True, kind="mergesort", inplace=True)
                    self.sort_is_ascending = True
            else:
                self.sort_index(level=level, ascending=True, kind="mergesort", inplace=True)
                self.sort_is_ascending = True
        else:
            col = self.columns[ix]
            if ix == self.column_sorted:
                if self.sort_is_ascending:
                    self.sort_values(col, ascending=False, kind="mergesort", inplace=True)
                    self.sort_is_ascending = False
                else:
                    self.sort_values(col, ascending=True, kind="mergesort", inplace=True)
                    self.sort_is_ascending = True
            else:
                self.sort_values(col, ascending=True, kind="mergesort", inplace=True)
                self.sort_is_ascending = True

        self.column_sorted = ix


@dataclass
class Store:
    settings: Settings = Settings()
    data: List[PandasGuiDataFrame] = field(default_factory=list)

    def get_dataframe(self, name):
        return next((x for x in self.data if x.name == name), None)