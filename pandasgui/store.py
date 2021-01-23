import textwrap
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Union, Iterable
import pandas as pd
from pandas import DataFrame
from PyQt5 import QtCore, QtGui, QtWidgets, sip
from PyQt5.QtCore import Qt
import traceback
from functools import wraps
from datetime import datetime
from pandasgui.utility import unique_name, in_interactive_console, rename_duplicates, autolog
from pandasgui.constants import LOCAL_DATA_DIR
import os
import collections
from enum import Enum
import json
import inspect
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
    func: callable
    args: tuple
    kwargs: dict
    time: str
    code: str

    def __init__(self, name, func, args, kwargs, time=None, code=""):
        if time is None:
            time = datetime.now().strftime("%H:%M:%S")

        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.time = time
        self.code = code


def track_history(func):
    """
    This keeps track of all actions that modify the DataFrames and other important actions like plotting.
    Any functions that modify the DataFrame
    """

    @wraps(func)
    def tracked_func(pgdf, *args, **kwargs):
        history_item = HistoryItem(name=func.__name__,
                                   func=func,
                                   args=args,
                                   kwargs=kwargs)

        pgdf.add_history_item(history_item)

        pgdf.current_history_item = history_item
        return_val = func(pgdf, *args, **kwargs)
        pgdf.current_history_item = None

        return return_val

    return tracked_func


class PandasGuiDataFrame:
    """
    All methods that modify the data should modify self.df_unfiltered, then self.df gets computed from that
    """

    def __init__(self, df: DataFrame, name: str = 'Untitled'):
        super().__init__()
        df = df.copy()

        self.df: DataFrame = df
        self.df_unfiltered: DataFrame = df
        self.name = name

        self.history: List[HistoryItem] = []
        self.history_imports: List[str] = ["import pandas as pd"]

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
        self.filtered_index_map = df.reset_index().index

    ###################################
    # Code history

    def code_export(self):
        code_history = ""

        # Add line to define df
        code_history += inspect.cleandoc(f"""
                # 'df' refers to the DataFrame passed into 'pandasgui.show'. Omit the line below if it is already defined.
                import pandas as pd
                from numpy import nan
                df = pd.DataFrame({self.df_unfiltered.to_dict()})
                """) + '\n\n'

        # Add imports to setup
        code_history += '\n'.join(self.history_imports) + '\n\n'

        for history_item in self.history:
            code_history += history_item.code
            code_history += "\n\n"

        if any([filt.enabled for filt in self.filters]):
            code_history += f"# Filters\n"
        for filt in self.filters:
            if filt.enabled:
                code_history += f"df = df.query('{filt.expr}')\n"

        return code_history

    def add_history_item(self, history_item):

        name = history_item.name
        func = history_item.func
        args = history_item.args
        kwargs = history_item.kwargs

        self.history.append(history_item)
        # Convert args to kwargs. The [1:] is to ignore the self argument
        arg_names = inspect.getfullargspec(func).args[1:]
        fake_kwargs = {key: val for key, val in zip(arg_names, args)}
        full_kwargs = {**fake_kwargs, **kwargs}

        # Don't want full formatted table of the DataFrame appearing in code history args
        for key, val in full_kwargs.items():
            if type(val) == pd.DataFrame:
                full_kwargs[key] = f"pd.DataFrame({val.to_dict()})"

        kwargs_string = ', '.join(arg_names)

        # Add lines defining the values of the args
        history_item.code += f"# {func.__name__}({kwargs_string})\n"
        for key, val in full_kwargs.items():
            history_item.code += f"{key} = {val}\n"

    def add_code(self, string, history_item=None):
        if not history_item:
            try:
                history_item = self.current_history_item
            except AttributeError:
                raise ValueError("add_code must be passed a HistoryItem if called from outside a pgdf method")

        history_item.code += string + "\n"

    ###################################
    # Editing cell data

    @track_history
    def edit_data(self, row, col, value):
        # Map the row number in the filtered df (which the user interacts with) to the unfiltered one
        row = self.filtered_index_map[row]

        self.df_unfiltered.iat[row, col] = value
        self.apply_filters()

        self.add_code(f"df.iat[row, col] = value")

    @track_history
    def paste_data(self, top_row, left_col, df_to_paste):
        # Not using iat here because it won't work with MultiIndex
        for i in range(df_to_paste.shape[0]):
            for j in range(df_to_paste.shape[1]):
                value = df_to_paste.iloc[i, j]
                self.df_unfiltered.at[self.df.index[top_row + i],
                                      self.df.columns[left_col + j]] = value
        self.apply_filters()

        self.add_code(inspect.cleandoc(f"""
            for i in range(df_to_paste.shape[0]):
                for j in range(df_to_paste.shape[1]):
                    value = df_to_paste.iloc[i, j]
                    df.at[df.index[top_row + i],
                          df.columns[left_col + j]] = value
            """))

    ###################################
    # Sorting

    @track_history
    def sort_column(self, ix: int):
        col_name = self.df_unfiltered.columns[ix]

        # Clicked an unsorted column
        if ix != self.column_sorted:
            self.df_unfiltered = self.df_unfiltered.sort_values(col_name, ascending=True, kind='mergesort')
            self.column_sorted = ix
            self.sort_is_ascending = True

            self.add_code("df = df.sort_values(df.columns[ix], ascending=True, kind='mergesort')")

        # Clicked a sorted column
        elif ix == self.column_sorted and self.sort_is_ascending:
            self.df_unfiltered = self.df_unfiltered.sort_values(col_name, ascending=False, kind='mergesort')
            self.column_sorted = ix
            self.sort_is_ascending = False

            self.add_code("df = df.sort_values(df.columns[ix], ascending=False, kind='mergesort')")

        # Clicked a reverse sorted column - reset to sorted by index
        elif ix == self.column_sorted:
            self.df_unfiltered = self.df_unfiltered.sort_index(ascending=True, kind='mergesort')
            self.column_sorted = None
            self.sort_is_ascending = None

            self.add_code("df = df.sort_index(ascending=True, kind='mergesort')")

        self.index_sorted = None
        self.apply_filters()

    @track_history
    def sort_index(self, ix: int):
        # Clicked an unsorted index level
        if ix != self.index_sorted:
            self.df_unfiltered = self.df_unfiltered.sort_index(level=ix, ascending=True, kind='mergesort')
            self.index_sorted = ix
            self.sort_is_ascending = True

            self.add_code("df = df.sort_index(level=ix, ascending=True, kind='mergesort')")

        # Clicked a sorted index level
        elif ix == self.index_sorted and self.sort_is_ascending:
            self.df_unfiltered = self.df_unfiltered.sort_index(level=ix, ascending=False, kind='mergesort')
            self.index_sorted = ix
            self.sort_is_ascending = False

            self.add_code("df = df.sort_index(level=ix, ascending=False, kind='mergesort')")

        # Clicked a reverse sorted index level - reset to sorted by full index
        elif ix == self.index_sorted:
            self.df_unfiltered = self.df_unfiltered.sort_index(ascending=True, kind='mergesort')

            self.index_sorted = None
            self.sort_is_ascending = None

            self.add_code("df = df.sort_index(ascending=True, kind='mergesort')")

        self.column_sorted = None
        self.apply_filters()

    ###################################
    # Filters

    def any_filtered(self):
        return any(filt.enabled for filt in self.filters)

    def add_filter(self, expr: str, enabled=True):
        filt = Filter(expr=expr, enabled=enabled, failed=False)
        self.filters.append(filt)
        self.apply_filters()

    def remove_filter(self, index: int):
        self.filters.pop(index)
        self.apply_filters()

    def edit_filter(self, index: int, expr: str):
        filt = self.filters[index]
        filt.expr = expr
        filt.failed = False
        self.apply_filters()

    def toggle_filter(self, index: int):
        self.filters[index].enabled = not self.filters[index].enabled
        self.apply_filters()

    def apply_filters(self):
        df = self.df_unfiltered.copy()
        df['_temp_range_index'] = df.reset_index().index

        for ix, filt in enumerate(self.filters):
            if filt.enabled and not filt.failed:
                try:
                    df = df.query(filt.expr)
                except Exception as e:
                    self.filters[ix].failed = True
                    logger.exception(e)

        self.filtered_index_map = df['_temp_range_index'].reset_index(drop=True)
        df = df.drop('_temp_range_index', axis=1)

        self.df = df
        self.update()

    # def apply_sorting(self):
    #     if self.index_sorted is not None:
    #         self.df = self.df.sort_index(level=self.index_sorted, ascending=self.sort_is_ascending, kind='mergesort')
    #     if self.column_sorted is not None:
    #         self.df = self.df.sort_values(self.df.columns[self.column_sorted], ascending=self.sort_is_ascending,
    #                                       kind='mergesort')
    #     self.apply_filters()

    ###################################
    # Other

    # Refresh PyQt models when the underlying pgdf is changed in anyway that needs to be reflected in the GUI
    def update(self):
        self.models = []
        if self.dataframe_viewer is not None:
            self.models += [self.dataframe_viewer.dataView.model(),
                       self.dataframe_viewer.columnHeader.model(),
                       self.dataframe_viewer.indexHeader.model(),
                       self.dataframe_viewer.columnHeaderNames.model(),
                       self.dataframe_viewer.indexHeaderNames.model(),
                       ]

        if self.filter_viewer is not None:
            self.models += [self.filter_viewer.list_model,
                       ]
        for model in self.models:
            model.beginResetModel()
            model.endResetModel()

        for view in [self.dataframe_viewer.columnHeader,
                     self.dataframe_viewer.indexHeader]:
            view.set_spans()

        for view in [self.dataframe_viewer.columnHeader,
                     self.dataframe_viewer.indexHeader,
                     self.dataframe_viewer.dataView]:
            view.updateGeometry()

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

        name = unique_name(name, self.get_dataframes().keys())
        pgdf = PandasGuiDataFrame.cast(pgdf)
        pgdf.settings = self.settings
        pgdf.name = name
        pgdf.store = self

        df = pgdf.df

        # Remove non-string column names
        if issubclass(type(df.columns), pd.core.indexes.multi.MultiIndex):
            levels = df.columns.levels
            for level in levels:
                if any([type(val) != str for val in level]):
                    logger.warning(f"In {name}, converted MultiIndex level values to string in: {str(level)}")
                    df.columns = df.columns.set_levels([[str(val) for val in level] for level in levels])
        else:
            for i, col in enumerate(df.columns):
                if type(col) != str:
                    logger.warning(f"In {name}, converted column name to string: {str(col)}")
                    df.rename(columns={col: str(col)}, inplace=True)

        # Check for duplicate columns
        if any(df.columns.duplicated()):
            logger.warning(f"In {name}, renamed duplicate columns: {list(set(df.columns[df.columns.duplicated()]))}")
            rename_duplicates(df)

        self.data.append(pgdf)

        if pgdf.dataframe_explorer is None:
            from pandasgui.widgets.dataframe_explorer import DataFrameExplorer
            pgdf.dataframe_explorer = DataFrameExplorer(pgdf)
        dfe = pgdf.dataframe_explorer
        self.gui.stacked_widget.addWidget(dfe)

        # Add to nav
        shape = pgdf.df.shape
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
            for pgdf in self.data:
                if names == pgdf.name:
                    return pgdf.df

        df_dict = {}
        for pgdf in self.data:
            if names is None or pgdf.name in names:
                df_dict[pgdf.name] = pgdf.df

        return df_dict

    def select_pgdf(self, name):
        pgdf = self.get_pgdf(name)
        dfe = pgdf.dataframe_explorer
        self.gui.stacked_widget.setCurrentWidget(dfe)
        self.selected_pgdf = pgdf

    def to_dict(self):
        import json
        return json.loads(json.dumps(self, default=lambda o: o.__dict__))
