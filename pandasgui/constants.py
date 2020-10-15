import os
from appdirs import user_data_dir

LOCAL_DATA_DIR = os.path.join(user_data_dir(), "pandasgui", "dataset_files")