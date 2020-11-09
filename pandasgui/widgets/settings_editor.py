from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
import sys
from typing import Union
from dataclasses import dataclass, asdict, is_dataclass
from enum import Enum
from pandasgui.store import Settings, Setting

class SettingsEditor(QtWidgets.QWidget):
    def __init__(self, settings: Settings, parent=None):
        super().__init__()

        layout = QtWidgets.QVBoxLayout()

        if is_dataclass(data):
            items = asdict(data).items()
            setter = lambda key, val: [data.__setattr__(key, val), print(f'Updated {key} to {val}')]
        elif type(data) == dict:
            items = data.items()
            setter = lambda key, val: [data.__setitem__(key, val), print(f'Updated {key} to {val}')]
        else:
            raise TypeError

        for key, val in items:
            if type(val) == str:
                widget = self.text_editor(key, val, setter)
            elif type(val) == bool:
                widget = self.bool_editor(key, val, setter)
            elif type(val) == Enum:
                widget = self.bool_editor(key, val, setter)
            else:
                raise TypeError
            layout.addWidget(widget)

        layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))

        self.setLayout(layout)

    def text_editor(self, key, val, setter):
        layout = QtWidgets.QHBoxLayout()
        line_edit = QtWidgets.QLineEdit(val)
        line_edit.textChanged.connect(lambda x, key=key: setter(key, x))
        layout.addWidget(QtWidgets.QLabel(key))
        layout.addWidget(line_edit)
        container = QtWidgets.QWidget()
        container.setLayout(layout)
        return container

    def bool_editor(self, key, val, setter):
        checkbox = QtWidgets.QCheckBox(key)
        checkbox.setCheckState(val == Qt.Checked)
        checkbox.stateChanged.connect(lambda x, key=key: setter(key, x == Qt.Checked))
        return checkbox

    def enum_editor(self, key, val, setter, options):
        combo = QtWidgets.QComboBox(key)
        combo.addItems()
        checkbox.stateChanged.connect(lambda x, key=key: setter(key, x == Qt.Checked))
        return checkbox

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    from pandasgui import store

    data = store.Settings()
    d = SettingsEditor(data)
    d.show()

    sys.exit(app.exec_())
