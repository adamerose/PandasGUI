'''
Creates a nonblocking instance of the Pandas GUI in a separate process. Works in both script & interactive mode
'''

import multiprocess


def start_gui(**kwargs):
    import sys
    from PyQt5 import QtWidgets
    from pandasgui.gui import PandasGUI

    # Set up QApplication
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)

    # Make GUi
    win = PandasGUI(nonblocking=True, **kwargs)

    app.exec_()


def show_nonblocking(**kwargs):
    thread = multiprocess.Process(target=start_gui, kwargs=kwargs)
    thread.start()


if __name__ == '__main__':
    import pandas as pd
    from pandasgui import show

    pokemon = pd.read_csv('sample_data/pokemon.csv')
    sample = pd.read_csv('sample_data/sample.csv')

    show(sample, nonblocking=True)
    show(pokemon)
