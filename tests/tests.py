import pandas as pd
import numpy as np
import time
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt


def generate_string_data(rows, cols, length=5):
    return pd.DataFrame(np.array([pd.util.testing.rands_array(length, cols) for x in range(rows)]))


def generate_int_data(rows, cols):
    return pd.DataFrame(np.random.randint(0, 100, size=(rows, cols)))


def generate_data():
    small_int_path = os.path.join("small_int.csv")
    large_int_path = "large_int.csv"
    small_str_path = "small_str.csv"
    large_str_path = "large_str.csv"

    generate_int_data(5000, 5).to_csv(small_int_path)
    generate_int_data(5000000, 50).to_csv(large_int_path)
    generate_string_data(5000, 5).to_csv(small_str_path)
    generate_string_data(5000000, 50).to_csv(large_str_path)


def test_memory_leak():
    from pandasgui import show

    def getObjects(cls):
        import gc
        objects = []
        for obj in gc.get_objects():
            if isinstance(obj, cls):
                objects.append(obj)
        return objects

    # string_data = generate_string_data(rows, cols)
    int_data = pd.read_csv(large_int_path)

    # %%

    for i in range(10):
        df = pd.DataFrame(int_data)

        print(len(getObjects(QtCore.QObject)), 'QObjects')
        start = time.time()
        gui = show(df)
        gui.close()
        end = time.time()
        print(end - start)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


import sys

sys.excepthook = except_hook


def test_webengine_import():
    app = QtWidgets.QApplication([])
    from pandasgui.widgets.plotly_viewer import PlotlyViewer
    import plotly.graph_objs as go

    fig = go.Figure()
    fig.add_scatter(
        x=np.random.rand(100),
        y=np.random.rand(100),
        mode="markers",
        marker={
            "size": 30,
            "color": np.random.rand(100),
            "opacity": 0.6,
            "colorscale": "Viridis",
        },
    )

    pv = PlotlyViewer(fig)
    pv.show()


def test_inputs():
    import pandas as pd
    import numpy as np
    from pandasgui import show
    iterables = [["bar", 57, 57], ["one", 23]]
    ix = pd.MultiIndex.from_product(iterables, names=["first", "second"])
    df = pd.DataFrame(np.random.randn(6, 6), index=ix[:6], columns=ix[:6])

    df2 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6],
                        2: [1, 2, 3], 'c': [4, 5, 6], }).rename(columns={'c': 2})
    show(df, df2)


test_inputs()