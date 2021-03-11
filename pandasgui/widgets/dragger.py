"""Dialog box widgets for various GUI functions"""

import re
from PyQt5 import QtCore, QtGui, QtWidgets, sip
from PyQt5.QtCore import Qt
from typing import List, Callable
import os

from pandasgui.utility import nunique

import pandasgui
import ast
from typing import Union, List, Iterable
from dataclasses import dataclass, field

from pandasgui.widgets import base_widgets


@dataclass
class ColumnArg:
    arg_name: str


@dataclass
class OptionListArg:
    arg_name: str
    values: List[str]


@dataclass
class BooleanArg:
    arg_name: str
    default_value: bool


# This schema is made up of multiple args, this defines all the drop zones available in the Dragger
@dataclass
class Schema:
    name: str = "Untitled"
    args: List[Union[ColumnArg, OptionListArg, BooleanArg]] = field(default_factory=list)
    label: str = "Untitled"
    function: Callable = None
    icon_path: str = "Untitled"


class Dragger(QtWidgets.QWidget):
    itemDropped = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()
    saving = QtCore.pyqtSignal()

    def __init__(self, sources: List[str],
                 schema: Schema, source_nunique: List[str], source_types: List[str]):
        super().__init__()
        self.schema = schema
        self.remembered_values = {}
        self.source_tree_unfiltered = []

        # Ensure no duplicates
        assert (len(sources) == len(set(sources)))
        assert (len(sources) == len(source_nunique))
        assert (len(sources) == len(source_types))

        # Custom kwargs dialog
        self.kwargs_dialog = self.CustomKwargsEditor(self)

        # Search box
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.textChanged.connect(self.filter)

        # Sources list
        self.source_tree = self.SourceTree(self)
        self.source_tree.setHeaderLabels(['Name', '#Unique', 'Type'])
        self.set_sources(sources, source_nunique, source_types)
        self.source_tree.setSortingEnabled(True)

        # Depends on Search Box and Source list
        self.filter()

        # Destinations tree
        self.dest_tree = self.DestinationTree(self)
        self.dest_tree.setHeaderLabels(['Name', '', ''])
        self.dest_tree.setColumnHidden(1, True)
        self.dest_tree.setColumnHidden(2, True)
        self.dest_tree.setItemsExpandable(False)
        self.dest_tree.setRootIsDecorated(False)

        self.set_schema(schema)
        self.apply_tree_settings()

        # Configure drag n drop
        sorc = self.source_tree
        dest = self.dest_tree

        sorc.setDragDropMode(sorc.DragOnly)
        sorc.setSelectionMode(sorc.ExtendedSelection)
        sorc.setDefaultDropAction(QtCore.Qt.CopyAction)
        dest.setDragDropMode(dest.DragDrop)
        dest.setSelectionMode(dest.ExtendedSelection)
        dest.setDefaultDropAction(QtCore.Qt.MoveAction)

        # Buttons
        self.kwargs_button = QtWidgets.QPushButton("Custom Kwargs")
        self.reset_button = QtWidgets.QPushButton("Reset")
        self.save_html_button = QtWidgets.QPushButton("Save HTML")
        self.finish_button = QtWidgets.QPushButton("Finish")

        # Signals
        self.itemDropped.connect(self.apply_tree_settings)
        self.dest_tree.itemChanged.connect(self.remember_values)
        self.dest_tree.itemDoubleClicked.connect(self.handle_double_click)
        self.kwargs_button.clicked.connect(self.custom_kwargs)
        self.reset_button.clicked.connect(self.reset)
        self.save_html_button.clicked.connect(self.save_html)
        self.finish_button.clicked.connect(self.finish)

        # Layout
        self.source_tree_layout = QtWidgets.QVBoxLayout()
        self.source_tree_layout.addWidget(self.search_bar)
        self.source_tree_layout.addWidget(self.source_tree)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addWidget(self.kwargs_button)
        self.button_layout.addWidget(self.reset_button)
        self.button_layout.addWidget(self.save_html_button)
        self.button_layout.addWidget(self.finish_button)

        self.main_layout = QtWidgets.QGridLayout()
        self.main_layout.addLayout(self.source_tree_layout, 0, 0)
        self.main_layout.addWidget(self.dest_tree, 0, 1)
        self.main_layout.addLayout(self.button_layout, 1, 0, 1, 2)

        self.setLayout(self.main_layout)

    def handle_double_click(self, item, column):

        # Delete chldren if is section
        if item.parent() is None:
            for i in reversed(range(item.childCount())):
                sip.delete(item.child(i))
        # Delete if not section
        else:
            sip.delete(item)

        self.apply_tree_settings()

    def filter(self):
        root = self.source_tree.invisibleRootItem()
        for i in range(root.childCount()):
            child = root.child(i)
            child.setHidden(True)

        items = self.source_tree.findItems(f".*{self.search_bar.text()}.*",
                                           Qt.MatchRegExp | Qt.MatchRecursive)
        for item in items:
            item.setHidden(False)

    # Clear tree items under each sections
    def clear_tree(self):
        root = self.dest_tree.invisibleRootItem()
        to_delete = []
        for i in range(root.childCount()):
            child = root.child(i)
            for j in range(child.childCount()):
                sub_child = child.child(j)
                to_delete.append(sub_child)

        for item in to_delete:
            sip.delete(item)

    def custom_kwargs(self):
        self.kwargs_dialog.setVisible(not self.kwargs_dialog.isVisible())

    def reset(self):
        self.remembered_values = {}
        self.clear_tree()

    def finish(self):
        self.finished.emit()

    def save_html(self):
        self.saving.emit()

    def apply_tree_settings(self):
        if len(self.schema.args) == 0:
            return

        # Destination tree
        root = self.dest_tree.invisibleRootItem()
        root.setFlags(root.flags() & Qt.ItemIsEnabled)

        for i in range(root.childCount()):
            child = root.child(i)
            child.setExpanded(True)

            arg = next(arg for arg in self.schema.args if arg.arg_name == child.text(0))
            if type(arg) == ColumnArg:
                child.setFlags(child.flags() & Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled
                               & ~Qt.ItemIsDragEnabled)

                for j in range(child.childCount()):
                    sub_child = child.child(j)
                    sub_child.setFlags(
                        sub_child.flags() & Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)

            if type(arg) == BooleanArg:
                child.setFlags(child.flags() & Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
                               & ~Qt.ItemIsDragEnabled & ~Qt.ItemIsDropEnabled)
                for j in range(child.childCount()):
                    sub_child = child.child(j)
                    sub_child.setFlags(
                        sub_child.flags() & Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)

        # Source tree
        root = self.source_tree.invisibleRootItem()
        root.setFlags(root.flags() & Qt.ItemIsEnabled)

        for i in range(root.childCount()):
            child = root.child(i)
            child.setFlags(child.flags() & Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)

        self.remember_values()

    def remember_values(self):
        self.remembered_values.update(self.get_data())

    def get_data(self):
        data = {}

        # Get args from destination UI
        root = self.dest_tree.invisibleRootItem()
        for i in range(root.childCount()):
            child = root.child(i)
            section = child.text(0)

            arg = next(arg for arg in self.schema.args if arg.arg_name == child.text(0))

            if type(arg) == ColumnArg:
                data[section] = []
                for j in range(child.childCount()):
                    sub_child = child.child(j)
                    value = sub_child.text(0)
                    data[section].append(value)

            if type(arg) == BooleanArg:
                data[section] = child.checkState(0) == Qt.Checked

        # Add custom kwargs
        root = self.kwargs_dialog.tree_widget.invisibleRootItem()
        for i in range(root.childCount()):
            child = root.child(i)
            key = child.text(0)
            value = child.text(1)
            try:
                value = ast.literal_eval(value)
            except (SyntaxError, ValueError):
                pass

            data[key] = value

        return data

    def set_sources(self, sources: List[str], source_nunique: List[str], source_types: List[str]):

        for i in range(len(sources)):
            item = base_widgets.QTreeWidgetItem(self.source_tree,
                                             [str(sources[i]), str(source_nunique[i]), str(source_types[i])])

        self.filter()

    def set_schema(self, schema: Schema):
        self.schema = schema

        # Delete all sections
        root = self.dest_tree.invisibleRootItem()
        for i in reversed(range(root.childCount())):
            sip.delete(root.child(i))

        for arg in schema.args:
            if type(arg) == ColumnArg:
                section = base_widgets.QTreeWidgetItem(self.dest_tree, [arg.arg_name])
                if arg.arg_name in self.remembered_values.keys():
                    for val in self.remembered_values[arg.arg_name]:
                        item = base_widgets.QTreeWidgetItem(section, [val])

            elif type(arg) == BooleanArg:
                section = base_widgets.QTreeWidgetItem(self.dest_tree, [arg.arg_name])
                if arg.arg_name in self.remembered_values.keys():
                    # Use remembered value
                    val = self.remembered_values[arg.arg_name]
                    section.setCheckState(0, Qt.Checked if val else Qt.Unchecked)
                else:
                    # Use default value
                    val = arg.default_value
                    section.setCheckState(0, Qt.Checked if val else Qt.Unchecked)
                section.setFlags(section.flags() | Qt.ItemIsUserCheckable)

        self.apply_tree_settings()

    class DestinationTree(base_widgets.QTreeWidget):
        def dropEvent(self, e: QtGui.QDropEvent):
            super().dropEvent(e)
            self.parent().itemDropped.emit()

    class SourceTree(base_widgets.QTreeWidget):
        def dropEvent(self, e: QtGui.QDropEvent):
            super().dropEvent(e)
            self.parent().itemDropped.emit()

    class CustomKwargsEditor(QtWidgets.QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setVisible(False)
            self.setWindowTitle("Custom Kwargs")

            self.tree_widget = QtWidgets.QTreeWidget()
            self.tree_widget.setHeaderLabels(['Kwarg Name', 'Kwarg Value'])
            self.kwarg_name = QtWidgets.QLineEdit()
            self.kwarg_value = QtWidgets.QLineEdit()
            self.submit_button = QtWidgets.QPushButton("Add")
            self.delete_button = QtWidgets.QPushButton("Delete")

            # Signals
            self.kwarg_name.returnPressed.connect(self.add_item)
            self.kwarg_value.returnPressed.connect(self.add_item)
            self.submit_button.pressed.connect(self.add_item)
            self.delete_button.pressed.connect(self.delete)

            # Layout
            self.layout = QtWidgets.QVBoxLayout()
            self.input_layout = QtWidgets.QHBoxLayout()
            self.input_layout.addWidget(self.kwarg_name)
            self.input_layout.addWidget(self.kwarg_value)
            self.input_layout.addWidget(self.submit_button)
            self.layout.addLayout(self.input_layout)
            self.layout.addWidget(self.tree_widget)
            self.layout.addWidget(self.delete_button)
            self.setLayout(self.layout)

        def add_item(self):
            name = self.kwarg_name.text()
            value = self.kwarg_value.text()

            if name != "" and value != "":
                self.kwarg_name.setText("")
                self.kwarg_value.setText("")

                item = base_widgets.QTreeWidgetItem(self.tree_widget, [name, value])

                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)

        def delete(self):
            for item in self.tree_widget.selectedItems():
                sip.delete(item)


class SearchableListWidget(QtWidgets.QWidget):
    def __init__(self, items, parent=None):
        super().__init__(parent)

        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.textChanged.connect(self.filter)

        self.list_widget = QtWidgets.QListWidget()

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        self.initial_items = items
        self.set_items(items)

    def filter(self):
        filtered_items = [
            item
            for item in self.initial_items
            if re.search(self.search_bar.text().lower(), item.lower())
        ]

        self.set_items(filtered_items)

    def get_items(self):
        return [
            str(self.list_widget.item(i).text())
            for i in range(self.list_widget.count())
        ]

    def set_items(self, items):
        self.list_widget.clear()
        for name in items:
            self.list_widget.addItem(name)


class SourceList(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Settings
        self.setDragDropMode(self.DragDrop)
        self.setSelectionMode(self.ExtendedSelection)
        self.setDefaultDropAction(QtCore.Qt.CopyAction)
        self.setAcceptDrops(True)

    def dropEvent(self, event):
        itemsTextList = self.getItems()

        # Default action
        QtWidgets.QListWidget.dropEvent(self, event)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from pandasgui.datasets import pokemon

    app = QApplication(sys.argv)

    test = Dragger(sources=pokemon.columns,
                   schema=Schema(name='line',
                                 args=[ColumnArg(arg_name='x'),
                                       ColumnArg(arg_name='y'),
                                       ColumnArg(arg_name='color'),
                                       BooleanArg(arg_name='apply_mean', default_value=True)], ),
                   source_nunique=nunique(pokemon),
                   source_types=pokemon.dtypes.values.astype(str))
    test.finished.connect(lambda: print(test.get_data()))
    test.show()

    sys.exit(app.exec_())
