
from PyQt5 import QtCore, QtGui, QtWidgets, sip
from PyQt5.QtCore import Qt

from pandasgui.store import PandasGuiDataFrameStore, PandasGuiStore
from pandasgui.widgets import base_widgets

import tempfile
import os

from pandasgui.utility import traverse_tree_widget
from pandasgui.widgets.column_viewer import FlatDraggableTree
from pandasgui.widgets.json_viewer import JsonViewer

# Use win32api on Windows because the pynput and mouse packages cause lag with PyQt drag-n-drop
# https://github.com/moses-palmer/pynput/issues/390
if os.name == 'nt':
    import win32api


    def mouse_pressed():
        return win32api.GetKeyState(0x01) not in [0, 1]
else:
    from pynput import mouse


    class MouseState(mouse.Listener):
        def __init__(self):
            self.pressed = False
            self.listener = mouse.Listener(on_click=self.on_click)
            self.listener.start()

        def on_click(self, x, y, button, pressed):
            self.pressed = pressed


    mouse_state = MouseState()


    def mouse_pressed():
        return mouse_state.pressed



class DelayedMimeData(QtCore.QMimeData):

    def __init__(self):
        super().__init__()
        self.callbacks = []

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def retrieveData(self, mime_type: str, preferred_type: QtCore.QVariant.Type):
        if not mouse_pressed():
            for callback in self.callbacks.copy():
                self.callbacks.remove(callback)
                callback()

        return QtCore.QMimeData.retrieveData(self, mime_type, preferred_type)

class Navigator(FlatDraggableTree):
    def __init__(self, store):
        super().__init__()
        self.store: PandasGuiStore = store
        store.navigator = self

        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDefaultDropAction(Qt.MoveAction)

        self.setHeaderLabels(['Name', 'Shape'])
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

        super().mouseReleaseEvent(event)

    def remove_item(self, name):
        for item in traverse_tree_widget(self):
            if item.text(0) == name:
                sip.delete(item)

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

    # Set CSV data in the case that the user is dragging DataFrames out of the GUI into a file folder
    def startDrag(self, actions):
        drag = QtGui.QDrag(self)
        names = [item.text(0) for item in self.selectedItems()]
        mime = DelayedMimeData()
        path_list = []
        for name in names:
            item = self.store.data[name]
            if isinstance(item, PandasGuiDataFrameStore):
                extension = ".csv"
            elif isinstance(item, JsonViewer):
                extension = ".json"
            else:
                raise ValueError

            file_name = name + extension
            path = os.path.join(tempfile.gettempdir(), 'DragTest', file_name)
            os.makedirs(os.path.dirname(path), exist_ok=True)

            def write_to_file(path=path, item=item, widget=self, file_name=file_name):
                with widget.store.status_message_context(f'Exporting {file_name}...'):
                    if isinstance(item, PandasGuiDataFrameStore):
                        item.df.to_csv(path, index=False)

                    elif isinstance(item, JsonViewer):
                        import json
                        with open(path, 'w') as f:
                            json.dump(item.jdata, f)
                    else:
                        pass

            mime.add_callback(write_to_file)
            path_list.append(QtCore.QUrl.fromLocalFile(path))

        mime.setUrls(path_list)
        mime.setData('application/x-qabstractitemmodeldatalist',
                     self.mimeData(self.selectedItems()).data('application/x-qabstractitemmodeldatalist'))
        drag.setMimeData(mime)
        drag.exec_(Qt.MoveAction)
        super().startDrag(actions)
