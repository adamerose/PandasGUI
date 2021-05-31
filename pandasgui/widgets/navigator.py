from PyQt5 import QtCore, QtGui, QtWidgets, sip
from PyQt5.QtCore import Qt

from pandasgui.store import PandasGuiDataFrameStore
from pandasgui.widgets import base_widgets

import tempfile
import os

from pandasgui.utility import traverse_tree_widget
from pynput import mouse


class MouseState(mouse.Listener):
    def __init__(self):
        self.pressed = False
        self.listener = mouse.Listener(on_click=self.on_click)

    def on_click(self, x, y, button, pressed):
        self.pressed = pressed


class DelayedMimeData(QtCore.QMimeData):
    def __init__(self):
        super().__init__()
        self.callbacks = []
        self.mouse_state = MouseState()
        self.mouse_state.listener.start()

    def __del__(self):
        self.mouse_state.listener.stop()

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def retrieveData(self, mime_type: str, preferred_type: QtCore.QVariant.Type):

        if not self.mouse_state.pressed:
            for callback in self.callbacks.copy():
                result = callback()
                if result:
                    self.callbacks.remove(callback)

        return QtCore.QMimeData.retrieveData(self, mime_type, preferred_type)


class Navigator(base_widgets.QTreeWidget):
    def __init__(self, store):
        super().__init__()
        self.store: PandasGuiStore = store
        store.navigator = self

        self.expandAll()
        self.setHeaderLabels(["Name", "Shape"])

        self.header().setStretchLastSection(False)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(self.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(self.ExtendedSelection)
        self.setSelectionBehavior(self.SelectRows)
        self.apply_tree_settings()

        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            pos = event.pos()
            item = self.itemAt(pos)
            ix = self.indexAt(pos)
            if item:
                menu = QtWidgets.QMenu(self)

                action1 = QtWidgets.QAction("Delete DataFrame")
                action1.triggered.connect(lambda: self.store.remove_dataframe(ix.row()))


                for action in [action1]:
                    menu.addAction(action)

                menu.exec_(QtGui.QCursor().pos())

    def showEvent(self, event: QtGui.QShowEvent):
        for i in range(self.columnCount()):
            self.resizeColumnToContents(i)
        event.accept()

    def remove_item(self, name):
        for item in traverse_tree_widget(self):
            if item.text(0) == name:
                sip.delete(item)

    def rowsInserted(self, parent: QtCore.QModelIndex, start: int, end: int):
        super().rowsInserted(parent, start, end)
        self.expandAll()

    def sizeHint(self) -> QtCore.QSize:
        self.header().setStretchLastSection(False)
        width = 5 + sum([self.columnWidth(i) for i in range(self.columnCount())])
        self.header().setStretchLastSection(True)

        return QtCore.QSize(width, super().sizeHint().height())
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
            df = self.store.get_pgdf(name).df

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
