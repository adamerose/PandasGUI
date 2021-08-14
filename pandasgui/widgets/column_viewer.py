import sys

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent

from pandasgui.store import PandasGuiDataFrameStore
from pandasgui.utility import nunique
from pandasgui.widgets import base_widgets


class FlatDraggableTree(base_widgets.QTreeWidget):
    mouseReleaseEventSignal = pyqtSignal(QMouseEvent)

    def __init__(self):
        super().__init__()

        self.header().setStretchLastSection(False)
        self.setDragDropMode(self.InternalMove)
        self.setSelectionMode(self.ExtendedSelection)
        self.setSelectionBehavior(self.SelectRows)
        self.setRootIsDecorated(False)

        self.expandAll()
        self.apply_tree_settings()

    def showEvent(self, event: QtGui.QShowEvent):
        for i in range(self.columnCount()):
            self.resizeColumnToContents(i)
        event.accept()

    def rowsInserted(self, parent: QtCore.QModelIndex, start: int, end: int):
        super().rowsInserted(parent, start, end)
        self.expandAll()

    def sizeHint(self) -> QtCore.QSize:
        self.header().setStretchLastSection(False)
        width = 5 + sum([self.columnWidth(i) for i in range(self.columnCount())])
        self.header().setStretchLastSection(True)

        return QtCore.QSize(width, super().sizeHint().height())

    def dragEnterEvent(self, e: QtGui.QDragEnterEvent) -> None:
        self.apply_tree_settings()
        super().dragEnterEvent(e)

    def apply_tree_settings(self):
        root = self.invisibleRootItem()
        root.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDropEnabled)

        for i in range(root.childCount()):
            child = root.child(i)
            child.setExpanded(True)

            child.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled & ~Qt.ItemIsDropEnabled)

    def mimeData(self, indexes):
        mimedata = super().mimeData(indexes)
        if indexes:
            mimedata.setText(indexes[0].text(0))
        return mimedata

    def mouseReleaseEvent(self, event):
        self.mouseReleaseEventSignal.emit(event)
        super().mouseReleaseEvent(event)


class ColumnViewer(QtWidgets.QWidget):
    def __init__(self, pgdf: PandasGuiDataFrameStore):
        super().__init__()

        self.tree: FlatDraggableTree = FlatDraggableTree()
        self.tree.setHeaderLabels(['Name'])
        self.tree.setDragEnabled(True)
        self.tree.setDefaultDropAction(Qt.CopyAction)

        # Search box
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.textChanged.connect(self.filter)

        self.source_tree_layout = QtWidgets.QVBoxLayout()
        self.source_tree_layout.addWidget(self.search_bar)
        self.source_tree_layout.addWidget(self.tree)
        self.setLayout(self.source_tree_layout)

        self.update_df(pgdf)

    def update_df(self, df):
        pgdf = PandasGuiDataFrameStore.cast(df)

        self.pgdf = pgdf
        self.refresh()

    def refresh(self):
        sources = self.pgdf.df_unfiltered.columns
        source_nunique = nunique(self.pgdf.df_unfiltered)
        source_types = self.pgdf.df_unfiltered.dtypes.values.astype(str)

        # Ensure no duplicates
        assert (len(sources) == len(set(sources)))
        assert (len(sources) == len(source_nunique))
        assert (len(sources) == len(source_types))

        self.tree.clear()
        for i in range(len(sources)):
            item = base_widgets.QTreeWidgetItem(self.tree,
                                                [str(sources[i]), str(source_nunique[i]), str(source_types[i])])

        # Depends on Search Box and Source list
        self.filter()
        self.tree.apply_tree_settings()

    def filter(self):
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            child = root.child(i)
            child.setHidden(True)

        items = self.tree.findItems(f".*{self.search_bar.text()}.*",
                                    Qt.MatchRegExp | Qt.MatchRecursive)
        for item in items:
            item.setHidden(False)


class SortableColumnViewer(ColumnViewer):

    def __init__(self, pgdf: PandasGuiDataFrameStore):
        super().__init__(pgdf)
        self.tree.setSortingEnabled(True)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    from pandasgui.datasets import pokemon

    x = ColumnViewer(pokemon)
    x.show()

    sys.exit(app.exec_())
