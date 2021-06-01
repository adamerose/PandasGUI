import collections
import json
import sys
from typing import Union
from PyQt5 import QtCore, QtGui, QtWidgets

from pandasgui.store import PandasGuiStoreItem
from pandasgui.utility import summarize_json


class JsonViewer(QtWidgets.QWidget, PandasGuiStoreItem):

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

        main_view_layout = QtWidgets.QVBoxLayout()
        main_view_layout.addLayout(top_section)
        main_view_layout.addWidget(self.tree_widget)

        main_view = QtWidgets.QWidget()
        main_view.setLayout(main_view_layout)

        summary_view = QtWidgets.QTextEdit()
        summary_view.setReadOnly(True)
        summary_view.setText(summarize_json(jdata))

        font = QtGui.QFont("Monospace")
        font.setStyleHint(QtGui.QFont.TypeWriter)
        summary_view.setFont(font)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(main_view, "Viewer")
        self.tabs.addTab(summary_view, "Structure")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tabs)

        self.setLayout(layout)
        self.resize(QtCore.QSize(400, 500))

    def find(self):

        text = self.find_box.text()

        if text == "":
            self.tree_widget.clearSelection()
            return

        result = []
        for col in [0, 1]:
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

    def pg_widget(self):
        return self

if "__main__" == __name__:
    app = QtWidgets.QApplication([])

    example1 = [{'apiVersion': 3,
                 'details': {'date': '2012-04-23T18:25:43.511Z', 'userCount': 3},
                 'users': [
                     {'id': 'jross',
                      'firstName': "Jeff",
                      'lastName': "Reeves",
                      'messages': [
                          {'content': "Hello",
                           'date_posted': "2012-04-23T18:25:43.511Z"},
                          {'content': "I finished the thing",
                           'date_posted': "2012-04-23T18:29:43.511Z"},
                          {'content': "Here it is",
                           'date_posted': "2012-04-23T18:30:43.511Z",
                           'error': "Failed to send message"},
                      ]},
                     {'id': 'sbank',
                      'firstName': "Steve",
                      'lastName': "Banks",
                      'messages': [
                          {'content': "Hi",
                           'date_posted': "2012-04-23T18:26:43.511Z"},
                      ]},
                     {'id': 'bscot',
                      'firstName': "Bob",
                      'messages': []},
                 ]}]

    json_viewer = JsonViewer(example1)
    json_viewer.show()

    import requests

    examples = []
    for url in ['https://jsonplaceholder.typicode.com/posts',  # 100 posts
                'https://jsonplaceholder.typicode.com/comments',  # 500 comments
                'https://jsonplaceholder.typicode.com/albums',  # 100 albums
                'https://jsonplaceholder.typicode.com/photos',  # 5000 photos
                'https://jsonplaceholder.typicode.com/todos',  # 200 todos
                'https://jsonplaceholder.typicode.com/users',  # 10 users
                ]:
        data = requests.get(url).json()
        x = JsonViewer(data)
        x.show()
        examples.append(x)

    sys.exit(app.exec_())
