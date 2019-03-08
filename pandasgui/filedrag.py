"""
A simple example pyside app that demonstrates dragging and dropping
of files onto a GUI.
- This app allows dragging and dropping of an image file
that this then displayed in the GUI
- Alternatively an image can be loaded using the button
- This app includes a workaround for using pyside for dragging and dropping
with OSx
- This app should work on Linux, Windows and OSx
"""

from __future__ import division, unicode_literals, print_function, absolute_import

from PyQt5 import QtWidgets, QtCore
import sys
import platform

class MainWindowWidget(QtWidgets.QWidget):
    """
    Subclass the widget and add a button to load images.

    Alternatively set up dragging and dropping of image files onto the widget
    """

    def __init__(self):
        super(MainWindowWidget, self).__init__()

        # Enable dragging and dropping onto the GUI
        self.setAcceptDrops(True)

        self.show()

    # The following three methods set up dragging and dropping for the app
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        """
        Drop files directly onto the widget
        File locations are stored in fname
        :param e:
        :return:
        """
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
            # Workaround for OSx dragging and dropping
            for url in e.mimeData().urls():
                fname = str(url.toLocalFile())

            print(fname)
        else:
            e.ignore()


# Run if called directly
if __name__ == '__main__':
    # Initialise the application
    app = QtWidgets.QApplication(sys.argv)
    # Call the widget
    ex = MainWindowWidget()
    sys.exit(app.exec_())