def __init__(self):
    super().__init__()
    self.setupUi(self)
    self.show()


import sys
app = QtWidgets.QApplication(sys.argv)
win = Ui_scatterDialog()
app.exec_()