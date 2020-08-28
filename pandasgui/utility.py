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


def get_logger(logger_name=None):
    import logging
    import sys

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("PandasGui %(levelname)s — %(name)s — %(message)s")

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
    try:
        from IPython import get_ipython
        ipython = get_ipython()
        if ipython is not None:
            ipython.magic("gui qt5")
    except ModuleNotFoundError:
        # Don't need to fix iPython if user doesn't have it
        return


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
