import inspect
import io
import os
import sys
import pprint
from typing import Callable, Union
from dataclasses import dataclass
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

import pandasgui
from pandasgui.constants import PANDASGUI_ICON_PATH
from pandasgui.store import PandasGuiStore, SettingsSchema
from pandasgui.utility import as_dict, fix_ipython, get_figure_type, resize_widget
from pandasgui.widgets.find_toolbar import FindToolbar
from pandasgui.widgets.json_viewer import JsonViewer
from pandasgui.widgets.navigator import Navigator
from pandasgui.widgets.figure_viewer import FigureViewer
from pandasgui.widgets.settings_editor import SettingsEditor
import qtstylish
from pandasgui.widgets.python_highlighter import PythonHighlighter
from IPython.core.magic import register_line_magic

import logging

logger = logging.getLogger(__name__)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


# Set the exception hook to our wrapping function
sys.excepthook = except_hook

# Enables PyQt event loop in IPython
fix_ipython()

# Keep a list of widgets so they don't get garbage collected
refs = []


class PandasGui(QtWidgets.QMainWindow):

    def __init__(self, settings: SettingsSchema = {}, **kwargs):
        """
        Args:
            settings: Dict of settings, as defined in pandasgui.store.SettingsStore
            kwargs: Dict of DataFrames where key is name & val is the DataFrame object
        """
        self.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        super().__init__()

        self.caller_stack = inspect.currentframe().f_back

        self.stacked_widget: QtWidgets.QStackedWidget = None
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

        # Create all widgets
        self.init_ui()

        # Add the item to the store differently depending what type it is
        for key, value in kwargs.items():
            # Pandas objects
            if issubclass(type(value), pd.DataFrame) or issubclass(type(value), pd.Series):
                self.store.add_dataframe(value, key)
            # Spark
            elif hasattr(value, 'toPandas'):
                temp = value.toPandas()
                self.store.add_dataframe(value, key)
            elif hasattr(value, 'to_pandas'):
                temp = value.to_pandas()
                self.store.add_dataframe(value, key)
            # JSON
            elif issubclass(type(value), list) or issubclass(type(value), dict):
                jv = JsonViewer(value)
                jv.setWindowTitle(key)
                self.store.add_item(jv, key)
            # Graphs
            elif get_figure_type(value) is not None:
                pv = FigureViewer(value)
                pv.setWindowTitle(key)
                self.store.add_item(pv, key)
            # File buffers
            elif issubclass(type(value), io.BytesIO) or issubclass(type(value), io.StringIO):
                value.seek(0)
                df = pd.read_csv(value)
                self.store.add_dataframe(df, key)
            # File paths
            elif issubclass(type(value), str):
                if os.path.exists(value):
                    self.store.import_file(value)
                else:
                    logger.warning(f"File path is invalid or does not exist: {value}")
            else:
                logger.warning(f"PandasGUI Unsupported type: {type(value)}")
        # Default to first item
        self.navigator.setCurrentItem(self.navigator.topLevelItem(0))

    # Create and add all widgets to GUI.
    def init_ui(self):
        self.code_history_viewer = None

        resize_widget(self, 0.7, 0.7)

        # Status bar
        self.setStatusBar(QtWidgets.QStatusBar())

        # Center window on screen
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(int((screen.width() - size.width()) / 2),
                  int((screen.height() - size.height()) / 2), )

        # Set window title and icon
        self.setWindowTitle("PandasGUI")
        self.app.setWindowIcon(QtGui.QIcon(PANDASGUI_ICON_PATH))

        # Hide the question mark on dialogs
        self.app.setAttribute(Qt.AA_DisableWindowContextHelpButton)

        # Accept drops, for importing files. See methods below: dropEvent, dragEnterEvent, dragMoveEvent
        self.setAcceptDrops(True)

        # This holds the DataFrameExplorer for each DataFrame
        self.stacked_widget = QtWidgets.QStackedWidget()

        # Make the navigation bar
        self.navigator = Navigator(self.store)

        # Make splitter to hold nav and DataFrameExplorers
        self.splitter = QtWidgets.QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.navigator)
        self.splitter.addWidget(self.stacked_widget)

        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        # makes the find toolbar
        self.find_bar = FindToolbar(self)
        self.addToolBar(self.find_bar)

        # QMainWindow setup
        self.make_menu_bar()
        self.setCentralWidget(self.splitter)

        # Create a copy of the settings in case the SettingsStore reference has
        # been discarded by Qt prematurely
        # https://stackoverflow.com/a/17935694/10342097
        self.store.settings = self.store.settings.copy()

        # Signals
        self.store.settings.settingsChanged.connect(self.apply_settings)

        self.apply_settings()

    ####################
    # Menu bar functions

    def make_menu_bar(self):
        menubar = self.menuBar()

        @dataclass
        class MenuItem:
            name: str
            func: Callable
            shortcut: str = ''

        items = {'Edit':      [MenuItem(name='Find',
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
                               MenuItem(name='Export To Clipboard',
                                        func=self.export_to_clipboard),
                               MenuItem(name='Code Export',
                                        func=self.show_code_export),
                               ],
                 'DataFrame': [MenuItem(name='Delete Selected DataFrames',
                                        func=self.delete_selected_dataframes),
                               MenuItem(name='Reload DataFrames',
                                        func=self.reload_data,
                                        shortcut='Ctrl+R'),
                               MenuItem(name='Parse All Dates',
                                        func=lambda: self.store.selected_pgdf.parse_all_dates()),
                               ],
                 'Settings':  [MenuItem(name='Preferences...',
                                        func=self.edit_settings),
                               {"Context Menus": [MenuItem(name='Add PandasGUI To Context Menu',
                                                           func=self.add_to_context_menu),
                                                  MenuItem(name='Remove PandasGUI From Context Menu',
                                                           func=self.remove_from_context_menu),
                                                  MenuItem(name='Add PandasGUI To Start Menu',
                                                           func=self.add_to_start_menu),
                                                  MenuItem(name='Remove PandasGUI From Start Menu',
                                                           func=self.remove_from_start_menu),
                                                  MenuItem(name='Add JupyterLab To Context Menu',
                                                           func=self.add_jupyter_to_context_menu),
                                                  MenuItem(name='Remove JupyterLab From Context Menu',
                                                           func=self.remove_jupyter_from_context_menu), ]}

                               ],
                 'Debug':     [MenuItem(name='About',
                                        func=self.about),
                               MenuItem(name='Browse Sample Datasets',
                                        func=self.show_sample_datasets),
                               MenuItem(name='View PandasGuiStore',
                                        func=self.view_store),
                               MenuItem(name='View DataFrame History',
                                        func=self.view_history),
                               MenuItem(name='Throw Error',
                                        func=lambda x: exec('raise(Exception("Exception raised by PandasGUI"))')),
                               ]
                 }

        def add_menus(dic, root):
            # Add menu items and actions to UI using the schema defined above
            for menu_name in dic.keys():
                menu = root.addMenu(menu_name)
                for x in dic[menu_name]:
                    if type(x) == dict:
                        add_menus(x, menu)
                    else:
                        action = QtWidgets.QAction(x.name, self)
                        action.setShortcut(x.shortcut)
                        action.triggered.connect(x.func)
                        menu.addAction(action)

        add_menus(items, menubar)

    def apply_settings(self):
        theme = self.store.settings.theme.value
        if theme == "classic":
            self.setStyleSheet("")
            self.store.settings.theme.value = 'classic'
        elif theme == "dark":
            self.setStyleSheet(qtstylish.dark())
            self.store.settings.theme.value = 'dark'
        elif theme == "light":
            self.setStyleSheet(qtstylish.light())
            self.store.settings.theme.value = 'light'

    def copy(self):
        if self.store.selected_pgdf.dataframe_explorer.active_tab == "DataFrame":
            self.store.selected_pgdf.dataframe_explorer.dataframe_viewer.copy()
        elif self.store.selected_pgdf.dataframe_explorer.active_tab == "Statistics":
            self.store.selected_pgdf.dataframe_explorer.statistics_viewer.dataframe_viewer.copy()

    def copy_with_headers(self):
        if self.store.selected_pgdf.dataframe_explorer.active_tab == "DataFrame":
            self.store.selected_pgdf.dataframe_viewer.copy(header=True)
        elif self.store.selected_pgdf.dataframe_explorer.active_tab == "Statistics":
            self.store.selected_pgdf.dataframe_explorer.statistics_viewer.dataframe_viewer.copy(header=True)

    def paste(self):
        if self.store.selected_pgdf.dataframe_explorer.active_tab == "DataFrame":
            self.store.selected_pgdf.dataframe_explorer.dataframe_viewer.paste()

    def show_code_export(self):
        self.store.selected_pgdf.dataframe_explorer.code_history_viewer.show()

    def update_code_export(self):
        self.store.selected_pgdf.dataframe_explorer.code_history_viewer.refresh()

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

    def view_history(self):
        d = self.store.selected_pgdf.history
        self.viewer = JsonViewer(d)
        self.viewer.show()

    def view_store(self):
        d = as_dict(self.store)
        self.viewer = JsonViewer(d)
        self.viewer.show()

    # Return all DataFrames, or a subset specified by names. Returns a dict of name:df or a single df if there's only 1
    def get_dataframes(self, names: Union[None, str, list] = None):
        return self.store.get_dataframes(names)

    def __getitem__(self, key):
        return self.get_dataframes(key)

    def import_dialog(self):
        dialog = QtWidgets.QFileDialog()
        paths, _ = dialog.getOpenFileNames(filter="*.csv *.xlsx *.parquet *.json")
        for path in paths:
            self.store.import_file(path)

    def export_dialog(self):
        dialog = QtWidgets.QFileDialog()
        pgdf = self.store.selected_pgdf
        path, _ = dialog.getSaveFileName(directory=pgdf.name, filter="*.csv")
        if path:
            pgdf.df.to_csv(path, index=False)

    def import_from_clipboard(self):
        df = pd.read_clipboard(sep=',|\t', engine="python",
                               na_values='""',  # https://stackoverflow.com/a/67915100/3620725
                               skip_blank_lines=False)
        self.store.add_dataframe(df)

    def export_to_clipboard(self):
        self.store.selected_pgdf.df.to_clipboard(excel=True, index=True)

    # https://stackoverflow.com/a/29769228/3620725
    def add_to_context_menu(self):
        import winreg

        key = winreg.HKEY_CURRENT_USER
        command_value = rf'{sys.executable} -m pandasgui.run_with_args "%V"'
        icon_value = fr"{os.path.dirname(pandasgui.__file__)}\resources\images\icon.ico"

        handle = winreg.CreateKeyEx(key, "Software\Classes\*\shell\Open with PandasGUI\command", 0,
                                    winreg.KEY_SET_VALUE)
        winreg.SetValueEx(handle, "", 0, winreg.REG_SZ, command_value)
        handle = winreg.CreateKeyEx(key, "Software\Classes\*\shell\Open with PandasGUI", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(handle, "icon", 0, winreg.REG_SZ, icon_value)

    def remove_from_context_menu(self):
        import winreg
        key = winreg.HKEY_CURRENT_USER
        winreg.DeleteKey(key, "Software\Classes\*\shell\Open with PandasGUI\command")
        winreg.DeleteKey(key, "Software\Classes\*\shell\Open with PandasGUI")

    # https://stackoverflow.com/a/46081847
    def add_to_start_menu(self):
        import os
        import win32com.client
        import pythoncom
        from pandasgui.constants import PANDASGUI_ICON_PATH_ICO, PYW_INTERPRETTER_PATH, SHORTCUT_PATH

        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(SHORTCUT_PATH)
        shortcut.Targetpath = PYW_INTERPRETTER_PATH
        shortcut.Arguments = '-c "import pandasgui; pandasgui.show()"'
        shortcut.IconLocation = PANDASGUI_ICON_PATH_ICO
        shortcut.WindowStyle = 7  # 7 - Minimized, 3 - Maximized, 1 - Normal
        shortcut.save()

    def remove_from_start_menu(self):
        from pandasgui.constants import SHORTCUT_PATH
        import os
        os.remove(SHORTCUT_PATH)

    def add_jupyter_to_context_menu(self):
        import winreg

        key = winreg.HKEY_CURRENT_USER
        command_value = rf'cmd.exe /k jupyter lab --notebook-dir="%V"'
        icon_value = fr"{os.path.dirname(pandasgui.__file__)}\resources\images\jupyter_icon.ico"

        handle = winreg.CreateKeyEx(key, "Software\Classes\directory\Background\shell\Open with JupyterLab\command", 0,
                                    winreg.KEY_SET_VALUE)
        winreg.SetValueEx(handle, "", 0, winreg.REG_SZ, command_value)
        handle = winreg.CreateKeyEx(key, "Software\Classes\directory\Background\shell\Open with JupyterLab", 0,
                                    winreg.KEY_SET_VALUE)
        winreg.SetValueEx(handle, "icon", 0, winreg.REG_SZ, icon_value)

    def remove_jupyter_from_context_menu(self):
        import winreg
        key = winreg.HKEY_CURRENT_USER
        winreg.DeleteKey(key, "Software\Classes\directory\Background\shell\Open with JupyterLab\command")
        winreg.DeleteKey(key, "Software\Classes\directory\Background\shell\Open with JupyterLab")

    def edit_settings(self):

        dialog = QtWidgets.QDialog(self)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(SettingsEditor(self.store.settings))
        dialog.setLayout(layout)
        dialog.resize(700, 800)
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
         settings: SettingsSchema = {},
         **kwargs):
    '''
    Objects provided as args and kwargs should be any of the following:
    DataFrame   Show it using PandasGui
    Series      Show it using PandasGui
    Figure      Show it using FigureViewer. Supports figures from plotly, bokeh, matplotlib, altair, PIL
    dict/list   Show it using JsonViewer
    '''
    logger.info("Opening PandasGUI")
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
        logger.warning("Duplicate names were provided, duplicates were ignored.")

    kwargs = {**kwargs, **items}

    pandas_gui = PandasGui(settings=settings, **kwargs)
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

    pandas_gui.show()
    pandas_gui.activateWindow()
    pandas_gui.raise_()

    # Start event loop if blocking enabled
    if pandas_gui.store.settings.block.value:
        pandas_gui.app.exec_()
    return pandas_gui


if __name__ == "__main__":
    from pandasgui.datasets import pokemon, titanic, mi_manufacturing, trump_tweets, all_datasets

    gui = show(pokemon, titanic, mi_manufacturing)
