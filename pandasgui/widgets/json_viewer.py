import sys
from typing import Union, List
from qtpy import QtCore, QtGui, QtWidgets

from pandasgui.store import PandasGuiStoreItem
from pandasgui.utility import summarize_json, traverse_tree_widget
from pandasgui.widgets import base_widgets

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

class JsonViewer(QtWidgets.QWidget, PandasGuiStoreItem):

    def __init__(self, jdata: Union[list, dict], parent=None):
        super().__init__(parent)

        self.jdata = jdata

        self.search_mode: Literal['filter', 'highlight'] = 'filter'

        self.search_mode_picker = QtWidgets.QComboBox()
        self.search_mode_picker.addItems(['filter', 'highlight'])
        self.search_mode_picker.currentTextChanged.connect(lambda text: [self.__setattr__('search_mode', text),
                                                                         self.find()])

        self.find_box = QtWidgets.QLineEdit()
        self.find_box.returnPressed.connect(self.find)
        self.find_box.textChanged.connect(self.find)
        self.find_box.setPlaceholderText("Find regex")

        self.tree_widget = base_widgets.QTreeWidget()
        self.tree_widget.setHeaderLabels(["Key", "Value"])

        root_item = self.tree_widget.invisibleRootItem()
        self.recurse_jdata(jdata, root_item)
        self.tree_widget.addTopLevelItem(root_item)
        self.tree_widget.expandAll()

        # We call .find after collapse because it will re-expand highlighted items (matching the find_box text)
        self.expand_all = QtWidgets.QPushButton("Expand All")
        self.expand_all.clicked.connect(lambda: [self.tree_widget.expandAll(), self.find()])
        self.collapse_all = QtWidgets.QPushButton("Collapse All")
        self.collapse_all.clicked.connect(lambda: [self.tree_widget.collapseAll(), self.find()])

        top_section = QtWidgets.QHBoxLayout()
        top_section.addWidget(self.find_box)
        top_section.addWidget(self.search_mode_picker)
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

        self.tree_widget.setSelectionMode(QtWidgets.QTreeWidget.ExtendedSelection)

    def find(self):

        text = self.find_box.text()

        if text == "":
            # Unhide and unselect all items
            for item in traverse_tree_widget(self.tree_widget):
                item.setHidden(False)
            self.tree_widget.clearSelection()
            return

        result: List[QtWidgets.QTreeWidgetItem] = []
        for col in range(self.tree_widget.columnCount()):
            result += self.tree_widget.findItems(f".*{text}.*",
                                                 QtCore.Qt.MatchRegExp | QtCore.Qt.MatchRecursive,
                                                 col)

        if self.search_mode == 'highlight':
            # Unhide all items
            for item in traverse_tree_widget(self.tree_widget):
                item.setHidden(False)

            # Highlight matching items
            self.tree_widget.clearSelection()
            self.tree_widget.setSelectionMode(QtWidgets.QTreeWidget.MultiSelection)
            for item in result:
                item.setSelected(True)
            self.tree_widget.setSelectionMode(QtWidgets.QTreeWidget.ExtendedSelection)

        elif self.search_mode == 'filter':
            # Unselect all items
            self.tree_widget.clearSelection()
            # Hide all items
            for item in traverse_tree_widget(self.tree_widget):
                item.setHidden(True)
            # Show matching items and parents
            for item in result:
                while item:
                    item.setHidden(False)
                    item.setExpanded(True)
                    item = item.parent()

        # Expand found items
        for item in result:
            while item:
                item.setExpanded(True)
                item = item.parent()

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

    data = {
        "Employees": [
            {
                "userId": "rirani",
                "jobTitleName": "Developer",
                "firstName": "Romin",
                "lastName": "Irani",
                "preferredFullName": "Romin Irani",
                "employeeCode": "E1",
                "region": "CA",
                "phoneNumber": "408-1234567",
                "emailAddress": "romin.k.irani@gmail.com"
            },
            {
                "userId": "nirani",
                "jobTitleName": "Developer",
                "firstName": "Neil",
                "lastName": "Irani",
                "preferredFullName": "Neil Irani",
                "employeeCode": "E2",
                "region": "CA",
                "phoneNumber": "408-1111111",
                "emailAddress": "neilrirani@gmail.com"
            },
            {
                "userId": "thanks",
                "jobTitleName": "Program Directory",
                "firstName": "Tom",
                "lastName": "Hanks",
                "preferredFullName": "Tom Hanks",
                "employeeCode": "E3",
                "region": "CA",
                "phoneNumber": "408-2222222",
                "emailAddress": "tomhanks@gmail.com"
            }
        ]
    }

    example = JsonViewer(data)
    example.show()


    refs = []
    import requests

    for url in [
        # 'https://jsonplaceholder.typicode.com/posts',  # 100 posts
        # 'https://jsonplaceholder.typicode.com/comments',  # 500 comments
        # 'https://jsonplaceholder.typicode.com/albums',  # 100 albums
        # 'https://jsonplaceholder.typicode.com/photos',  # 5000 photos
        # 'https://jsonplaceholder.typicode.com/todos',  # 200 todos
        # 'https://jsonplaceholder.typicode.com/users',  # 10 users
    ]:
        data = requests.get(url).json()
        x = JsonViewer(data)
        x.show()
        refs.append(x)

    sys.exit(app.exec_())
