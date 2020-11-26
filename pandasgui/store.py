from dataclasses import dataclass, field, asdict
from typing import Dict, List, Union, Iterable
import pandas as pd
from pandas import DataFrame
from PyQt5 import QtCore, QtGui, QtWidgets, sip
from PyQt5.QtCore import Qt
import traceback
from functools import wraps
from datetime import datetime
from pandasgui.utility import unique_name, in_interactive_console, rename_duplicates
from pandasgui.constants import LOCAL_DATA_DIR
import os
import collections
from enum import Enum
import json

import logging

logger = logging.getLogger(__name__)

# JSON file that stores persistent user preferences
preferences_path = os.path.join(LOCAL_DATA_DIR, 'preferences.json')
if not os.path.exists(preferences_path):
    with open(preferences_path, 'w') as f:
        json.dump({'theme': "light"}, f)

with open(preferences_path) as f:
    preferences = json.load(f)


class DictLike:
    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)


class Setting(DictLike):
    def __init__(self, label, value, description, dtype, persist):
        self.label: str = label
        self.value: any = value
        self.description: str = description
        self.dtype: Union[type(str), type(bool), Enum] = dtype
        self.persist: bool = persist

    def __setattr__(self, key, value):
        try:
            if self.persist:
                preferences[self.label] = value
                with open(preferences_path, 'w') as f:
                    json.dump(preferences, f)
        except AttributeError:
            # Get attribute error because of __setattr__ happening in __init__ before self.persist is set
            pass

        super().__setattr__(key, value)


class Settings(DictLike):
    def __init__(self, editable=False, style="Fusion", block=None, theme=preferences['theme']):
        if block is None:
            if in_interactive_console():
                # Don't block if in an interactive console (so you can view GUI and still continue running commands)
                block = False
            else:
                # If in a script, we need to block or the script will continue and finish without allowing GUI interaction
                block = True

        self.block = Setting(label="block",
                             value=block,
                             description="Should GUI block code execution until closed?",
                             dtype=bool,
                             persist=False)

        self.editable = Setting(label="editable",
                                value=editable,
                                description="Are table cells editable?",
                                dtype=bool,
                                persist=False)

        self.style = Setting(label="style",
                             value=style,
                             description="PyQt app style",
                             dtype=Enum("StylesEnum", QtWidgets.QStyleFactory.keys()),
                             persist=False)

        self.theme = Setting(label="theme",
                             value=theme,
                             description="UI theme",
                             dtype=str,
                             persist=True)


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
    def wrapper(pgdf, *args, **kwargs):
        history_item = HistoryItem(name=func.__name__,
                                   args=args,
                                   kwargs=kwargs,
                                   time=datetime.now().strftime("%H:%M:%S"))
        pgdf.history.append(history_item)

        return func(pgdf, *args, **kwargs)

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
        self.store: Union[Store, None] = None
        self.dataframe_explorer: Union["DataFrameExplorer", None] = None
        self.dataframe_viewer: Union["DataFrameViewer", None] = None
        self.filter_viewer: Union["FilterViewer", None] = None

        self.column_sorted: Union[int, None] = None
        self.index_sorted: Union[int, None] = None
        self.sort_is_ascending: Union[bool, None] = None

        self.filters: List[Filter] = []

    # Refresh PyQt models when the underlying pgdf is changed in anyway that needs to be reflected in the GUI
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

        for view in [self.dataframe_viewer.columnHeader,
                     self.dataframe_viewer.indexHeader]:
            view.set_spans()

    @track_history
    def edit_data(self, row, col, value, skip_update=False):
        # Not using iat here because it won't work with MultiIndex
        self.dataframe_original.at[self.dataframe.index[row], self.dataframe.columns[col]] = value
        if not skip_update:
            self.apply_filters()
            self.update()

    @track_history
    def paste_data(self, top_row, left_col, df_to_paste):
        # Not using iat here because it won't work with MultiIndex
        for i in range(df_to_paste.shape[0]):
            for j in range(df_to_paste.shape[1]):
                value = df_to_paste.iloc[i, j]
                self.edit_data(top_row + i, left_col + j, value, skip_update=True)

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
            self.dataframe = self.dataframe.reindex(unsorted_index)

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
    def cast(x: Union["PandasGuiDataFrame", pd.DataFrame, pd.Series, Iterable]):
        if isinstance(x, PandasGuiDataFrame):
            return x
        if isinstance(x, pd.DataFrame):
            return PandasGuiDataFrame(x)
        elif isinstance(x, pd.Series):
            return PandasGuiDataFrame(x.to_frame())
        else:
            try:
                return PandasGuiDataFrame(pd.DataFrame(x))
            except:
                raise TypeError(f"Could not convert {type(x)} to DataFrame")


@dataclass
class Store:
    settings: Union["Settings", None] = None
    data: List[PandasGuiDataFrame] = field(default_factory=list)
    gui: Union["PandasGui", None] = None
    navigator: Union["Navigator", None] = None
    selected_pgdf: Union[PandasGuiDataFrame, None] = None

    def __post_init__(self):
        self.settings = Settings()

    def add_dataframe(self, pgdf: Union[DataFrame, PandasGuiDataFrame],
                      name: str = "Untitled"):

        # Check for duplicate columns
        if type(pgdf) == DataFrame:
            df = pgdf
        else:
            df = pgdf.dataframe
        if any(df.columns.duplicated()):
            logger.warning(f"Renamed duplicate column names in {name}: {list(set(df.columns[df.columns.duplicated()]))}")
            rename_duplicates(df)


        name = unique_name(name, self.get_dataframes().keys())
        pgdf = PandasGuiDataFrame.cast(pgdf)
        pgdf.settings = self.settings
        pgdf.name = name
        pgdf.store = self

        self.data.append(pgdf)

        if pgdf.dataframe_explorer is None:
            from pandasgui.widgets.dataframe_explorer import DataFrameExplorer
            pgdf.dataframe_explorer = DataFrameExplorer(pgdf)
        dfe = pgdf.dataframe_explorer
        self.gui.stacked_widget.addWidget(dfe)

        # Add to nav
        shape = pgdf.dataframe.shape
        shape = str(shape[0]) + " X " + str(shape[1])

        item = QtWidgets.QTreeWidgetItem(self.navigator, [name, shape])
        self.navigator.itemSelectionChanged.emit()
        self.navigator.setCurrentItem(item)
        self.navigator.apply_tree_settings()

    def import_file(self, path):
        if not os.path.isfile(path):
            logger.warning("Path is not a file: " + path)
        elif path.endswith(".csv"):
            filename = os.path.split(path)[1].split('.csv')[0]
            df = pd.read_csv(path, engine='python')
            self.add_dataframe(df, filename)
        elif path.endswith(".xlsx"):
            filename = os.path.split(path)[1].split('.csv')[0]
            df_dict = pd.read_excel(path, sheet_name=None)
            for sheet_name in df_dict.keys():
                df_name = f"{filename} - {sheet_name}"
                self.add_dataframe(df_dict[sheet_name], df_name)
        else:
            logger.warning("Can only import csv / xlsx. Invalid file: " + path)

    def get_pgdf(self, name):
        return next((x for x in self.data if x.name == name), None)

    def get_dataframes(self, names: Union[None, str, list] = None):
        if type(names) == str:
            names = [names]

        df_dict = {}
        for pgdf in self.data:
            if names is None or pgdf.name in names:
                df_dict[pgdf.name] = pgdf.dataframe

        return df_dict

    def select_pgdf(self, name):
        pgdf = self.get_pgdf(name)
        dfe = pgdf.dataframe_explorer
        self.gui.stacked_widget.setCurrentWidget(dfe)
        self.selected_pgdf = pgdf

    def to_dict(self):
        import json
        return json.loads(json.dumps(self, default=lambda o: o.__dict__))
