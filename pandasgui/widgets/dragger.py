"""Dialog box widgets for various GUI functions"""

import re
from PyQt5 import QtCore, QtGui, QtWidgets, sip
from PyQt5.QtCore import Qt
from typing import List, Callable
import os
import pandasgui
import ast
from typing import Union, List, Iterable
from dataclasses import dataclass


# All argument schemas inherit from this
@dataclass
class Arg:
    arg_name: str


@dataclass
class ColumnArg(Arg):
    pass


@dataclass
class OptionListArg(Arg):
    values: List[str]


@dataclass
class Schema:
    name: str
    args: List[Arg]
    label: str
    function: Callable
    icon_path: str


class Dragger(QtWidgets.QWidget):
    itemDropped = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()

    def __init__(self, sources: List[str],
                 destinations: List[str], source_types: List[str]):
        super().__init__()
        self.remembered_values = {}
        self.source_tree_unfiltered = []

        # Ensure no duplicates
        assert (len(sources) == len(set(sources)))
        assert (len(destinations) == len(set(destinations)))
        assert (len(sources) == len(source_types))

        # Custom kwargs dialog
        self.kwargs_dialog = self.CustomKwargsEditor(self)

        # Search box
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.textChanged.connect(self.filter)

        # Sources list
        self.source_tree = self.SourceTree(self)
        self.source_tree.setHeaderLabels(['Name', 'Type'])
        self.set_sources(sources, source_types)
        self.source_tree.setSortingEnabled(True)

        # Depends on Search Box and Source list
        self.filter()

        # Destinations tree
        self.dest_tree = self.DestinationTree(self)
        self.dest_tree.setHeaderLabels(['Name', ''])
        self.dest_tree.setColumnHidden(1, True)
        self.dest_tree.setItemsExpandable(False)
        self.dest_tree.setRootIsDecorated(False)

        self.set_destinations(destinations)
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
        self.finish_button = QtWidgets.QPushButton("Finish")

        # Signals
        self.itemDropped.connect(self.apply_tree_settings)
        self.dest_tree.itemDoubleClicked.connect(self.handle_double_click)
        self.kwargs_button.clicked.connect(self.custom_kwargs)
        self.reset_button.clicked.connect(self.reset)
        self.finish_button.clicked.connect(self.finish)

        # Layout
        self.source_tree_layout = QtWidgets.QVBoxLayout()
        self.source_tree_layout.addWidget(self.search_bar)
        self.source_tree_layout.addWidget(self.source_tree)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addWidget(self.kwargs_button)
        self.button_layout.addWidget(self.reset_button)
        self.button_layout.addWidget(self.finish_button)

        self.main_layout = QtWidgets.QGridLayout()
        self.main_layout.addLayout(self.source_tree_layout, 0, 0)
        self.main_layout.addWidget(self.dest_tree, 0, 1)
        self.main_layout.addLayout(self.button_layout, 1, 0, 1, 2)

        self.setLayout(self.main_layout)

        image_dir = os.path.join(pandasgui.__path__[0], 'images')
        # Styling (https://doc.qt.io/qt-5/stylesheet-examples.html#customizing-qtreeview)
        stylesheet = """
                                     QTreeView::branch:has-siblings:adjoins-item {
                                         border-image: url(%s) 0;
                                     }

                                     QTreeView::branch:!has-children:!has-siblings:adjoins-item {
                                         border-image: url(%s) 0;
                                     }

                                     QTreeView { background-color: white; padding: 0px 5px; }
                                     """ % (
            os.path.join(image_dir, "stylesheet-branch-more.png").replace("\\", "/"),
            os.path.join(image_dir, "stylesheet-branch-end.png").replace("\\", "/"),
        )
        self.dest_tree.setStyleSheet(stylesheet)

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

    def apply_tree_settings(self):
        # Destination tree
        root = self.dest_tree.invisibleRootItem()
        root.setFlags(Qt.ItemIsEnabled)

        for i in range(root.childCount()):
            child = root.child(i)
            child.setExpanded(True)

            child.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled)

            for j in range(child.childCount()):
                sub_child = child.child(j)
                sub_child.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)

        # Source tree
        root = self.source_tree.invisibleRootItem()
        root.setFlags(Qt.ItemIsEnabled)

        for i in range(root.childCount()):
            child = root.child(i)
            child.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)

        # Remember values
        self.remembered_values.update(self.get_data())

    def get_data(self):
        data = {}

        root = self.dest_tree.invisibleRootItem()
        for i in range(root.childCount()):
            child = root.child(i)
            section = child.text(0)
            data[section] = []

            for j in range(child.childCount()):
                sub_child = child.child(j)
                value = sub_child.text(0)
                data[section].append(value)

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

    def set_sources(self, sources: List[str], source_types: List[str]):

        for i in range(len(sources)):
            item = QtWidgets.QTreeWidgetItem(self.source_tree,
                                             [str(sources[i]), str(source_types[i])])

        self.filter()

    def set_destinations(self, destinations: List[str]):
        # Delete all sections
        root = self.dest_tree.invisibleRootItem()
        for i in reversed(range(root.childCount())):
            sip.delete(root.child(i))

        for dest in destinations:
            section = QtWidgets.QTreeWidgetItem(self.dest_tree, [dest])

            if dest in self.remembered_values.keys():
                for val in self.remembered_values[dest]:
                    item = QtWidgets.QTreeWidgetItem(section, [val])

        self.apply_tree_settings()

    class DestinationTree(QtWidgets.QTreeWidget):
        def dropEvent(self, e: QtGui.QDropEvent):
            super().dropEvent(e)
            self.parent().itemDropped.emit()

    class SourceTree(QtWidgets.QTreeWidget):
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

                item = QtWidgets.QTreeWidgetItem(self.tree_widget, [name, value])

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

    test = Dragger(sources=pokemon.columns, destinations=["x", "y", "color"],
                   source_types=pokemon.dtypes.values.astype(str))
    test.finished.connect(lambda: print(test.get_data()))
    test.show()

    sys.exit(app.exec_())
