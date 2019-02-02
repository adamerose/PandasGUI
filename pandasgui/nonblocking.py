'''
This module creates a nonblocking instance of the Pandas GUI in a separate process. Works in both script & interactive mode
'''
import multiprocess


def start_gui(**kwargs):
    import sys
    from PyQt5 import QtWidgets
    from gui import PandasGUI

    # Set up QApplication
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)

    # Make GUi
    win = PandasGUI(**kwargs)

    app.exec_()


def show_nonblocking(**kwargs):
    thread = multiprocess.Process(target=start_gui, kwargs=kwargs)
    thread.start()


if __name__ == '__main__':
    import pandas as pd
    from gui import show

    pokemon = pd.read_csv('sample_data/pokemon.csv')

    sample = pd.read_csv('sample_data/sample.csv')

    tuples = [('A', 'one', 'x'), ('A', 'one', 'y'), ('A', 'two', 'x'), ('A', 'two', 'y'),
              ('B', 'one', 'x'), ('B', 'one', 'y'), ('B', 'two', 'x'), ('B', 'two', 'y')]
    index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second', 'third'])
    multidf = pd.DataFrame(pd.np.random.randn(8, 8), index=index[:8], columns=index[:8])

    show(sample, nonblocking=True)
    show(multidf)

    print('test')
