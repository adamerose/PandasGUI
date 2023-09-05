import logging
import pandas as pd
from PyQt5 import QtWidgets
from typing import List, Union
import sys
import inspect
from collections import OrderedDict

logger = logging.getLogger(__name__)


class DotDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, dct):
        for key, value in dct.items():
            if hasattr(value, "keys"):
                value = DotDict(value)
            self[key] = value


class SlicableOrderedDict(OrderedDict):
    def __getitem__(self, k):
        if not isinstance(k, slice):
            return OrderedDict.__getitem__(self, k)
        x = SlicableOrderedDict()
        for idx, key in enumerate(self.keys()):
            if k.start <= idx < k.stop:
                x[key] = self[key]
        return x


def throttle(wait):
    """
        https://gist.github.com/walkermatt/2871026
        Decorator that will postpone a functions
        execution until after wait seconds
        have elapsed since the last time it was invoked. """
    from threading import Timer
    def decorator(fn):
        def throttled(*args, **kwargs):
            def call_it():
                fn(*args, **kwargs)

            try:
                throttled.t.cancel()
            except(AttributeError):
                pass
            throttled.t = Timer(wait, call_it)
            throttled.t.start()

        return throttled

    return decorator


def as_dict(obj, recurse_list=None):
    # Primitive types
    if not hasattr(obj, "__dict__"):
        return str(obj)

    # Check if object was seen before, otherwise traverse it too
    if recurse_list is None:
        recurse_list = []
    if id(obj) in recurse_list:
        return "*loop detected*"
    else:
        recurse_list.append(id(obj))
        result = {}
        for key, val in obj.__dict__.items():

            if key.startswith("_"):
                continue

            if isinstance(val, list):
                if len(val) == 0:
                    element = str(val)
                else:
                    element = []
                    for item in val:
                        element.append(as_dict(item, recurse_list=recurse_list))
            else:
                element = as_dict(val, recurse_list=recurse_list)
            result[key] = element
        return result


# https://stackoverflow.com/a/47275100/3620725
def fix_pyqt():
    import sys

    sys._excepthook = sys.excepthook

    def my_exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)

    sys.excepthook = my_exception_hook


# This makes it so PyQt5 windows don't become unresponsive in IPython outside app._exec() loops
def fix_ipython():
    from IPython import get_ipython
    ipython = get_ipython()
    if ipython is not None:
        ipython.magic("gui qt5")


def in_interactive_console():
    # https://stackoverflow.com/a/64523765/3620725
    return hasattr(sys, 'ps1')


def flatten_df(df):
    df = df.reset_index()
    df.columns = flatten_multiindex(df.columns)
    return df


def flatten_multiindex(mi, sep=" - ", format=None):
    import pandas as pd

    if issubclass(type(mi), pd.core.indexes.multi.MultiIndex):
        # Flatten multi-index headers
        if format == None:
            # Flatten by putting sep between each header value
            flat_index = [sep.join([str(x) for x in tup]).strip(sep)
                          for tup in mi.values]
        else:
            # Flatten according to the provided format string
            flat_index = []
            for tuple in mi.values:

                placeholders = []
                for name in mi.names:
                    if name is None:
                        name = ""
                    name = "{" + str(name) + "}"
                    placeholders.append(name)

                # Check if index segment contains each placeholder
                if all([item != "" for item in tuple]):
                    # Replace placeholders in format with corresponding values
                    flat_name = format
                    for i, val in enumerate(tuple):  # Iterates over the values in this index segment
                        flat_name = flat_name.replace(placeholders[i], val)
                else:
                    # If the segment doesn't contain all placeholders, just join them with sep instead
                    flat_name = sep.join(tuple).strip(sep)
                flat_index.append(flat_name)
    elif issubclass(type(mi), pd.core.indexes.base.Index):
        return mi
    else:
        raise TypeError(f"Expected Index but got {type(mi)}")

    return flat_index


# Alternative to dataframe.nunique that works when it contains unhashable items
def nunique(df):
    results = {}
    for col in df.columns:
        s = df[col]
        try:
            results[col] = s.nunique()
        except TypeError as e:
            results[col] = s.astype(str).nunique()

    return pd.Series(results)


# Alternative to series.unique that works when it contains unhashable items
def unique(s):
    try:
        return s.unique()
    except TypeError as e:
        return s.astype(str).unique()


def traverse_tree_widget(tree: Union[QtWidgets.QTreeWidget, QtWidgets.QTreeWidgetItem]) -> List[
    QtWidgets.QTreeWidgetItem]:
    if issubclass(type(tree), QtWidgets.QTreeWidget):
        tree = tree.invisibleRootItem()

    items = []
    for i in range(tree.childCount()):
        child = tree.child(i)
        sub_items = traverse_tree_widget(child)
        items += [child]
        items += sub_items

    return items


# Remove all widgets from a PyQt layout
def clear_layout(layout):
    if layout is not None:
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                clear_layout(child.layout())


def unique_name(name, existing_names):
    if name in existing_names:
        for i in range(2, 999):
            new_name = f"{name} ({i})"
            if new_name not in existing_names:
                return new_name
        raise ValueError("Stopped generating unique name after 1000 attempts")
    else:
        return name


# Take a df and rename duplicate columns by appending number suffixes
def rename_duplicates(df):
    import copy
    new_columns = df.columns.values
    suffix = {key: 2 for key in set(new_columns)}
    dup = pd.Series(new_columns).duplicated()

    if type(df.columns) == pd.core.indexes.multi.MultiIndex:
        # Need to be mutable, make it list instead of tuples
        for i in range(len(new_columns)):
            new_columns[i] = list(new_columns[i])
        for ix, item in enumerate(new_columns):
            item_orig = copy.copy(item)
            if dup[ix]:
                for level in range(len(new_columns[ix])):
                    new_columns[ix][level] = new_columns[ix][level] + f"_{suffix[tuple(item_orig)]}"
                suffix[tuple(item_orig)] += 1

        # Convert back from list to tuples now that we're done mutating values
        for i in range(len(new_columns)):
            new_columns[i] = tuple(new_columns[i])

        df.columns = pd.MultiIndex.from_tuples(new_columns)
    # Not a MultiIndex
    else:
        for ix, item in enumerate(new_columns):
            if dup[ix]:
                new_columns[ix] = item + f"_{suffix[item]}"
                suffix[item] += 1
        df.columns = new_columns


def delete_datasets():
    from pandasgui.datasets import LOCAL_DATASET_DIR
    import shutil
    logger.info(f"Deleting sample dataset directory ({LOCAL_DATASET_DIR})")
    shutil.rmtree(LOCAL_DATASET_DIR)


def parse_date(s: pd.Series):
    try:
        return pd.to_datetime(s)
    except:
        return s


# Automatically try to parse dates for all columns
def parse_all_dates(df: Union[pd.DataFrame, pd.Series]):
    # Try to parse all string columns as dates
    if type(df) == pd.DataFrame:
        def parse_dates_if_str(col: pd.Series):
            if (col.dtype == object or col.dtype == pd.StringDtype):
                # Edge case where pd.to_datetime will work but we don't want it to
                if all(col.isna()):
                    return col
                else:
                    return parse_date(col)
            else:
                return col

        return df.apply(parse_dates_if_str)
    elif type(df) == pd.Series:
        return parse_date(df)


def clean_dataframe(df, name="DataFrame"):
    # Remove non-string column names
    converted_names = []
    if issubclass(type(df.columns), pd.core.indexes.multi.MultiIndex):
        levels = df.columns.levels
        for level in levels:
            if any([type(val) != str for val in level]):
                logger.warning(f"In {name}, converted MultiIndex level values to string in: {str(level)}")
                df.columns = df.columns.set_levels([[str(val) for val in level] for level in levels])
                converted_names.append(str(level))
        if converted_names:
            logger.warning(f"In {name}, converted MultiIndex level names to string: {', '.join(converted_names)}")
    else:
        for i, col in enumerate(df.columns):
            if type(col) != str:
                df.rename(columns={col: str(col)}, inplace=True)
                converted_names.append(str(col))
        if converted_names:
            logger.warning(f"In {name}, converted column names to string: {', '.join(converted_names)}")

    # Check for duplicate columns
    if any(df.columns.duplicated()):
        logger.warning(f"In {name}, renamed duplicate columns: {list(set(df.columns[df.columns.duplicated()]))}")
        rename_duplicates(df)

    return df


def test_logging():
    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")


# Resize a widget to a percentage of the screen size
def resize_widget(widget, x, y):
    from PyQt5 import QtCore, QtWidgets
    widget.resize(QtCore.QSize(int(x * QtWidgets.QDesktopWidget().screenGeometry().width()),
                               int(y * QtWidgets.QDesktopWidget().screenGeometry().height())))


def get_kwargs():
    frame = inspect.currentframe().f_back
    keys, _, _, values = inspect.getargvalues(frame)
    kwargs = {}
    for key in keys:
        if key != 'self':
            kwargs[key] = values[key]
    return kwargs


# Flatten nested iterables
def flatten_iter(item):
    t = []
    if type(item) in [list, tuple, set]:
        for sub_item in item:
            t += flatten_iter(sub_item)
    else:
        t.append(item)

    return t


# Make a string from a kwargs dict as they would be displayed when passed to a function
# eg. {'a': 5, 'b': 6} -> a=5, b=6
def kwargs_string(kwargs_dict):
    chunks = []
    for key, val in kwargs_dict.items():
        if isinstance(val, pd.DataFrame):
            chunk = f'{key}={val._pgdf.name}'
        else:
            chunk = f'{key}={repr(val)}'
        chunks.append(chunk)
    return ', '.join(chunks)


def get_function_body(func):
    import inspect
    from itertools import dropwhile
    source_lines = inspect.getsourcelines(func)[0]
    source_lines = dropwhile(lambda x: x.startswith('@'), source_lines)
    line = next(source_lines).strip()
    if not line.startswith('def '):
        return line.rsplit(':')[-1].strip()
    elif not line.endswith(':'):
        for line in source_lines:
            line = line.strip()
            if line.endswith(':'):
                break
    # Handle functions that are not one-liners
    first_line = next(source_lines)
    # Find the indentation of the first line
    indentation = len(first_line) - len(first_line.lstrip())
    return ''.join([first_line[indentation:]] + [line[indentation:] for line in source_lines])


# In North America, Week 1 of any given year is the week which contains January 1st. Weeks span Sunday to Saturday.
def get_week(timestamp):
    from datetime import datetime

    this_jan1 = datetime(timestamp.year, 1, 1)
    next_jan1 = datetime(timestamp.year + 1, 1, 1)
    day_of_year = int(timestamp.strftime('%j'))
    days_until_jan1 = (next_jan1 - timestamp).days

    # Sunday = 0
    def day_of_week(ts):
        return int(ts.strftime('%w'))

    # Check if timestamp is in the same week as next year's January
    if days_until_jan1 <= day_of_week(next_jan1):
        return 1
    else:
        # Week Number = ((Days since start of week 1) / 7) + 1
        return (day_of_year + day_of_week(this_jan1) - 1) // 7 + 1


def get_week_str(ts):
    year = ts.year
    week = get_week(ts)

    if ts.month == 12 and week == 1:
        year += 1

    return "{}W{:02}".format(year, week)


# Rename a variable in a Python expression
def refactor_variable(expr, old_name, new_name):
    import ast
    import astor

    tree = ast.parse(expr)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if node.id == old_name:
                node.id = new_name

    return astor.code_gen.to_source(tree)


def get_figure_type(fig):
    # Plotly
    try:
        import plotly.basedatatypes
        if issubclass(type(fig), plotly.basedatatypes.BaseFigure):
            return "plotly"
    except ModuleNotFoundError:
        pass
    # Matplotlib
    try:
        import matplotlib.axes, matplotlib.figure
        if issubclass(type(fig), matplotlib.axes.Axes) \
                or issubclass(type(fig), matplotlib.figure.Figure):
            return "matplotlib"
    except ModuleNotFoundError:
        pass
    # Bokeh
    try:
        import bokeh.plotting
        if issubclass(type(fig), bokeh.plotting.Figure):
            return "bokeh"
    except ModuleNotFoundError:
        pass
    # Altair
    try:
        import altair.vegalite.v4.api
        if issubclass(type(fig), altair.vegalite.v4.api.Chart):
            return "altair"
    except ModuleNotFoundError:
        pass
    return None


# Take the text entered for a DataFrame cell and parse it into an appropriate type for the column
def parse_cell(text, column_dtype):
    import numpy as np
    if text == "":
        return np.nan

    if column_dtype == str:
        return text

    # Parse text using same logic as reading a CSV file by using a file buffer
    try:
        from io import StringIO
        import pandas as pd
        value = pd.read_csv(StringIO(text), dtype=column_dtype, header=None).values[0][0]
        return value
    except ValueError:
        raise ValueError(f"Could not convert {repr(text)} to type {column_dtype}")


value = parse_cell('nan', str)


def summarize_json(data, terse=True):
    from collections import defaultdict

    if len(data) == 0:
        print(f"Data is an empty {type(data).__name__}")
        return

    def list_keys(data, parent_key='ROOT'):
        parent_key = parent_key.strip('.')
        keys = []
        if isinstance(data, list):
            parent_subkeys = parent_key.split(".")
            for item in data:
                keys += list_keys(item, f'{".".join(parent_subkeys[:-1])}.[{parent_subkeys[-1]}]')
        elif isinstance(data, dict):
            for key, item in data.items():
                keys += list_keys(item, f'{parent_key}.{key}')
        else:
            return [f'{parent_key} - {type(data).__name__}']

        return keys

    keycount = defaultdict(lambda: 0)

    for key in reversed(sorted(list_keys(data))):
        keycount[key] += 1

    summary = ""

    width = max([len(str(count)) for count in keycount.values()])
    redundant_subkeys = set()
    for key, count in keycount.items():
        if terse:
            line = f"{count: <{width}} {key}"

            for redundant_subkey in sorted(list(redundant_subkeys), key=len, reverse=True):
                line = line.replace(redundant_subkey, ' ' * len(redundant_subkey))

            for i in range(line.count('.')):
                subkey = '.'.join(key.split('.')[:-1 - i])
                redundant_subkeys.add(subkey)
        else:
            line = f"{count: <{width}} {key}"

        summary += line + "\n"

    return summary


# Given two lists find pairs (src, dest) such that moving values in A according to each pair gives B
def get_movements(a: list, b: list):
    assert set(a) == set(b)

    from copy import copy
    a = copy(a)

    movements = []
    for dest, letter in enumerate(b):
        src = a.index(letter)
        if src != 0:
            movements.append((src + dest, dest))
        a.pop(src)
    return movements


event_lookup = {"0": "QEvent::None",
                "114": "QEvent::ActionAdded",
                "113": "QEvent::ActionChanged",
                "115": "QEvent::ActionRemoved",
                "99": "QEvent::ActivationChange",
                "121": "QEvent::ApplicationActivate",
                "122": "QEvent::ApplicationDeactivate",
                "36": "QEvent::ApplicationFontChange",
                "37": "QEvent::ApplicationLayoutDirectionChange",
                "38": "QEvent::ApplicationPaletteChange",
                "214": "QEvent::ApplicationStateChange",
                "35": "QEvent::ApplicationWindowIconChange",
                "68": "QEvent::ChildAdded",
                "69": "QEvent::ChildPolished",
                "71": "QEvent::ChildRemoved",
                "40": "QEvent::Clipboard",
                "19": "QEvent::Close",
                "200": "QEvent::CloseSoftwareInputPanel",
                "178": "QEvent::ContentsRectChange",
                "82": "QEvent::ContextMenu",
                "183": "QEvent::CursorChange",
                "52": "QEvent::DeferredDelete",
                "60": "QEvent::DragEnter",
                "62": "QEvent::DragLeave",
                "61": "QEvent::DragMove",
                "63": "QEvent::Drop",
                "170": "QEvent::DynamicPropertyChange",
                "98": "QEvent::EnabledChange",
                "10": "QEvent::Enter",
                "150": "QEvent::EnterEditFocus",
                "124": "QEvent::EnterWhatsThisMode",
                "206": "QEvent::Expose",
                "116": "QEvent::FileOpen",
                "8": "QEvent::FocusIn",
                "9": "QEvent::FocusOut",
                "23": "QEvent::FocusAboutToChange",
                "97": "QEvent::FontChange",
                "198": "QEvent::Gesture",
                "202": "QEvent::GestureOverride",
                "188": "QEvent::GrabKeyboard",
                "186": "QEvent::GrabMouse",
                "159": "QEvent::GraphicsSceneContextMenu",
                "164": "QEvent::GraphicsSceneDragEnter",
                "166": "QEvent::GraphicsSceneDragLeave",
                "165": "QEvent::GraphicsSceneDragMove",
                "167": "QEvent::GraphicsSceneDrop",
                "163": "QEvent::GraphicsSceneHelp",
                "160": "QEvent::GraphicsSceneHoverEnter",
                "162": "QEvent::GraphicsSceneHoverLeave",
                "161": "QEvent::GraphicsSceneHoverMove",
                "158": "QEvent::GraphicsSceneMouseDoubleClick",
                "155": "QEvent::GraphicsSceneMouseMove",
                "156": "QEvent::GraphicsSceneMousePress",
                "157": "QEvent::GraphicsSceneMouseRelease",
                "182": "QEvent::GraphicsSceneMove",
                "181": "QEvent::GraphicsSceneResize",
                "168": "QEvent::GraphicsSceneWheel",
                "18": "QEvent::Hide",
                "27": "QEvent::HideToParent",
                "127": "QEvent::HoverEnter",
                "128": "QEvent::HoverLeave",
                "129": "QEvent::HoverMove",
                "96": "QEvent::IconDrag",
                "101": "QEvent::IconTextChange",
                "83": "QEvent::InputMethod",
                "207": "QEvent::InputMethodQuery",
                "169": "QEvent::KeyboardLayoutChange",
                "6": "QEvent::KeyPress",
                "7": "QEvent::KeyRelease",
                "89": "QEvent::LanguageChange",
                "90": "QEvent::LayoutDirectionChange",
                "76": "QEvent::LayoutRequest",
                "11": "QEvent::Leave",
                "151": "QEvent::LeaveEditFocus",
                "125": "QEvent::LeaveWhatsThisMode",
                "88": "QEvent::LocaleChange",
                "176": "QEvent::NonClientAreaMouseButtonDblClick",
                "174": "QEvent::NonClientAreaMouseButtonPress",
                "175": "QEvent::NonClientAreaMouseButtonRelease",
                "173": "QEvent::NonClientAreaMouseMove",
                "177": "QEvent::MacSizeChange",
                "43": "QEvent::MetaCall",
                "102": "QEvent::ModifiedChange",
                "4": "QEvent::MouseButtonDblClick",
                "2": "QEvent::MouseButtonPress",
                "3": "QEvent::MouseButtonRelease",
                "5": "QEvent::MouseMove",
                "109": "QEvent::MouseTrackingChange",
                "13": "QEvent::Move",
                "197": "QEvent::NativeGesture",
                "208": "QEvent::OrientationChange",
                "12": "QEvent::Paint",
                "39": "QEvent::PaletteChange",
                "131": "QEvent::ParentAboutToChange",
                "21": "QEvent::ParentChange",
                "212": "QEvent::PlatformPanel",
                "217": "QEvent::PlatformSurface",
                "75": "QEvent::Polish",
                "74": "QEvent::PolishRequest",
                "123": "QEvent::QueryWhatsThis",
                "106": "QEvent::ReadOnlyChange",
                "199": "QEvent::RequestSoftwareInputPanel",
                "14": "QEvent::Resize",
                "204": "QEvent::ScrollPrepare",
                "205": "QEvent::Scroll",
                "117": "QEvent::Shortcut",
                "51": "QEvent::ShortcutOverride",
                "17": "QEvent::Show",
                "26": "QEvent::ShowToParent",
                "50": "QEvent::SockAct",
                "192": "QEvent::StateMachineSignal",
                "193": "QEvent::StateMachineWrapped",
                "112": "QEvent::StatusTip",
                "100": "QEvent::StyleChange",
                "87": "QEvent::TabletMove",
                "92": "QEvent::TabletPress",
                "93": "QEvent::TabletRelease",
                "171": "QEvent::TabletEnterProximity",
                "172": "QEvent::TabletLeaveProximity",
                "219": "QEvent::TabletTrackingChange",
                "22": "QEvent::ThreadChange",
                "1": "QEvent::Timer",
                "120": "QEvent::ToolBarChange",
                "110": "QEvent::ToolTip",
                "184": "QEvent::ToolTipChange",
                "194": "QEvent::TouchBegin",
                "209": "QEvent::TouchCancel",
                "196": "QEvent::TouchEnd",
                "195": "QEvent::TouchUpdate",
                "189": "QEvent::UngrabKeyboard",
                "187": "QEvent::UngrabMouse",
                "78": "QEvent::UpdateLater",
                "77": "QEvent::UpdateRequest",
                "111": "QEvent::WhatsThis",
                "118": "QEvent::WhatsThisClicked",
                "31": "QEvent::Wheel",
                "132": "QEvent::WinEventAct",
                "24": "QEvent::WindowActivate",
                "103": "QEvent::WindowBlocked",
                "25": "QEvent::WindowDeactivate",
                "34": "QEvent::WindowIconChange",
                "105": "QEvent::WindowStateChange",
                "33": "QEvent::WindowTitleChange",
                "104": "QEvent::WindowUnblocked",
                "203": "QEvent::WinIdChange",
                "126": "QEvent::ZOrderChange", }
