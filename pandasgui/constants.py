import os
from appdirs import user_data_dir

CATEGORICAL_THRESHOLD = 50
DEFAULT_TITLE_FORMAT = "{name}: {title_columns}{title_dimensions}{names}{title_y}{title_z}{over_by}{title_x} {selection}<br>"\
                       "<sub>{groupings}{filters} {title_trendline}</sub>"

LOCAL_DATA_DIR = os.path.join(user_data_dir(), "pandasgui")
LOCAL_DATASET_DIR = os.path.join(LOCAL_DATA_DIR, "dataset_files")

os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
os.makedirs(LOCAL_DATASET_DIR, exist_ok=True)
