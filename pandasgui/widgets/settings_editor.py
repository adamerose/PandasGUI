import ast
import pprint

import typing
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
import sys
from typing import Union
from dataclasses import dataclass, is_dataclass
from enum import EnumMeta
from pandasgui.store import SETTINGS_STORE, SettingsStore, Setting
from pandasgui.utility import traverse_tree_widget, resize_widget
from pandasgui.widgets import base_widgets


class SettingsEditor(QtWidgets.QWidget):
    def __init__(self, settings: SettingsStore, parent=None):
        super().__init__(parent)

        self.settings = settings
        self.tree = base_widgets.QTreeWidget()
        self.tree.setHeaderLabels(['Name', 'Value'])
        self.tree.setRootIsDecorated(False)

        finish_button = QtWidgets.QPushButton('Finish')
        finish_button.clicked.connect(self.finish)

        reset_button = QtWidgets.QPushButton('Reset To Defaults')
        reset_button.clicked.connect(self.reset_to_defaults)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tree)
        layout.addWidget(finish_button)
        layout.addWidget(reset_button)

        self.init_tree()

        self.setLayout(layout)

    def init_tree(self):

        self.tree.clear()

        # Dont display these settings because they have effects during the GUI initialization so changing them doesn't work
        settings_to_show = {k: v for k, v in self.settings.__dict__.items() if k not in ['block']}

        # Make a QTreeWidget with widgets in col2 that set its value
        for ix, (setting_name, setting) in enumerate(settings_to_show.items()):

            item = QtWidgets.QTreeWidgetItem(self.tree, [setting_name])
            item.setData(1, Qt.UserRole, setting.value)
            if setting.dtype == str:

                def setter(new_val, item=item):
                    try:
                        item.setData(1, Qt.UserRole, new_val)
                    except:
                        pass

                widget = QtWidgets.QLineEdit(setting.value)
                widget.textChanged.connect(setter)

            elif setting.dtype == dict:

                def setter(new_val, item=item):
                    try:
                        item.setData(1, Qt.UserRole, dict(ast.literal_eval(new_val)))
                    except:
                        pass

                widget = QtWidgets.QPlainTextEdit(pprint.pformat(setting.value))
                widget.textChanged.connect(lambda widget=widget: setter(widget.toPlainText()))

            elif setting.dtype == bool:

                def setter(new_val, item=item):
                    try:
                        item.setData(1, Qt.UserRole, new_val == Qt.Checked)
                    except:
                        pass

                widget = QtWidgets.QCheckBox(setting.label)
                widget.setCheckState(Qt.Checked if setting.value else Qt.Unchecked)
                widget.stateChanged.connect(setter)

            elif typing.get_origin(setting.dtype) == typing.Literal:

                def setter(new_val, item=item):
                    try:
                        item.setData(1, Qt.UserRole, new_val)
                    except:
                        pass

                widget = QtWidgets.QComboBox()
                widget.addItems(typing.get_args(setting.dtype))
                widget.setCurrentText(setting.value)
                widget.currentTextChanged.connect(setter)

            else:
                raise TypeError

            item.treeWidget().setItemWidget(item, 1, widget)

    def finish(self):
        # Get args from destination UI
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            setting_name = item.text(0)
            setting_value = item.data(1, Qt.UserRole)
            self.settings[setting_name].value = setting_value
        self.settings.settingsChanged.emit()

    def reset_to_defaults(self):
        self.settings.reset_to_defaults()
        self.init_tree()
        self.finish()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    from pandasgui import store

    d = SettingsEditor(SETTINGS_STORE)
    d.show()

    sys.exit(app.exec_())
