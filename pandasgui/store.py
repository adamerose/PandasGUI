from dataclasses import dataclass, field, asdict
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

    initial_index: pd.Index = None

    column_sorted: Union[int, None] = None
    index_sorted: Union[int, None] = None
    sort_is_descending: Union[bool, None] = None

    def __init__(self, df):
        super().__init__(df)
        self.init_inplace()

    def init_inplace(self):
        self.initial_index = self.index.copy()

    def update_inplace(self, df):
        self._update_inplace(df)

    def sort_by(self, ix: int, is_index=False):
        if is_index:

            # Clicked an unsorted index
            if ix != self.index_sorted:
                self.sort_index(level=ix, ascending=True, kind="mergesort", inplace=True)

                self.index_sorted = ix
                self.sort_is_descending = False

            # Clicked a sorted index level
            elif ix == self.index_sorted and not self.sort_is_descending:
                self.sort_index(level=ix, ascending=False, kind="mergesort", inplace=True)

                self.index_sorted = ix
                self.sort_is_descending = True

            # Clicked a reverse sorted index level
            elif ix == self.index_sorted and self.sort_is_descending:
                temp = self.reindex(self.initial_index)
                self.update_inplace(temp)

                self.index_sorted = None
                self.sort_is_descending = None

            self.column_sorted = None

        else:
            col_name = self.columns[ix]

            # Clicked an unsorted column
            if ix != self.column_sorted:
                self.sort_values(col_name, ascending=True, kind="mergesort", inplace=True)

                self.column_sorted = ix
                self.sort_is_descending = False

            # Clicked a sorted column
            elif ix == self.column_sorted and not self.sort_is_descending:
                self.sort_values(col_name, ascending=False, kind="mergesort", inplace=True)

                self.column_sorted = ix
                self.sort_is_descending = True

            # Clicked a reverse sorted column
            elif ix == self.column_sorted and self.sort_is_descending:
                temp = self.reindex(self.initial_index)
                self.update_inplace(temp)

                self.column_sorted = None
                self.sort_is_descending = None

            self.index_sorted = None

        self.dataframe_viewer.data_changed()


@dataclass
class Store:
    settings: Settings = Settings()
    data: List[PandasGuiDataFrame] = field(default_factory=list)

    def get_dataframe(self, name):
        return next((x for x in self.data if x.name == name), None)

    def to_dict(self):
        import json
        return json.loads(json.dumps(self, default=lambda o: o.__dict__))
