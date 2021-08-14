from PyQt5 import QtWidgets


class CollapsiblePanel(QtWidgets.QGroupBox):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setTitle(title)

        self.contents_widget = QtWidgets.QWidget(self)
        self.toggled.connect(self.on_toggled)
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.contents_widget)

    def setContent(self, widget) -> None:
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(widget)
        self.contents_widget.setLayout(layout)
        super().setLayout(self.layout)

    def on_toggled(self, checked: bool = ...) -> None:
        if checked:
            self.contents_widget.show()
        else:
            self.contents_widget.hide()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    x = CollapsiblePanel("title")
    w = QtWidgets.QLineEdit("asdf")
    x.setContent(w)
    x.show()
    app.exec_()
