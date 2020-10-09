from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
import tempfile
import os
from pynput import mouse


class MouseState(mouse.Listener):
    def __init__(self):
        self.pressed = False

        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.start()

    def on_click(self, x, y, button, pressed):
        self.pressed = pressed


mouse_state = MouseState()


class DelayedMimeData(QtCore.QMimeData):
    def __init__(self):
        super().__init__()
        self.callbacks = []

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def retrieveData(self, mime_type: str, preferred_type: QtCore.QVariant.Type):

        if not mouse_state.pressed:
            for callback in self.callbacks.copy():
                result = callback()
                if result:
                    self.callbacks.remove(callback)

        return QtCore.QMimeData.retrieveData(self, mime_type, preferred_type)


class Navigator(QtWidgets.QTreeWidget):
    def __init__(self, store):
        super().__init__()
        self.store = store
        store.navigator = self

        self.expandAll()
        self.setHeaderLabels(["Name", "Shape"])
        for i in range(self.columnCount()):
            self.resizeColumnToContents(i)

        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(self.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(self.ExtendedSelection)
        self.setSelectionBehavior(self.SelectRows)
        self.apply_tree_settings()

        self.setColumnWidth(0, 150)
        self.setColumnWidth(1, 150)

    def rowsInserted(self, parent: QtCore.QModelIndex, start: int, end: int):
        super().rowsInserted(parent, start, end)
        self.expandAll()

    def sizeHint(self):
        # Width
        width = 0
        for i in range(self.columnCount()):
            width += self.columnWidth(i)
        return QtCore.QSize(300, 500)

    def apply_tree_settings(self):
        root = self.invisibleRootItem()
        root.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled)

        for i in range(root.childCount()):
            child = root.child(i)
            child.setExpanded(True)

            child.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)

    def selectionChanged(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection) -> None:
        """
        Show the DataFrameExplorer corresponding to the highlighted nav item.
        """
        super().selectionChanged(selected, deselected)

        if len(self.selectedItems()) != 1:
            # Don't change view if user is selecting multiple things using ExtendedSelection (shift / ctrl)
            return

        item = self.selectedItems()[0]
        df_name = item.data(0, Qt.DisplayRole)
        self.store.select_pgdf(df_name)

    def dropEvent(self, e: QtGui.QDropEvent):
        super().dropEvent(e)
        self.apply_tree_settings()

    def startDrag(self, actions):
        drag = QtGui.QDrag(self)
        names = [item.text(0) for item in self.selectedItems()]
        mime = DelayedMimeData()
        path_list = []
        for name in names:
            path = os.path.join(tempfile.gettempdir(), 'DragTest', name + ".csv")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            df = self.store.get_pgdf(name).dataframe

            def write_to_file(path=path, df=df, widget=self):
                if widget.underMouse():
                    return False
                else:
                    df.to_csv(path, index=False)

                    return True

            mime.add_callback(write_to_file)

            path_list.append(QtCore.QUrl.fromLocalFile(path))
        mime.setUrls(path_list)
        mime.setData('application/x-qabstractitemmodeldatalist',
                     self.mimeData(self.selectedItems()).data('application/x-qabstractitemmodeldatalist'))
        drag.setMimeData(mime)
        drag.exec_(Qt.MoveAction)
