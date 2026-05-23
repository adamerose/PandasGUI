import os
import sys
from pathlib import Path

from appdirs import user_data_dir

LOCAL_DATA_DIR = os.path.join(user_data_dir(), "pandasgui")
LOCAL_DATASET_DIR = os.path.join(LOCAL_DATA_DIR, "dataset_files")

os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
os.makedirs(LOCAL_DATASET_DIR, exist_ok=True)

RESOURCE_IMAGE_DIR = Path(__file__).resolve().parent / "resources" / "images"
PANDASGUI_ICON_PATH = str(RESOURCE_IMAGE_DIR / "icon.png")
PANDASGUI_ICON_PATH_ICO = str(RESOURCE_IMAGE_DIR / "icon.ico")

if sys.platform == "win32":
    SHORTCUT_PATH = os.path.join(os.getenv('APPDATA'), 'Microsoft/Windows/Start Menu/Programs/PandasGUI.lnk', )
    PY_INTERPRETTER_PATH = os.path.join(os.path.dirname(sys.executable), 'python.exe')
    PYW_INTERPRETTER_PATH = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
