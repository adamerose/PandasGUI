from PyQt5 import QtCore, QtWidgets, QtGui
import pandas as pd
import sys

class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        layout = QtWidgets.QVBoxLayout()

        # Create a string list model and show it in 3 views
        data = ["one", "two", "three"]
        model = QtCore.QStringListModel(data)

        listView = QtWidgets.QListView()
        listView.setModel(model)

        listView2 = QtWidgets.QListView()
        listView2.setModel(model)

        combobox = QtWidgets.QComboBox()
        combobox.setModel(model)

        # Add widgets to main window and show it
        for item in [listView, listView2, combobox]:
            layout.addWidget(item)
        self.setLayout(layout)
        self.show()

if __name__ == '__main__':
    print(QtWidgets.QStyleFactory.keys())
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Windows")

    window = Window()
    sys.exit(app.exec_())

