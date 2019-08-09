# This file isn't used. Keeping it for reference in case I want to re-add the separate process functionality

"""Creates a non-blocking instance of the Pandas GUI in a separate process. Works in both script & interactive mode"""

import multiprocessing


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
    thread = multiprocessing.Process(target=start_gui, kwargs=kwargs)
    thread.start()


if __name__ == '__main__':
    from pandasgui import show

    from pandasgui.datasets import iris, flights, multi, pokemon

    show(iris, flights, multi, pokemon)
