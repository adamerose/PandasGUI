"""Dialog box widgets for various GUI functions"""

import re
from PyQt5 import QtCore, QtGui, QtWidgets, sip
from PyQt5.QtCore import Qt
from typing import List
import os
import pandasgui


class Dragger(QtWidgets.QWidget):
    itemDropped = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()

    remembered_values = {}
    source_list_unfiltered = []

    def __init__(self, sources: List[str],
                 destinations: List[str]):
        super().__init__()

        # Ensure no duplicates
        assert (len(sources) == len(set(sources)))
        assert (len(destinations) == len(set(destinations)))

        # Search box
        self.search_box = QtWidgets.QLineEdit()
        self.search_box.textChanged.connect(self.filter)

        # Sources list
        self.source_list = QtWidgets.QListWidget()
        self.set_sources(sources)

        # Depends on Search Box and Source list
        self.filter()

        # Destinations tree
        self.dest_tree = self.DestinationTree(self)
        self.dest_tree.setHeaderLabels(['Name'])
        self.dest_tree.setItemsExpandable(False)
        self.dest_tree.setRootIsDecorated(False)

        self.set_destinations(destinations)

        self.apply_tree_settings()

        # Configure drag n drop
        sorc = self.source_list
        dest = self.dest_tree

        sorc.setDragDropMode(sorc.DragOnly)
        sorc.setSelectionMode(sorc.ExtendedSelection)
        sorc.setDefaultDropAction(QtCore.Qt.CopyAction)
        dest.setDragDropMode(dest.DragDrop)
        dest.setSelectionMode(dest.ExtendedSelection)
        dest.setDefaultDropAction(QtCore.Qt.MoveAction)

        # Buttons
        self.reset_button = QtWidgets.QPushButton("Reset")
        self.finish_button = QtWidgets.QPushButton("Finish")

        # Signals
        self.itemDropped.connect(self.apply_tree_settings)
        self.dest_tree.itemDoubleClicked.connect(self.handle_double_click)
        self.reset_button.clicked.connect(self.reset)
        self.finish_button.clicked.connect(self.finish)

        # Layout
        self.source_list_layout = QtWidgets.QVBoxLayout()
        self.source_list_layout.addWidget(self.search_box)
        self.source_list_layout.addWidget(self.source_list)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addWidget(self.reset_button)
        self.button_layout.addWidget(self.finish_button)

        self.main_layout = QtWidgets.QGridLayout()
        self.main_layout.addLayout(self.source_list_layout, 0, 0)
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

    def filter(self):
        filtered_items = [
            item
            for item in self.source_list_unfiltered
            if re.search(self.search_box.text().lower(), item.lower())
        ]

        self.source_list.clear()
        for name in filtered_items:
            self.source_list.addItem(name)

    def reset(self):

        self.remembered_values = {}
        self.clear_tree()

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

    def finish(self):
        self.finished.emit()

    def apply_tree_settings(self):
        root = self.dest_tree.invisibleRootItem()
        root.setFlags(Qt.ItemIsEnabled)

        for i in range(root.childCount()):
            child = root.child(i)
            child.setExpanded(True)

            child.setFlags(Qt.ItemIsEnabled |
                           Qt.ItemIsDropEnabled)

            for j in range(child.childCount()):
                sub_child = child.child(j)
                sub_child.setFlags(Qt.ItemIsEnabled |
                                   Qt.ItemIsDragEnabled | Qt.ItemIsSelectable)

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

        return data

    def set_sources(self, sources: List[str]):
        self.source_list_unfiltered = sources
        self.filter()

    def set_destinations(self, destinations: List[str], keep_values=True):
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
        # I override dropEvent and dragMoveEvent to fix drops being disabled at edges of
        def dropEvent(self, e: QtGui.QDropEvent):
            super().dropEvent(e)
            self.parent().itemDropped.emit()


class SearchableListWidget(QtWidgets.QWidget):
    def __init__(self, items, parent=None):
        super().__init__(parent)

        self.search_box = QtWidgets.QLineEdit()
        self.search_box.textChanged.connect(self.filter)

        self.list_widget = QtWidgets.QListWidget()

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.search_box)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        self.initial_items = items
        self.set_items(items)

    def filter(self):
        filtered_items = [
            item
            for item in self.initial_items
            if re.search(self.search_box.text().lower(), item.lower())
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

    test = Dragger(sources=pokemon.columns, destinations=["x", "y", "color"])
    test.show()

    sys.exit(app.exec_())
