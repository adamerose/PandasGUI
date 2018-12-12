from PyQt5 import QtWidgets, QtGui, QtCore


class GUI(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.show()
        for num in range(5):
            b = QtWidgets.QPushButton(str(num))
            b.clicked.connect(lambda: self.func(num))
            layout.addWidget(b)

    def func(self, thing):
        print(thing)


app = QtWidgets.QApplication([])
win = GUI()
app.exec_()