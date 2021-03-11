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
    from pandasgui.widgets.figure_viewer import FigureViewer
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

    pv = FigureViewer(fig)
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

    from pandasgui.datasets import all_datasets
    show(df, df2, **all_datasets)


def test_code_history():
    import pandas as pd
    import numpy as np
    from pandasgui import show
    from pandasgui.datasets import pokemon
    pokemon = pokemon.head(10)[['Name', 'Attack', 'Defense', 'Generation', 'HP', 'Legendary']]
    gui = show(pokemon)
    pgdf = gui.store.data['pokemon']

    pgdf.edit_data(6, 3, 999)
    pgdf.sort_column(5)
    pgdf.edit_data(3, 4, 5)
    pgdf.paste_data(0, 1, pd.DataFrame({0: {0: 1000, 1: 1001}, 1: {0: 1002, 1: 1003}, 2: {0: 1004, 1: 1005}}))
    pgdf.add_filter('HP > 50')
    pgdf.sort_column(4)

    code = pgdf.code_export()
    # https://stackoverflow.com/a/52217741/3620725
    df = pokemon
    namespace = {'df': df}
    exec(code, namespace)
    df = namespace['df']

    assert (df.fillna('NULL').equals(gui.get_dataframes('pokemon').fillna('NULL')))


test_webengine_import()
test_inputs()
test_code_history()

# iterables = [["bar", "baz", "baz"], ["one", "two"]]
# ix = pd.MultiIndex.from_product(iterables, names=["first", "second"])
# df = pd.DataFrame(np.random.randn(6, 6), index=ix[:6], columns=ix[:6])
