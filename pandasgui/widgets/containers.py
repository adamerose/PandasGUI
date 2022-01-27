from qtpy import QtWidgets


class Container(QtWidgets.QGroupBox):
    def __init__(self, widget, title):
        super().__init__()

        self.setTitle(title)
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setFlat(True)
