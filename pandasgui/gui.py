import inspect
import os
import sys
import pprint
from typing import Union, Iterable, Callable
from dataclasses import dataclass
import pandas as pd
import pkg_resources
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
import plotly.basedatatypes

from pandasgui.store import PandasGuiStore, PandasGuiDataFrameStore
from pandasgui.utility import fix_ipython, fix_pyqt, as_dict, delete_datasets, resize_widget, get_figure_type
from pandasgui.widgets.dataframe_explorer import DataFrameExplorer
from pandasgui.widgets.grapher import schemas
from pandasgui.widgets.func_ui import BooleanArg
from pandasgui.widgets.find_toolbar import FindToolbar
from pandasgui.widgets.json_viewer import JsonViewer
from pandasgui.widgets.navigator import Navigator
from pandasgui.widgets.figure_viewer import FigureViewer
from pandasgui.widgets.settings_editor import SettingsEditor
from pandasgui.themes import qstylish
from pandasgui.widgets.python_highlighter import PythonHighlighter
from IPython.core.magic import (register_line_magic, register_cell_magic,
                                register_line_cell_magic)

import logging

logger = logging.getLogger(__name__)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


# Set the exception hook to our wrapping function
sys.excepthook = except_hook

# Enables PyQt event loop in IPython
fix_ipython()

# Keep a list of PandasGUI widgets so they don't get garbage collected
refs = []
plotly_refs = []


class PandasGui(QtWidgets.QMainWindow):
    def __init__(self, settings: dict = {}, **kwargs):
        """
        Args:
            settings: Dict of settings, as defined in pandasgui.store.SettingsStore
            kwargs: Dict of DataFrames where key is name & val is the DataFrame object
        """
        self.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        super().__init__()

        self.caller_stack = inspect.currentframe().f_back

        self.stacked_widget = None
        self.navigator = None
        self.splitter = None
        self.find_bar = None

        refs.append(self)

        self.store = PandasGuiStore()
        self.store.gui = self
        # Add user provided settings to data store
        for key, value in settings.items():
            setting = self.store.settings[key]
            setting.value = value

        # update default schema
        for i, chart in enumerate(schemas):
            if chart.name in ('bar', 'line'):
                args = schemas[i].args
                for j, arg in enumerate(args):
                    if arg.arg_name == 'apply_sort':
                        args[j] = BooleanArg(arg_name='apply_sort', default_value=self.store.settings.apply_sort.value)
                    elif arg.arg_name == 'apply_mean':
                        args[j] = BooleanArg(arg_name='apply_mean', default_value=self.store.settings.apply_mean.value)

        # This will silently fail if the style isn't available on the OS, which is okay
        self.app.setStyle(QtWidgets.QStyleFactory.create(self.store.settings.style.value))

        # Create all widgets
        self.init_ui()

        # Adds DataFrames listed in kwargs to data store.
        for df_name, df in kwargs.items():
            self.store.add_dataframe(df, df_name)

        # Default to first item
        self.navigator.setCurrentItem(self.navigator.topLevelItem(0))

        self.show()
        # Start event loop if blocking enabled
        if self.store.settings.block.value:
            self.app.exec_()

    # Create and add all widgets to GUI.
    def init_ui(self):
        resize_widget(self, 0.7, 0.7)

        # Center window on screen
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(int((screen.width() - size.width()) / 2),
                  int((screen.height() - size.height()) / 2), )

        # Set window title and icon
        self.setWindowTitle("PandasGUI")
        pdgui_icon_path = pkg_resources.resource_filename(__name__, "resources/images/icon.png")
        self.app.setWindowIcon(QtGui.QIcon(pdgui_icon_path))

        # Hide the question mark on dialogs
        self.app.setAttribute(Qt.AA_DisableWindowContextHelpButton)

        # Accept drops, for importing files. See methods below: dropEvent, dragEnterEvent, dragMoveEvent
        self.setAcceptDrops(True)

        # This holds the DataFrameExplorer for each DataFrame
        self.stacked_widget = QtWidgets.QStackedWidget()

        # Make the navigation bar
        self.navigator = Navigator(self.store)

        # Make splitter to hold nav and DataFrameExplorers
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.navigator)
        self.splitter.addWidget(self.stacked_widget)

        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        nav_width = self.navigator.sizeHint().width()
        self.splitter.setSizes([nav_width, self.width() - nav_width])
        self.splitter.setContentsMargins(10, 10, 10, 10)

        # makes the find toolbar
        self.find_bar = FindToolbar(self)
        self.addToolBar(self.find_bar)

        # QMainWindow setup
        self.make_menu_bar()
        self.setCentralWidget(self.splitter)

    ####################
    # Menu bar functions

    def make_menu_bar(self):
        menubar = self.menuBar()

        @dataclass
        class MenuItem:
            name: str
            func: Callable
            shortcut: str = ''

        items = {'Edit': [MenuItem(name='Find',
                                   func=self.find_bar.show_find_bar,
                                   shortcut='Ctrl+F'),
                          MenuItem(name='Copy',
                                   func=self.copy,
                                   shortcut='Ctrl+C'),
                          MenuItem(name='Copy With Headers',
                                   func=self.copy_with_headers,
                                   shortcut='Ctrl+Shift+C'),
                          MenuItem(name='Paste',
                                   func=self.paste,
                                   shortcut='Ctrl+V'),
                          MenuItem(name='Import',
                                   func=self.import_dialog),
                          MenuItem(name='Import From Clipboard',
                                   func=self.import_from_clipboard),
                          MenuItem(name='Export',
                                   func=self.export_dialog),
                          MenuItem(name='Delete Selected DataFrames',
                                   func=self.delete_selected_dataframes),
                          MenuItem(name='Refresh Data',
                                   func=self.reload_data,
                                   shortcut='Ctrl+R'),
                          MenuItem(name='Code Export',
                                   func=self.code_export),
                          ],
                 'Settings': [MenuItem(name='Add To Context Menu',
                                       func=self.add_to_context_menu),
                              MenuItem(name='Remove From Context Menu',
                                       func=self.remove_from_context_menu),
                              MenuItem(name='Preferences...',
                                       func=self.edit_settings),

                              ],
                 'Debug': [MenuItem(name='About',
                                    func=self.about),
                           MenuItem(name='Print Data PandasGuiStore',
                                    func=self.print_store),
                           MenuItem(name='View Data PandasGuiStore',
                                    func=self.view_store),
                           MenuItem(name='Print History (for current DataFrame)',
                                    func=self.print_history),
                           MenuItem(name='Browse Sample Datasets',
                                    func=self.show_sample_datasets),
                           ]
                 }

        menus = {}
        # Add menu items and actions to UI using the schema defined above
        for menu_name in items.keys():
            menu = menubar.addMenu(menu_name)
            menus[menu_name] = menu
            for x in items[menu_name]:
                action = QtWidgets.QAction(x.name, self)
                action.setShortcut(x.shortcut)
                action.triggered.connect(x.func)
                menu.addAction(action)

        # Add an extra option list to the menu for each GUI style that exist for the user's system
        theme_menu = menus['Settings'].addMenu("&Set Theme")
        theme_group = QtWidgets.QActionGroup(theme_menu)
        for theme in ["light", "dark", "classic"]:
            theme_action = QtWidgets.QAction(f"&{theme}", self, checkable=True)
            theme_action.triggered.connect(lambda checked, theme=theme: self.set_theme(theme))
            theme_group.addAction(theme_action)
            theme_menu.addAction(theme_action)

            # Set the default theme
            if theme == self.store.settings.theme.value:
                theme_action.trigger()

    def set_theme(self, name: str):
        if name == "classic":
            self.setStyleSheet("")
            self.store.settings.theme.value = 'classic'
        elif name == "dark":
            self.setStyleSheet(qstylish.dark())
            self.store.settings.theme.value = 'dark'
        elif name == "light":
            self.setStyleSheet(qstylish.light())
            self.store.settings.theme.value = 'light'

    def copy(self):
        if self.store.selected_pgdf.dataframe_explorer.active_tab == "DataFrame":
            self.store.selected_pgdf.dataframe_explorer.dataframe_viewer.copy()
        elif self.store.selected_pgdf.dataframe_explorer.active_tab == "Statistics":
            self.store.selected_pgdf.dataframe_explorer.statistics_viewer.copy()

    def copy_with_headers(self):
        if self.store.selected_pgdf.dataframe_explorer.active_tab == "DataFrame":
            self.store.selected_pgdf.dataframe_viewer.copy(header=True)
        elif self.store.selected_pgdf.dataframe_explorer.active_tab == "Statistics":
            self.store.selected_pgdf.dataframe_explorer.statistics_viewer.copy(header=True)

    def paste(self):
        if self.store.selected_pgdf.dataframe_explorer.active_tab == "DataFrame":
            self.store.selected_pgdf.dataframe_explorer.dataframe_viewer.paste()

    def code_export(self):
        code_history = self.store.selected_pgdf.code_export()
        self.code_export_dialog = QtWidgets.QDialog(self)
        layout = QtWidgets.QVBoxLayout()
        textbox = QtWidgets.QPlainTextEdit()
        highlight = PythonHighlighter(textbox.document(), dark=self.store.selected_pgdf.settings.theme.value == 'dark')
        textbox.setPlainText(code_history)
        textbox.setReadOnly(True)
        textbox.setLineWrapMode(textbox.NoWrap)
        layout.addWidget(textbox)
        resize_widget(self.code_export_dialog, 0.5, 0.5)
        self.code_export_dialog.setLayout(layout)
        self.code_export_dialog.show()

    def delete_selected_dataframes(self):
        for name in [item.text(0) for item in self.navigator.selectedItems()]:
            self.store.remove_dataframe(name)

    def reorder_columns(self):
        self.store.selected_pgdf

    def dropEvent(self, e):
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
            fpath_list = []
            for url in e.mimeData().urls():
                fpath_list.append(str(url.toLocalFile()))

            for fpath in fpath_list:
                self.store.import_file(fpath)
        else:
            e.ignore()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def print_store(self):
        d = as_dict(self.store)
        pprint.pprint(d)

    def print_history(self):
        pgdf = self.store.selected_pgdf
        if len(pgdf.history) == 0:
            print(f"No actions recorded yet for {pgdf.name}")
        else:
            header = f'---- History ({pgdf.name}) ----'
            print(header)
            for h in pgdf.history:
                print(h)
            print('-' * len(header))

    def view_store(self):
        d = as_dict(self.store)
        self.store_viewer = JsonViewer(d)
        self.store_viewer.show()

    # Return all DataFrames, or a subset specified by names. Returns a dict of name:df or a single df if there's only 1
    def get_dataframes(self, names: Union[None, str, list] = None):
        return self.store.get_dataframes(names)

    def __getitem__(self, key):
        return self.get_dataframes(key)

    def import_dialog(self):
        dialog = QtWidgets.QFileDialog()
        paths, _ = dialog.getOpenFileNames(filter="*.csv *.xlsx *.parquet")
        for path in paths:
            self.store.import_file(path)

    def export_dialog(self):
        dialog = QtWidgets.QFileDialog()
        pgdf = self.store.selected_pgdf
        path, _ = dialog.getSaveFileName(directory=pgdf.name, filter="*.csv")
        pgdf.df.to_csv(path, index=False)

    def import_from_clipboard(self):
        df = pd.read_clipboard()
        self.store.add_dataframe(df)

    # https://stackoverflow.com/a/29769228/3620725
    def add_to_context_menu(self):
        import winreg

        key = winreg.HKEY_CURRENT_USER
        value = rf'{sys.executable} -m pandasgui.run_with_args "%V"'
        icon_value = r"C:\_MyFiles\Programming\pandasgui\pandasgui\resources\images\icon.ico"

        handle = winreg.CreateKeyEx(key, "Software\Classes\*\shell\Open with PandasGUI\command", 0,
                                    winreg.KEY_SET_VALUE)
        winreg.SetValueEx(handle, "", 0, winreg.REG_SZ, value)
        handle = winreg.CreateKeyEx(key, "Software\Classes\*\shell\Open with PandasGUI", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(handle, "icon", 0, winreg.REG_SZ, icon_value)

    def remove_from_context_menu(self):
        import winreg
        key = winreg.HKEY_CURRENT_USER
        winreg.DeleteKey(key, "Software\Classes\*\shell\Open with PandasGUI\command")
        winreg.DeleteKey(key, "Software\Classes\*\shell\Open with PandasGUI")

    def edit_settings(self):

        dialog = QtWidgets.QDialog(self)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(SettingsEditor(self.store.settings))
        dialog.setLayout(layout)
        dialog.show()

    def about(self):
        import pandasgui
        dialog = QtWidgets.QDialog(self)
        layout = QtWidgets.QVBoxLayout()
        dialog.setLayout(layout)
        layout.addWidget(QtWidgets.QLabel(f"Version: {pandasgui.__version__}"))
        layout.addWidget(QtWidgets.QLabel(
            f'''GitHub: <a style="color: #1e81cc;" href="https://github.com/adamerose/PandasGUI">https://github.com/adamerose/PandasGUI</a>'''))
        # dialog.resize(500, 500)
        dialog.setWindowTitle("About")
        dialog.show()

    def show_sample_datasets(self):
        from pandasgui.datasets import LOCAL_DATASET_DIR
        import os
        os.startfile(LOCAL_DATASET_DIR, 'explore')

    def closeEvent(self, e: QtGui.QCloseEvent) -> None:
        refs.remove(self)
        super().closeEvent(e)

    # Replace all GUI DataFrames with the current DataFrame of the same name from the scope show was called
    def reload_data(self):
        callers_local_vars = self.caller_stack.f_locals.items()
        refreshed_names = []
        for var_name, var_val in callers_local_vars:
            for ix, name in enumerate([pgdf.name for pgdf in self.store.data.values()]):
                if var_name == name:
                    none_found_flag = False
                    self.store.remove_dataframe(var_name)
                    self.store.add_dataframe(var_val, name=var_name)
                    refreshed_names.append(var_name)

        if not refreshed_names:
            print("No matching DataFrames found to reload")
        else:
            print(f"Refreshed {', '.join(refreshed_names)}")


def show(*args,
         settings={},
         **kwargs):
    # Get the variable names in the scope show() was called from
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()

    # Make a dictionary of the DataFrames from the position args and get their variable names using inspect
    items = {}
    untitled_number = 1
    for ix, item in enumerate(args):
        name = None

        for var_name, var_val in callers_local_vars:
            if var_val is item:
                name = var_name

        if name is None:
            name = f"untitled_{untitled_number}"
            untitled_number += 1
        items[name] = item

    dupes = [key for key in items.keys() if key in kwargs.keys()]
    if any(dupes):
        logger.warning("Duplicate DataFrame names were provided, duplicates were ignored.")

    kwargs = {**kwargs, **items}

    plotly_kwargs = {key: value for (key, value) in kwargs.items() if get_figure_type(value) is not None}
    dataframe_kwargs = {key: value for (key, value) in kwargs.items() if issubclass(type(value), pd.DataFrame)}
    invalid_kwargs = {key: value for (key, value) in kwargs.items()
                      if key not in list(plotly_kwargs.keys()) + list(dataframe_kwargs.keys())}

    if invalid_kwargs:
        for key, val in invalid_kwargs.items():
            logger.warning(f"Invalid type passed to pandasgui.show: type({key}) = {type(val)}")

    if plotly_kwargs:
        for name, fig in plotly_kwargs.items():
            pv = FigureViewer(fig)
            pv.show()
            plotly_refs.append(pv)
            pv.setWindowTitle(name)

    if dataframe_kwargs:
        pandas_gui = PandasGui(settings=settings, **dataframe_kwargs)
        pandas_gui.caller_stack = inspect.currentframe().f_back

        # Register IPython magic
        try:
            @register_line_magic
            def pg(line):
                pandas_gui.store.eval_magic(line)
                return line

        except Exception as e:
            # Let this silently fail if no IPython console exists
            if e.args[0] == 'Decorator can only run in context where `get_ipython` exists':
                pass
            else:
                raise e

        return pandas_gui


if __name__ == "__main__":
    from pandasgui.datasets import all_datasets, pokemon, mi_manufacturing

    gui = show(**all_datasets)
