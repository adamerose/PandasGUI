import logging
import pandas as pd
from PyQt5 import QtWidgets
from typing import List, Union
import sys

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
    have elapsed since the last time it was invoked."""
    from threading import Timer

    def decorator(fn):
        def throttled(*args, **kwargs):
            def call_it():
                fn(*args, **kwargs)

            try:
                throttled.t.cancel()
            except (AttributeError):
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


def get_logger(logger_name=None):
    import logging
    import sys

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("PandasGUI %(levelname)s — %(name)s — %(message)s")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


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
    return hasattr(sys, "ps1")


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
            flat_index = [
                sep.join([str(x) for x in tup]).strip(sep) for tup in mi.values
            ]
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
                    for i, val in enumerate(
                        tuple
                    ):  # Iterates over the values in this index segment
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


# Alternative to df.nunique that works when it contains unhashable items
def nunique(df):
    results = {}
    for col in df.columns:
        s = df[col]
        try:
            results[col] = s.nunique()
        except TypeError as e:
            results[col] = s.astype(str).nunique()

    return pd.Series(results)


def traverse_tree_widget(
    tree: Union[QtWidgets.QTreeWidget, QtWidgets.QTreeWidgetItem]
) -> List[QtWidgets.QTreeWidgetItem]:
    if type(tree) == QtWidgets.QTreeWidget:
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


def delete_datasets():
    from pandasgui.datasets import LOCAL_DATA_DIR
    import shutil

    logger.info(f"Deleting sample dataset directory ({LOCAL_DATA_DIR})")
    shutil.rmtree(LOCAL_DATA_DIR)


event_lookup = {
    "0": "QEvent::None",
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
    "126": "QEvent::ZOrderChange",
}
