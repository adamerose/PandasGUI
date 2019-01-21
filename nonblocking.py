import time
import multiprocess
import inspect

from PyQt5 import QtWidgets
class MainWindow(QtWidgets.QTextEdit):
    def __init__(self):
        # call super class constructor
        super(MainWindow, self).__init__()
        self.show()

def start_gui(**kwargs):
    import sys
    from PyQt5 import QtWidgets
    import pandasgui.pdgui

    # Set up QApplication
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)

    # Make GUi
    win = pandasgui.pdgui.PandasGUI(**kwargs)

    app.exec_()

def show(*args, **kwargs):
    # Get the variable names (in the scope show() was called from) of DataFrames passed to show()
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()

    # Make a dictionary out of these variable names and DataFrames
    dataframes = {}
    for i, df_object in enumerate(args):
        df_name = 'untitled' + str(i + 1)

        for var_name, var_val in callers_local_vars:
            if var_val is df_object:
                df_name = var_name

        dataframes[df_name] = df_object

    # Add these to the kwargs
    if(any([key in kwargs.keys() for key in dataframes.keys()])):
        print("Warning! Duplicate DataFrame names were given, duplicates were ignored.")
    kwargs = {**kwargs, **dataframes}

    thread = multiprocess.Process(target=start_gui, kwargs=kwargs)
    thread.start()

if __name__ == '__main__':
    import pandas as pd
    pokemon = pd.read_csv('pokemon.csv')

    sample = pd.read_csv('sample.csv')

    tuples = [('A', 'one', 'x'), ('A', 'one', 'y'), ('A', 'two', 'x'), ('A', 'two', 'y'),
              ('B', 'one', 'x'), ('B', 'one', 'y'), ('B', 'two', 'x'), ('B', 'two', 'y')]
    index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second', 'third'])
    multidf = pd.DataFrame(pd.np.random.randn(8, 8), index=index[:8], columns=index[:8])

    show(sample, multidf=multidf, pokemon=pokemon)
