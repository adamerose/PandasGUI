from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
import sys
from typing import Union
from dataclasses import dataclass, is_dataclass
from enum import EnumMeta
from pandasgui.store import SETTINGS_STORE, SettingsStore, Setting


class SettingsEditor(QtWidgets.QWidget):
    def __init__(self, settings: SettingsStore, parent=None):
        super().__init__()

        layout = QtWidgets.QGridLayout()
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        self.settings = settings
        setter = lambda key, val: self.settings[key].value.__setattr__(val)

        # Dont display these settings because they have effects during the GUI initialization so changing them doesn't work
        settings_to_show = {k: v for k, v in self.settings.__dict__.items() if k not in ['block', 'style', 'editable']}

        for setting_name, setting in settings_to_show.items():
            if setting.dtype == str:
                widget = self.text_editor(setting)
            elif setting.dtype == bool:
                widget = self.bool_editor(setting)
            elif issubclass(type(setting.dtype), EnumMeta):
                widget = self.enum_editor(setting)
            else:
                raise TypeError
            row = layout.rowCount()
            layout.addWidget(QtWidgets.QLabel(setting.label), row, 0)
            layout.addWidget(widget, row, 1)

        layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding),
                       layout.rowCount(), 0)
        self.setLayout(layout)

    def text_editor(self, setting: Setting):

        def setter(new_val, setting=setting):
            setting.value = new_val

        line_edit = QtWidgets.QLineEdit(setting.value)
        line_edit.textChanged.connect(setter)

        return line_edit

    def bool_editor(self, setting: Setting):

        def setter(new_val, setting=setting):
            setting.value = new_val == Qt.Checked

        checkbox = QtWidgets.QCheckBox(setting.label)
        checkbox.setCheckState(Qt.Checked if setting.value else Qt.Unchecked)
        checkbox.stateChanged.connect(setter)

        return checkbox

    def enum_editor(self, setting: Setting):

        def setter(new_val, setting=setting):
            setting.value = new_val

        combo = QtWidgets.QComboBox()
        combo.addItems([x.name for x in list(setting.dtype)])
        combo.setCurrentText(setting.value)
        combo.currentTextChanged.connect(setter)

        return combo


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    from pandasgui import store

    d = SettingsEditor(SETTINGS_STORE)
    d.show()

    sys.exit(app.exec_())
