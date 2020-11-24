from pandasgui.gui import show

__all__ = ["show"]


# Logger config
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setFormatter(logging.Formatter('PandasGUI %(levelname)s — %(name)s — %(message)s'))
logger.addHandler(sh)
