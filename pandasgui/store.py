from dataclasses import dataclass


@dataclass
class Settings:
    editable: bool = True  # Are table cells editable
    block: bool = False


@dataclass
class Store:
    settings: Settings = Settings()


store = Store()
