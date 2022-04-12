import os
import sys
from appdirs import user_data_dir
import pkg_resources

LOCAL_DATA_DIR = os.path.join(user_data_dir(), "pandasgui")
LOCAL_DATASET_DIR = os.path.join(LOCAL_DATA_DIR, "dataset_files")

os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
os.makedirs(LOCAL_DATASET_DIR, exist_ok=True)

PANDASGUI_ICON_PATH = pkg_resources.resource_filename(__name__, "resources/images/icon.png")
PANDASGUI_ICON_PATH_ICO = pkg_resources.resource_filename(__name__, "resources/images/icon.ico")

SHORTCUT_PATH = os.path.join(os.getenv('APPDATA'), 'Microsoft/Windows/Start Menu/Programs/PandasGUI.lnk', )
PY_INTERPRETTER_PATH = os.path.join(os.path.dirname(sys.executable), 'python.exe')
PYW_INTERPRETTER_PATH = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')