class DotDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, dct):
        for key, value in dct.items():
            if hasattr(value, "keys"):
                value = DotDict(value)
            self[key] = value


from threading import Timer


def throttle(wait):
    """
        https://gist.github.com/walkermatt/2871026
        Decorator that will postpone a functions
        execution until after wait seconds
        have elapsed since the last time it was invoked. """
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

def to_dict(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = to_dict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return to_dict(obj._ast())
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [to_dict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, to_dict(value, classkey))
                     for key, value in obj.__dict__.items()
                     if not callable(value) and not key.startswith('_')])
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj


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
