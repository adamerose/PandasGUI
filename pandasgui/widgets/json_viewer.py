import collections
import json
import sys
from typing import Union
from PyQt5 import QtCore, QtGui, QtWidgets


class JsonViewer(QtWidgets.QWidget):

    def __init__(self, jdata: Union[list, dict], parent=None):
        super().__init__(parent)

        self.find_box = QtWidgets.QLineEdit()
        self.find_box.returnPressed.connect(self.find)
        self.find_box.textChanged.connect(self.find)
        self.find_box.setPlaceholderText("Find")

        self.tree_widget = QtWidgets.QTreeWidget()
        self.tree_widget.setHeaderLabels(["Key", "Value"])
        self.tree_widget.header().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        root_item = self.tree_widget.invisibleRootItem()
        self.recurse_jdata(jdata, root_item)
        self.tree_widget.addTopLevelItem(root_item)
        self.tree_widget.expandAll()

        self.expand_all = QtWidgets.QPushButton("Expand All")
        self.expand_all.clicked.connect(self.tree_widget.expandAll)
        self.collapse_all = QtWidgets.QPushButton("Collapse All")
        self.collapse_all.clicked.connect(self.tree_widget.collapseAll)

        top_section = QtWidgets.QHBoxLayout()
        top_section.addWidget(self.find_box)
        top_section.addWidget(self.expand_all)
        top_section.addWidget(self.collapse_all)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(top_section)
        layout.addWidget(self.tree_widget)

        self.setLayout(layout)

        self.resize(QtCore.QSize(400,500))

        self.show()


    def find(self):

        text = self.find_box.text()

        if text == "":
            self.tree_widget.clearSelection()
            return

        result = []
        for col in [0,1]:
            result += self.tree_widget.findItems(text,
                                                 QtCore.Qt.MatchRegExp | QtCore.Qt.MatchRecursive,
                                                 col)
        self.tree_widget.clearSelection()
        self.tree_widget.setSelectionMode(self.tree_widget.MultiSelection)

        for item in result:
            item.setSelected(True)

        self.tree_widget.setSelectionMode(self.tree_widget.ExtendedSelection)

    def recurse_jdata(self, jdata, tree_widget):

        if isinstance(jdata, dict):
            items = jdata.items()
        elif isinstance(jdata, list):
            items = [(str(i), val) for i, val in enumerate(jdata)]
        else:
            raise ValueError(f"Expected dict or list, instead got {type(jdata)}")

        for key, val in items:
            text_list = []

            if isinstance(val, dict) or isinstance(val, list):
                text_list.append(key)
                row_item = QtWidgets.QTreeWidgetItem([key])
                self.recurse_jdata(val, row_item)
            else:
                text_list.append(key)
                text_list.append(str(val))
                row_item = QtWidgets.QTreeWidgetItem([key, str(val)])

            tree_widget.addChild(row_item)


if "__main__" == __name__:
    qt_app = QtWidgets.QApplication(sys.argv)
    data_list = [{
        "name": "Tim",
        "age": 22,
        "cars": {
            "car1": "Mazda",
        }
    }, {
        "name": "John",
        "age": 30,
        "cars": {
            "car1": "Ford",
            "car2": "BMW",
            "car3": "Fiat"
        }
    }]

    data_dict = {
        "name": "Tim",
        "age": 22,
        "cars": {
            "car1": "Mazda",
        }
    }
    json_viewer = JsonViewer(data_list)
    json_viewer2 = JsonViewer(data_dict)
    sys.exit(qt_app.exec_())
