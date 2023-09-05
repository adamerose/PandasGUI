from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt


class DockWidget(QtWidgets.QDockWidget):
    # This signal is used to track which dock is considered active or focussed
    activated = QtCore.pyqtSignal()

    def __init__(self, title: str, pgdf_name: str = 'Untitled'):
        super().__init__(title)
        self.title = title
        self.pgdf_name = pgdf_name

        self.setTitleBarWidget(QtWidgets.QWidget())
        self.dockLocationChanged.connect(self.on_dockLocationChanged)
        self.setFeatures(self.DockWidgetFloatable |
                         self.DockWidgetMovable |
                         self.DockWidgetClosable)

        self.visibilityChanged.connect(lambda visible: visible and self.activated.emit())

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            self.activated.emit()
        return super().eventFilter(obj, event)

    def setWidget(self, widget) -> None:
        temp = super().setWidget(widget)
        for w in self.findChildren(QtWidgets.QWidget) + [self]:
            w.installEventFilter(self)
        return temp

    def on_dockLocationChanged(self):
        main: QtWidgets.QMainWindow = self.parent()
        all_dock_widgets = main.findChildren(QtWidgets.QDockWidget)

        for dock_widget in all_dock_widgets:
            sibling_tabs = main.tabifiedDockWidgets(dock_widget)
            # If you pull a tab out of a group the other tabs still see it as a sibling while dragging...
            sibling_tabs = [s for s in sibling_tabs if not s.isFloating()]

            if len(sibling_tabs) != 0:
                # Hide title bar
                dock_widget.setTitleBarWidget(QtWidgets.QWidget())
            else:
                # Re-enable title bar
                dock_widget.setTitleBarWidget(None)

        if self.isFloating():
            self.setWindowTitle(f"{self.title} ({self.pgdf_name})")
        else:
            self.setWindowTitle(self.title)

    def minimumSizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(100, 100)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        event.ignore()
        main: QtWidgets.QMainWindow = self.parent()
        dock_widgets = main.findChildren(QtWidgets.QDockWidget)
        dock_widgets = [w for w in dock_widgets if not w.isFloating()]

        self.setFloating(False)
        if len(dock_widgets) > 0:
            if self != dock_widgets[0]:
                main.tabifyDockWidget(dock_widgets[0], self)
            else:
                main.tabifyDockWidget(dock_widgets[1], self)
        else:
            main.addDockWidget(Qt.LeftDockWidgetArea, self)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    main = QtWidgets.QMainWindow()

    dock1 = DockWidget("Blue")
    dock2 = DockWidget("Green")
    dock3 = DockWidget("Red")

    content1 = QtWidgets.QWidget()
    content1.setStyleSheet("background-color:blue;")
    content1.setMinimumSize(QtCore.QSize(50, 50))

    content2 = QtWidgets.QWidget()
    content2.setStyleSheet("background-color:green;")
    content2.setMinimumSize(QtCore.QSize(50, 50))

    content3 = QtWidgets.QWidget()
    content3.setStyleSheet("background-color:red;")
    content3.setMinimumSize(QtCore.QSize(50, 50))

    dock1.setWidget(content1)
    dock2.setWidget(content2)
    dock3.setWidget(content3)

    dock1.setAllowedAreas(Qt.AllDockWidgetAreas)
    dock2.setAllowedAreas(Qt.AllDockWidgetAreas)
    dock3.setAllowedAreas(Qt.AllDockWidgetAreas)

    main.addDockWidget(Qt.RightDockWidgetArea, dock1)
    main.tabifyDockWidget(dock1, dock2)
    main.addDockWidget(Qt.RightDockWidgetArea, dock3)

    main.setDockOptions(main.GroupedDragging | main.AllowTabbedDocks | main.AllowNestedDocks)

    main.setTabPosition(Qt.AllDockWidgetAreas, QtWidgets.QTabWidget.North)
    main.resize(400, 200)
    main.show()

    app.exec_()
