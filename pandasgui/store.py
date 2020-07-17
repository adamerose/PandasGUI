from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Settings:
    editable: bool = True  # Are table cells editable
    block: bool = False


@dataclass
class DataItem:
    dataframe: "DataFrame"
    dataframe_explorer: "DataFrameExplorer"


@dataclass
class Store:
    settings: Settings = Settings()
    data: Dict[DataItem] = field(default_factory=dict)


store = Store()
