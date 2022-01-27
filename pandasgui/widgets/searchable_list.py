import re
from qtpy import QtWidgets


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


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication

    app = QApplication(sys.argv)

    test = SearchableListWidget(['cat', 'dog', 'hotdog', 'catch'])
    test.show()

    sys.exit(app.exec_())
