from dataclasses import dataclass, field, asdict
from typing import Dict, List, Union
import pandas as pd
from pandas import DataFrame
from PyQt5 import QtCore, QtGui, QtWidgets, sip
from PyQt5.QtCore import Qt
import traceback
from functools import wraps
from datetime import datetime
from pandasgui.utility import get_logger

logger = get_logger(__name__)


@dataclass
class Settings:
    # Should GUI block code execution until closed
    block: bool = False
    # Are table cells editable
    editable: bool = True


@dataclass
class Filter:
    expr: str
    enabled: bool
    failed: bool


@dataclass
class HistoryItem:
    name: str
    args: tuple
    kwargs: dict
    time: str


def track_history(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self.history.append(HistoryItem(name=func.__name__,
                                        args=args,
                                        kwargs=kwargs,
                                        time=datetime.now().strftime("%H:%M:%S"))
                            )
        func(self, *args, **kwargs)

    return wrapper


class PandasGuiDataFrame:
    def __init__(self, df: DataFrame, name: str = 'Untitled'):
        super().__init__()
        df = df.copy()

        self.dataframe = df
        self.dataframe_original = df
        self.name = name

        self.history: List[HistoryItem] = []

        # References to other object instances that may be assigned later
        self.settings: Settings = Settings()
        self.dataframe_explorer: Union["DataFrameExplorer", None] = None
        self.dataframe_viewer: Union["DataFrameViewer", None] = None
        self.filter_viewer: Union["FilterViewer", None] = None

        self.column_sorted: Union[int, None] = None
        self.index_sorted: Union[int, None] = None
        self.sort_is_ascending: Union[bool, None] = None

        self.filters: List[Filter] = []

    def update(self):
        models = []
        if self.dataframe_viewer is not None:
            models += [self.dataframe_viewer.dataView.model(),
                       self.dataframe_viewer.columnHeader.model(),
                       self.dataframe_viewer.indexHeader.model(),
                       self.dataframe_viewer.columnHeaderNames.model(),
                       self.dataframe_viewer.indexHeaderNames.model(),
                       ]

        if self.filter_viewer is not None:
            models += [self.filter_viewer.list_model,
                       ]

        for model in models:
            model.beginResetModel()
            model.endResetModel()

    @track_history
    def edit_data(self, row, col, value):
        # Not using iat here because it won't work with MultiIndex
        self.dataframe_original.at[self.dataframe.index[row], self.dataframe.columns[col]] = value
        self.apply_filters()
        self.update()

    @track_history
    def sort_column(self, ix: int):
        col_name = self.dataframe.columns[ix]

        # Clicked an unsorted column
        if ix != self.column_sorted:
            self.dataframe = self.dataframe.sort_values(col_name, ascending=True, kind="mergesort")
            self.column_sorted = ix
            self.sort_is_ascending = True

        # Clicked a sorted column
        elif ix == self.column_sorted and self.sort_is_ascending:
            self.dataframe = self.dataframe.sort_values(col_name, ascending=False, kind="mergesort")
            self.column_sorted = ix
            self.sort_is_ascending = False

        # Clicked a reverse sorted column - reset to the original unsorted order
        elif ix == self.column_sorted:
            unsorted_index = self.dataframe_original[self.dataframe_original.index.isin(self.dataframe.index)].index
            self.dataframe = self.dataframe.reindex(unsorted_index)
            self.column_sorted = None
            self.sort_is_ascending = None

        self.index_sorted = None
        self.update()

    @track_history
    def sort_index(self, ix: int):
        # Clicked an unsorted index level
        if ix != self.index_sorted:
            self.dataframe = self.dataframe.sort_index(level=ix, ascending=True, kind="mergesort")
            self.index_sorted = ix
            self.sort_is_ascending = True

        # Clicked a sorted index level
        elif ix == self.index_sorted and self.sort_is_ascending:
            self.dataframe = self.dataframe.sort_index(level=ix, ascending=False, kind="mergesort")
            self.index_sorted = ix
            self.sort_is_ascending = False

        # Clicked a reverse sorted index level - reset to the original unsorted order
        elif ix == self.index_sorted:
            unsorted_index = self.dataframe_original[self.dataframe_original.index.isin(self.dataframe.index)].index
            self.dataframe.index = unsorted_index

            self.index_sorted = None
            self.sort_is_ascending = None

        self.column_sorted = None
        self.update()

    @track_history
    def add_filter(self, expr: str, enabled=True):
        filt = Filter(expr=expr, enabled=enabled, failed=False)
        self.filters.append(filt)
        self.apply_filters()

    @track_history
    def remove_filter(self, index: int):
        self.filters.pop(index)
        self.apply_filters()

    @track_history
    def edit_filter(self, index: int, expr: str):
        filt = self.filters[index]
        filt.expr = expr
        filt.failed = False
        self.apply_filters()

    @track_history
    def toggle_filter(self, index: int):
        self.filters[index].enabled = not self.filters[index].enabled
        self.apply_filters()

    def apply_filters(self):

        df = self.dataframe_original
        for ix, filt in enumerate(self.filters):
            if filt.enabled and not filt.failed:
                try:
                    df = df.query(filt.expr)
                except Exception as e:
                    self.filters[ix].failed = True
                    logger.exception(e)
        self.dataframe = df
        self.update()

    @staticmethod
    def cast(x: Union["PandasGuiDataFrame", pd.DataFrame, pd.Series]):
        if type(x) == PandasGuiDataFrame:
            return x
        if type(x) == pd.DataFrame:
            return PandasGuiDataFrame(x)
        elif type(x) == pd.Series:
            return PandasGuiDataFrame(pd.DataFrame(x))
        else:
            raise TypeError


@dataclass
class Store:
    settings: Settings = Settings()
    data: List[PandasGuiDataFrame] = field(default_factory=list)

    def add_pgdf(self, pgdf):
        pgdf.settings = self.settings
        self.data.append(pgdf)

    def get_dataframe(self, name):
        return next((x for x in self.data if x.name == name), None)

    def to_dict(self):
        import json
        return json.loads(json.dumps(self, default=lambda o: o.__dict__))
