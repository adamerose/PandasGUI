# Set version
try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:
    from importlib_metadata import PackageNotFoundError, version

try:
    __version__ = version("pandasgui")
except PackageNotFoundError:
    __version__ = "0.2.15"

# Logger config
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setFormatter(logging.Formatter('PandasGUI %(levelname)s — %(name)s — %(message)s'))
logger.addHandler(sh)

# Imports
from pandasgui.gui import show

__all__ = ["show", "__version__"]
