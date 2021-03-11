from collections import defaultdict
import datetime
import logging
import pandas as pd
from PyQt5 import QtWidgets
from typing import List, Union
import sys
import inspect

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


# Automatically try to parse dates for all columns
def parse_dates(df: Union[pd.DataFrame, pd.Series]):
    def parse_dates_series(s: pd.Series):
        try:
            return pd.to_datetime(s)
        except:
            return s

    if type(df) == pd.DataFrame:
        return df.apply(lambda col: parse_dates_series(col) if col.dtype == object else col)
    elif type(df) == pd.Series:
        return parse_dates_series(df)


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

    # Convert columns to datetime where possible
    converted_names = []
    dtypes_old = df.dtypes
    df = parse_dates(df)
    dtypes_new = df.dtypes
    for col_name in [df.columns[ix] for ix in range(len(dtypes_new)) if dtypes_old[ix] != dtypes_new[ix]]:
        converted_names.append(str(col_name))
    if converted_names:
        logger.warning(f"In {name}, converted columns to datetime: {', '.join(converted_names)}")

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


def active_filters_repr(filters):
    "string representation of active filter expressions"
    return ','.join([filter.expr for filter in filters if filter.enabled and filter.failed == False])


def remove_units(label):
    "we do not want to repeat units in the title. It is assumed they are in parenthesis"
    if type(label) == list and len(label) == 0:
        return label
    elif type(label) == list and len(label) == 1:
        return remove_units(label[0])
    elif type(label) == list and len(label) > 1:
        return [remove_units(val) for val in label]
    try:
        return label[:label.rindex("(")] if label[-1] == ")" else label
    except (AttributeError, IndexError, TypeError, ValueError):
        return label


def axis_title_labels(kwargs):
    "handling of x, y, z and dimentsions, columns / orientation and log scales for all charts"
    orientation = kwargs.get("orientation")
    log_x = kwargs.get("log_x", False)
    log_y = kwargs.get("log_y", False)
    log_z = kwargs.get("log_z", False)

    title_log_x = "log " if log_x else ""
    title_log_y = "log " if log_y else ""
    title_log_z = "log " if log_z else ""

    x = remove_units(kwargs.get("x"))
    y = remove_units(kwargs.get("y", ""))
    z = remove_units(kwargs.get("z", ""))
    dimensions = remove_units(kwargs.get("dimensions", ""))
    columns = remove_units(kwargs.get("columns", ""))

    if orientation == "h":
        x, y = y, x
        title_log_x, title_log_y = title_log_y, title_log_x
    if x is None:
        opt_x = x  # wordcloud, pie etc have no x
    elif type(x) == list:
        opt_x = [title_log_x + val for val in x]
    else:
        opt_x = title_log_x + x
    if type(y) == list:
        opt_y = [title_log_y + val for val in y]
    else:
        opt_y = title_log_y + y
    return opt_x, opt_y, title_log_z + z, dimensions, columns


def eval_title(pgdf, current_schema, kwargs):
    """template variable replacement.

    Besides all dragger selections (x, y, z, color etc), and all custom kwargs, extra template variables are:

          date: current datetime
          filters: active filter expressions, comma delimited
          title_x: x minus units and with log scale if selected
          title_y: y minus units and with log scale if selected
          title_z: z minus units and with log scale if selected
          title_dimensions: dimensions list minus units
          title_columns: columns list minus units
          title_trendline: trendline description
          vs: when doing a title with x vs y, use {x}{vs}{y}
          over_by: when doing a title y over x, use {y}{over_by}{x}. Preferred. for distributions, will use "by"
          name: dataframe name
          total: total number of observations
          subset: observations with active filters applied
          selection: ready to use string representing {subset} observations of {total}
          groupings: groupings tied to Legend and not on legend: marker_symbol, line_group, size etc
    """
    today = datetime.datetime.now()
    name = pgdf.name
    chart = current_schema.name
    x, y, z, dimensions, columns = axis_title_labels(kwargs)

    # Histograms default to count for aggregation
    histfunc = ""
    over_by = " over "
    vs = " vs "
    color = kwargs.get("color")
    symbol = kwargs.get("symbol")
    apply_mean = kwargs.get("apply_mean", None)
    apply_sort = kwargs.get("apply_sort", None)
    title_trendline = kwargs.get("trendline", "")
    if title_trendline != "":
        title_trendline = f"trend lines are <i>{title_trendline}</i>"

    if chart == "histogram":
        histfunc = kwargs.get("histfunc", "sum" if y else "count")
        if x is None and y:
            y = f"{y} {histfunc}"
    elif chart in ("box", "violin"):
        histfunc = "distribution"
        over_by = " by "
        if x is None and y:
            y = f"{y} {histfunc}"
    elif chart == "bar":
        over_by = " by "
        if y == "":
            y = "count"
            if color is None and apply_mean:
                over_by = " of "
        else:
            if apply_mean:
                func = "average"
            else:
                func = "sum"
            y = f"{func} of {y}"
        if apply_sort:
            if x:
                x = f"sorted {x}"
    elif chart == "density_heatmap":
        histfunc = kwargs.get("histfunc", "sum")
        if y and z:
            y, z = f"binned {histfunc} of {z} for ", y
        elif y:
            y = f"binned count of {y}"
        histfunc = ""
    elif chart == "density_contour":
        histfunc = kwargs.get("histfunc", "count")
        estimation = "estimated density "
        if y and z:
            y, z = f"estimated {histfunc} density of {z} for ", y
        elif y:
            y = f"estimated count density of {y}"
        histfunc = ""
    elif chart == "scatter_3d":
        if y and z:
            # need to separate them
            z = ", " + z
    elif chart in ("word_cloud", "scatter_matrix", "pie"):
        x = ""  # else string will evaluate to None
    elif chart == "line":
        if kwargs.get("apply_mean", None):
            over_by = " by "
            if y:
                y = f"average of {y}"
        if kwargs.get("apply_sort", None):
            if x:
                x = f"sorted {x}"

    # filters
    filters = active_filters_repr(pgdf.filters)
    if filters != "":
        filters = "Filters: " + filters
    total = pgdf.df_unfiltered.shape[0]

    subset = pgdf.df.shape[0]
    selection = ""
    groupings = ""
    sep = ""
    showlegend = kwargs.get("showlegend", True)

    # over / by
    over_by = f" {histfunc}{over_by}" if x else ""
    vs = f"{vs} {histfunc}" if y else ""

    # Groupings in Legend
    if color or symbol:
        if showlegend:
            groupings += "Legend"
        else:
            if color:
                groupings += f"{sep}color={color}"
                sep = ", "
            if symbol:
                groupings += f"{sep}symbol={symbol}"
        sep = ", "

    # this one shows on the legend, but is not labeled
    if kwargs.get("marker_symbol"):
        groupings += f"{sep}marker={kwargs['marker_symbol']}"

    # next two don't show in the plotly legend, so we need to explicitly add them
    if "line_group" in kwargs.keys():
        groupings += f"{sep}line_group={kwargs['line_group']}"
    if "size" in kwargs.keys():
        groupings += f"{sep}size={kwargs['size']}"
    if "text" in kwargs.keys():
        groupings += f"{sep}text={kwargs['text']}"
    if groupings != "":
        groupings = "Grouped by " + groupings
        if filters != "":
            groupings += " - "

    if subset != total:
        selection = f"({subset} obs. of {total}) "
    elif kwargs.get("apply_mean", None):
        selection = "({groupby_obs} " + f"derived obs. from {total})"
    else:
        selection = f"({total} obs.)" if chart == "line" else "(all observations)"

    return kwargs["title"].format_map(defaultdict(str,
                                                  date=today,
                                                  filters=filters,
                                                  title_x=x,
                                                  title_y=y,
                                                  title_z=z,
                                                  title_dimensions=dimensions,
                                                  title_columns=columns,
                                                  title_trendline=title_trendline,
                                                  vs=vs,
                                                  over_by=over_by,
                                                  name=name,
                                                  total=total,
                                                  subset=subset,
                                                  selection=selection,
                                                  groupings=groupings,
                                                  **kwargs))


# Make a string from a kwargs dict as they would be displayed when passed to a function
# eg. {'a': 5, 'b': 6} -> a=5, b=6
def kwargs_string(kwargs_dict):
    return ', '.join([f'{key}={repr(val)}' for key, val in kwargs_dict.items()])


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
    try:
        import plotly
        if issubclass(type(fig), plotly.basedatatypes.BaseFigure):
            return "plotly"
    except ModuleNotFoundError:
        pass

    try:
        import matplotlib.axes, matplotlib.figure
        if issubclass(type(fig), matplotlib.axes.Axes) \
                or issubclass(type(fig), matplotlib.figure.Figure):
            return "matplotlib"
    except ModuleNotFoundError:
        pass

    try:
        import bokeh.plotting
        if issubclass(type(fig), bokeh.plotting.Figure):
            return "bokeh"
    except ModuleNotFoundError:
        pass

    return None


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
