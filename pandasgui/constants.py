import os
from appdirs import user_data_dir

LOCAL_DATA_DIR = os.path.join(user_data_dir(), "pandasgui")
LOCAL_DATASET_DIR = os.path.join(LOCAL_DATA_DIR, "dataset_files")

os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
os.makedirs(LOCAL_DATASET_DIR, exist_ok=True)
