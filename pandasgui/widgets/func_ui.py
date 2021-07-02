from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets, sip
from PyQt5.QtCore import Qt
from typing import List, Callable
import os
import inspect
import pprint
import pandas as pd

from pandasgui.jotly import ColumnName, ColumnNameList, OtherDataFrame
from pandasgui.utility import nunique, get_function_body, refactor_variable, kwargs_string, flatten_df
from pandasgui.store import SETTINGS_STORE, PandasGuiDataFrameStore
import pandasgui
import ast
from typing import List, Union
from typing_extensions import Literal, get_args, get_origin
from dataclasses import asdict, dataclass

from pandasgui.widgets import base_widgets
from pandasgui import jotly


class HiddenArg:
    pass


@dataclass
class ColumnNameArg:
    arg_name: str
    default_value: str

    def __init__(self, arg_name, default_value=None):
        self.arg_name = arg_name
        self.default_value = default_value


@dataclass
class ColumnNameListArg:
    arg_name: str
    default_value: List[str]

    def __init__(self, arg_name, default_value=None):
        if default_value is None:
            default_value = []

        self.arg_name = arg_name
        self.default_value = default_value


@dataclass
class LiteralArg:
    arg_name: str
    values: List[str]
    default_value: List[str]

    def __init__(self, arg_name, values, default_value=None):
        if default_value is None:
            default_value = values[0]

        self.arg_name = arg_name
        self.values = values
        self.default_value = default_value


@dataclass
class BooleanArg:
    arg_name: str
    default_value: bool

    def __init__(self, arg_name, default_value=None):
        if default_value is None:
            default_value = True

        self.arg_name = arg_name
        self.default_value = default_value


# Display a dropdown to pick a DataFrame name from the list of DataFrames in the GUI
@dataclass
class OtherDataFrameArg:
    arg_name: str
    default_value: str

    def __init__(self, arg_name, default_value=None):
        self.arg_name = arg_name
        self.default_value = default_value


# This schema is made up of multiple args, this defines all the drop zones available in the Dragger
@dataclass
class Schema:

    def __init__(self,
                 name="Untitled",
                 label="Untitled",
                 function=None,
                 icon_path=None,
                 args=None,
                 ):

        if args is None:
            args = []

            if function is not None:
                sig = inspect.signature(function)
                for _, param in sig.parameters.items():
                    arg_name = param.name
                    arg_default = param.default if param.default != inspect._empty else None
                    arg_type = param.annotation

                    if get_origin(arg_type) == Literal:
                        values = get_args(arg_type)
                        args.append(LiteralArg(arg_name, values, default_value=arg_default))

                    elif arg_type == ColumnName:
                        args.append(ColumnNameArg(arg_name, default_value=arg_default or ''))

                    elif arg_type == ColumnNameList:
                        args.append(ColumnNameListArg(arg_name, default_value=arg_default or []))

                    elif arg_type == bool:
                        args.append(BooleanArg(arg_name, default_value=arg_default))

                    elif arg_type == OtherDataFrame:
                        args.append(OtherDataFrameArg(arg_name, default_value=arg_default))

        self.name = name
        self.args = args
        self.label = label
        self.function = function
        self.icon_path = icon_path

    name: str
    args: List[Union[ColumnNameArg, ColumnNameListArg, LiteralArg, BooleanArg]]
    label: str
    function: Callable
    icon_path: str


def format_kwargs(kwargs):
    for k, v in kwargs.items():
        if isinstance(v, pd.DataFrame):
            kwargs[k] = '*DataFrame Object*'
    return pprint.pformat(kwargs, width=40)


class FuncUi(QtWidgets.QWidget):
    valuesChanged = QtCore.pyqtSignal()
    itemDropped = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()
    saving = QtCore.pyqtSignal()

    def __init__(self, pgdf, schema: Schema = None):
        super().__init__()
        self.remembered_values = {}

        self.schema = schema
        self.pgdf: PandasGuiDataFrameStore = pgdf
        self.df = flatten_df(pgdf.df)

        # Custom kwargs dialog
        self.kwargs_dialog = CustomKwargsEditor(self)

        # Preview dialog
        self.preview_dialog = QtWidgets.QDialog(self)
        self.preview_dialog_text = QtWidgets.QTextEdit()
        self.preview_dialog.setLayout(QtWidgets.QVBoxLayout())
        self.preview_dialog.layout().addWidget(self.preview_dialog_text)
        self.valuesChanged.connect(lambda: self.preview_dialog_text.setText(
            format_kwargs(self.get_data())))

        # Code export dialog
        self.code_export_dialog = QtWidgets.QDialog(self)
        self.code_export_dialog_text = QtWidgets.QTextEdit()
        self.code_export_dialog.setLayout(QtWidgets.QVBoxLayout())
        self.code_export_dialog.layout().addWidget(self.code_export_dialog_text)

        self.valuesChanged.connect(lambda: self.code_export_dialog_text.setText(
            format_kwargs(self.get_data())))

        # Sources list
        self.source_tree = SourceTree(self.df)
        self.source_tree2 = SourceTree(self.df)

        # Destinations tree
        self.dest_tree = DestinationTree(self)
        self.dest_tree.setHeaderLabels(['Name', 'Value'])

        # Set schema
        self.set_schema(self.schema)

        # Buttons
        self.kwargs_button = QtWidgets.QPushButton("Custom Kwargs")
        self.save_html_button = QtWidgets.QPushButton("Save HTML")
        self.code_export_button = QtWidgets.QPushButton("Code Export")
        self.reset_button = QtWidgets.QPushButton("Reset")
        self.preview_button = QtWidgets.QPushButton("Preview Kwargs")
        self.finish_button = QtWidgets.QPushButton("Finish")

        # Signals
        self.valuesChanged.connect(self.remember_values)
        self.dest_tree.itemDoubleClicked.connect(self.handle_double_click)

        self.kwargs_button.clicked.connect(self.custom_kwargs)
        self.reset_button.clicked.connect(self.reset)
        self.save_html_button.clicked.connect(self.save_html)
        self.code_export_button.clicked.connect(self.code_export)
        self.preview_button.clicked.connect(self.preview)
        self.finish_button.clicked.connect(self.finish)

        # Layout

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addWidget(self.kwargs_button)
        self.button_layout.addWidget(self.save_html_button)
        self.button_layout.addWidget(self.reset_button)
        self.button_layout.addWidget(self.code_export_button)
        self.button_layout.addWidget(self.preview_button)
        self.button_layout.addWidget(self.finish_button)

        self.source_tree_layout = QtWidgets.QVBoxLayout()
        self.source_tree_layout.addWidget(self.source_tree)
        self.source_tree_layout.addWidget(self.source_tree2)
        self.source_tree_layout_wrapper = QtWidgets.QWidget()
        self.source_tree_layout_wrapper.setLayout(self.source_tree_layout)

        self.splitter = QtWidgets.QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(3)

        self.splitter.addWidget(self.source_tree_layout_wrapper)
        self.splitter.addWidget(self.dest_tree)

        self.main_layout = QtWidgets.QGridLayout()
        self.main_layout.addWidget(self.splitter, 0, 0, 2, 1)
        self.main_layout.addLayout(self.button_layout, 2, 0, 1, 2)

        self.setLayout(self.main_layout)

    def handle_double_click(self, item, column):
        # Delete chldren if is section
        if item.parent() is None:
            for i in reversed(range(item.childCount())):
                sip.delete(item.child(i))
        # Delete if not section
        else:
            sip.delete(item)

    def custom_kwargs(self):
        self.kwargs_dialog.setVisible(not self.kwargs_dialog.isVisible())

    def preview(self):
        self.preview_dialog.setVisible(not self.preview_dialog.isVisible())

    def code_export(self):
        func = self.schema.function
        func_body = get_function_body(func)
        kwargs = self.get_data()
        text = func_body

        # Replace variable names with values
        for key, val in kwargs.items():
            if isinstance(val, pd.DataFrame):
                df_dict = self.pgdf.store.get_dataframes()
                df_name = next((k for k in df_dict if df_dict[k] is val), None)

                text = refactor_variable(text, key, df_name)
            else:
                text = refactor_variable(text, key, repr(val))

        # Plug in settings values
        for setting_name, setting in SETTINGS_STORE.__dict__.items():
            text = text.replace(f"SETTINGS_STORE.{setting_name}.value", repr(setting.value))

        # Do other replacements
        text = refactor_variable(text, "data_frame", "df")
        text = text.replace("return fig", "show(fig)")

        # Get kwargs not absorbed by jotly function
        extra_kwargs = {k: v for k, v in kwargs.items() if k not in inspect.getfullargspec(func).args}
        text = text.replace("**kwargs", kwargs_string(extra_kwargs))

        # Add imports
        text = ("import plotly.express as px\n" +
                "from pandasgui import show\n\n" + text)

        self.code_export_dialog_text.setText(text)
        self.code_export_dialog.setVisible(not self.code_export_dialog.isVisible())

    def reset(self):
        self.remembered_values = {}
        self.set_schema(self.schema)

    def finish(self):
        self.finished.emit()

    def save_html(self):
        self.saving.emit()

    def remember_values(self):
        self.remembered_values.update(self.get_data())

    def get_data(self):
        data = {}

        # Get args from destination UI
        root = self.dest_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            section = item.text(0)
            data[section] = item.data(1, Qt.UserRole)

        # Add custom kwargs
        root = self.kwargs_dialog.tree_widget.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            key = item.text(0)
            value = item.text(1)
            try:
                value = ast.literal_eval(value)
            except (SyntaxError, ValueError):
                pass

            data[key] = value

        return data

    def set_data(self, dct: dict):
        for dct_key in list(dct.keys()):
            # Set tree values
            root = self.dest_tree.invisibleRootItem()
            for i in range(root.childCount()):
                item = root.child(i)
                arg = next(arg for arg in self.schema.args if arg.arg_name == item.text(0))
                if arg.arg_name == dct_key:
                    val = dct.pop(dct_key)
                    item.setData(1, Qt.UserRole, val)
                    self.remembered_values[dct_key] = val

            # Set kwargs_dialog values
            root = self.kwargs_dialog.tree_widget.invisibleRootItem()
            for i in range(root.childCount()):
                item = root.child(i)
                key = item.text(0)
                if key == dct_key:
                    val = dct.pop(dct_key)
                    item.setText(1, val)
                    self.remembered_values[dct_key] = val

        if dct.keys():
            raise ValueError(f"{dct.keys()} not in schema")

        self.set_schema(self.schema)

    def set_schema(self, schema: Schema):
        self.schema = schema

        # Delete all sections
        root = self.dest_tree.invisibleRootItem()
        for i in reversed(range(root.childCount())):
            sip.delete(root.child(i))

        for arg in schema.args:

            item = base_widgets.QTreeWidgetItem(self.dest_tree, [arg.arg_name])
            item.setFlags(item.flags() & Qt.ItemIsEnabled & ~Qt.ItemIsDropEnabled & ~Qt.ItemIsDragEnabled)

            if type(arg) == ColumnNameArg:

                cdz = ColumnDropZone()
                item.treeWidget().setItemWidget(item, 1, cdz)
                cdz.valueChanged.connect(
                    lambda text, item=item: item.setData(1, Qt.UserRole, text if text != "" else None))

                if arg.arg_name in self.remembered_values.keys():
                    val = self.remembered_values[arg.arg_name]
                elif arg.arg_name in asdict(SETTINGS_STORE).keys():
                    val = SETTINGS_STORE[arg.arg_name].value
                else:
                    val = arg.default_value

                # Logic to show value in widget and support converting from ColumnListArg to ColumnArg
                if val is None:
                    val_repr = ''
                elif type(val) == str:
                    val_repr = val
                elif type(val) == list:
                    if len(val) == 0:
                        val_repr = ''
                    else:
                        val_repr = val[0]
                else:
                    raise ValueError

                cdz.setText(val_repr)
                cdz.valueChanged.emit(val_repr)  # Need this incase value was same
                cdz.valueChanged.connect(lambda: self.valuesChanged.emit())

            elif type(arg) == ColumnNameListArg:

                cldz = ColumnListDropZone()
                item.treeWidget().setItemWidget(item, 1, cldz)
                cldz.valueChanged.connect(
                    lambda name_list, item=item: item.setData(1, Qt.UserRole, name_list))

                if arg.arg_name in self.remembered_values.keys():
                    val = self.remembered_values[arg.arg_name]
                elif arg.arg_name in asdict(SETTINGS_STORE).keys():
                    val = SETTINGS_STORE[arg.arg_name].value
                else:
                    val = arg.default_value

                # Logic to show value in widget and support converting from ColumnArg to ColumnListArg
                if val is None:
                    val_repr = []
                elif type(val) == str:
                    val_repr = [val]
                elif type(val) == list:
                    val_repr = val
                else:
                    raise ValueError

                cldz.set_names(val_repr)
                cldz.valueChanged.emit(val_repr)  # Need this incase value was same
                cldz.valueChanged.connect(lambda: self.valuesChanged.emit())

            elif type(arg) == BooleanArg:
                checkbox = QtWidgets.QCheckBox()

                checkbox.stateChanged.connect(
                    lambda state, item=item: item.setData(1, Qt.UserRole, state == Qt.Checked))

                item.treeWidget().setItemWidget(item, 1, checkbox)
                if arg.arg_name in self.remembered_values.keys():
                    val = self.remembered_values[arg.arg_name]
                elif arg.arg_name in asdict(SETTINGS_STORE).keys():
                    val = SETTINGS_STORE[arg.arg_name].value
                else:
                    val = arg.default_value
                checkbox.setChecked(val)
                checkbox.stateChanged.emit(Qt.Checked if val else Qt.Unchecked)
                checkbox.stateChanged.connect(lambda: self.valuesChanged.emit())

            elif type(arg) == LiteralArg:
                combo_box = QtWidgets.QComboBox()
                combo_box.addItems([str(x) for x in arg.values])
                item.treeWidget().setItemWidget(item, 1, combo_box)

                combo_box.currentIndexChanged.connect(
                    lambda ix, values=arg.values, item=item: item.setData(1, Qt.UserRole, values[ix]))
                combo_box.currentIndexChanged.connect(lambda: self.valuesChanged.emit())

                if arg.arg_name in self.remembered_values.keys() and arg.arg_name in arg.values:
                    val = self.remembered_values[arg.arg_name]
                elif arg.arg_name in asdict(SETTINGS_STORE).keys():
                    val = SETTINGS_STORE[arg.arg_name].value
                    if val == '':
                        val = None
                else:
                    val = arg.default_value
                ix = arg.values.index(val)
                combo_box.setCurrentIndex(ix)
                combo_box.currentIndexChanged.emit(ix)  # Need this incase value was same

            elif type(arg) == OtherDataFrameArg:

                names = list(self.pgdf.store.get_dataframes().keys())
                other_names = [n for n in names if n != self.pgdf.name]
                dataframes = list(self.pgdf.store.get_dataframes().values())
                other_dataframes = [d for d in dataframes if d is not self.pgdf.df]
                combo_box = QtWidgets.QComboBox()
                combo_box.addItems([str(x) for x in other_names])
                item.treeWidget().setItemWidget(item, 1, combo_box)

                combo_box.currentIndexChanged.connect(
                    lambda ix, values=other_dataframes, item=item: [
                        item.setData(1, Qt.UserRole, values[ix]),
                        self.source_tree2.set_df(values[ix])
                    ])
                combo_box.currentIndexChanged.connect(lambda: self.valuesChanged.emit())

                if arg.arg_name in self.remembered_values.keys() and arg.arg_name in names:
                    val = self.remembered_values[arg.arg_name]
                elif arg.arg_name in asdict(SETTINGS_STORE).keys():
                    val = SETTINGS_STORE[arg.arg_name].value
                else:
                    if arg.default_value is None:
                        val = other_names[0]
                    else:
                        val = arg.default_value
                ix = other_names.index(val)
                combo_box.setCurrentIndex(ix)
                combo_box.currentIndexChanged.emit(ix)  # Need this incase value was same

        self.valuesChanged.emit()

        if any([type(arg) == OtherDataFrameArg for arg in schema.args]):
            self.source_tree2.show()
        else:
            self.source_tree2.hide()

        self.dest_tree.autosize_columns()


class ColumnDropZone(QtWidgets.QLineEdit):
    valueChanged = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setReadOnly(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QtWidgets.QApplication.startDragDistance():
            return
        drag = QtGui.QDrag(self)
        mimedata = QtCore.QMimeData()
        mimedata.setText(self.text())
        drag.setMimeData(mimedata)
        pixmap = QtGui.QPixmap(self.size())
        painter = QtGui.QPainter(pixmap)
        painter.drawPixmap(self.rect(), self.grab())
        painter.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        drag.exec_(Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        pos = event.pos()
        dropped_text = event.mimeData().text()

        # Swap text between source and this
        current_text = self.text()
        source = event.source()
        if type(source) == ColumnDropZone:
            source.setText(current_text)
            source.valueChanged.emit(current_text)

        self.setText(dropped_text)
        self.valueChanged.emit(dropped_text)

        event.acceptProposedAction()

    def mouseDoubleClickEvent(self, e: QtGui.QMouseEvent) -> None:
        self.setText("")
        self.valueChanged.emit("")
        super().mouseDoubleClickEvent(e)


class ColumnListDropZone(QtWidgets.QListWidget):
    valueChanged = QtCore.pyqtSignal(list)  # List of strings

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

        self.setDragDropMode(self.DragDrop)
        self.setSelectionMode(self.ExtendedSelection)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)

    def sizeHint(self):
        width = super().sizeHint().width()
        height = sum([self.sizeHintForRow(i) for i in range(self.count())]) + 5
        if self.count() == 0:
            height += 30
        elif self.count() == 1:
            height += (30 - self.sizeHintForRow(0))
        return QtCore.QSize(width, height)

    def remove_duplicates(self):
        self.set_names(list(OrderedDict.fromkeys(self.get_items())))

    def set_names(self, names: List[str]):
        self.clear()
        self.addItems(names)
        self.valueChanged.emit(self.get_items())

    def get_items(self):
        return [self.item(ix).text() for ix in range(self.count())]

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    # https://stackoverflow.com/a/12178903/3620725
    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        src_widget = event.source()
        if isinstance(src_widget, QtWidgets.QTreeWidget):
            items = [item.text(0) for item in src_widget.selectedItems()]
            self.addItems(items)
            self.remove_duplicates()
            self.valueChanged.emit(self.get_items())
            event.acceptProposedAction()
        elif isinstance(src_widget, ColumnDropZone):
            source = event.source()
            source.setText('')
            source.valueChanged.emit('')

            dropped_text = event.mimeData().text()
            self.addItems([dropped_text])
            self.remove_duplicates()
            self.valueChanged.emit(self.get_items())
        else:
            super().dropEvent(event)

    def mouseDoubleClickEvent(self, e: QtGui.QMouseEvent) -> None:
        ix = self.indexAt(e.pos())
        sip.delete(self.itemAt(e.pos()))
        self.valueChanged.emit([self.item(ix).text() for ix in range(self.count())])
        super().mouseDoubleClickEvent(e)

    def mimeData(self, indexes):
        mimedata = super().mimeData(indexes)
        if indexes:
            mimedata.setText(indexes[0].text())
        return mimedata


def decode_data(bytearray):
    data = []
    item = {}

    ds = QtCore.QDataStream(bytearray)
    while not ds.atEnd():

        row = ds.readInt32()
        column = ds.readInt32()

        map_items = ds.readInt32()
        for i in range(map_items):
            key = ds.readInt32()

            value = QtCore.QVariant()
            ds >> value
            item[Qt.ItemDataRole(key)] = value

        data.append(item)
    return data


class DestinationTree(base_widgets.QTreeWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setItemsExpandable(False)
        self.setRootIsDecorated(False)
        self.setAcceptDrops(False)
        self.setColumnWidth(0, 90)
        root = self.invisibleRootItem()
        root.setFlags(root.flags() & Qt.ItemIsEnabled & ~Qt.ItemIsDropEnabled & ~Qt.ItemIsDragEnabled)

        self.setDragDropMode(self.DragDrop)
        self.setSelectionMode(self.ExtendedSelection)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)

    # https://stackoverflow.com/a/67213574/3620725
    def setItemWidget(self, item, column, widget):
        super().setItemWidget(item, column, widget)
        if isinstance(widget, QtWidgets.QListWidget):
            widget.model().rowsInserted.connect(
                lambda: self.updateItemWidget(item, column))
            widget.model().rowsRemoved.connect(
                lambda: self.updateItemWidget(item, column))

    # https://stackoverflow.com/a/67213574/3620725
    def updateItemWidget(self, item, column):
        widget = self.itemWidget(item, column)
        item.setSizeHint(column, widget.sizeHint())
        self.updateGeometries()


class DraggableTree(base_widgets.QTreeWidget):

    def dropEvent(self, e: QtGui.QDropEvent):
        super().dropEvent(e)
        self.parent().itemDropped.emit()

    def mimeData(self, indexes):
        mimedata = super().mimeData(indexes)
        if indexes:
            mimedata.setText(indexes[0].text(0))
        return mimedata


class SourceTree(QtWidgets.QWidget):
    def __init__(self, df):
        super().__init__()

        self.tree = DraggableTree()

        # Search box
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.textChanged.connect(self.filter)

        self.tree.setHeaderLabels(['Name', '#Unique', 'Type'])

        self.tree.setSortingEnabled(True)

        self.source_tree_layout = QtWidgets.QVBoxLayout()
        self.source_tree_layout.addWidget(self.search_bar)
        self.source_tree_layout.addWidget(self.tree)
        self.setLayout(self.source_tree_layout)

        # Configure drag n drop
        self.tree.setDragDropMode(self.tree.DragOnly)
        self.tree.setSelectionMode(self.tree.ExtendedSelection)
        self.tree.setDefaultDropAction(QtCore.Qt.CopyAction)

        self.set_df(df)

    def set_df(self, df):
        sources = df.columns
        source_nunique = nunique(df)
        source_types = df.dtypes.values.astype(str)

        # Ensure no duplicates
        assert (len(sources) == len(set(sources)))
        assert (len(sources) == len(source_nunique))
        assert (len(sources) == len(source_types))

        self.set_sources(sources, source_nunique, source_types)

        # Depends on Search Box and Source list
        self.filter()

    def set_sources(self, sources: List[str], source_nunique: List[str], source_types: List[str]):
        self.tree.clear()
        for i in range(len(sources)):
            item = base_widgets.QTreeWidgetItem(self.tree,
                                                [str(sources[i]), str(source_nunique[i]), str(source_types[i])])

        self.filter()

    def filter(self):
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            child = root.child(i)
            child.setHidden(True)

        items = self.tree.findItems(f".*{self.search_bar.text()}.*",
                                    Qt.MatchRegExp | Qt.MatchRecursive)
        for item in items:
            item.setHidden(False)


class CustomKwargsEditor(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.setWindowTitle("Custom Kwargs")

        self.tree_widget = QtWidgets.QTreeWidget()
        self.tree_widget.setHeaderLabels(['Kwarg Name', 'Kwarg Value'])
        self.kwarg_name = QtWidgets.QLineEdit()
        self.kwarg_value = QtWidgets.QLineEdit()
        self.submit_button = QtWidgets.QPushButton("Add")
        self.delete_button = QtWidgets.QPushButton("Delete")

        # Signals
        self.kwarg_name.returnPressed.connect(self.add_item)
        self.kwarg_value.returnPressed.connect(self.add_item)
        self.submit_button.pressed.connect(self.add_item)
        self.delete_button.pressed.connect(self.delete)

        # Layout
        self.layout = QtWidgets.QVBoxLayout()
        self.input_layout = QtWidgets.QHBoxLayout()
        self.input_layout.addWidget(self.kwarg_name)
        self.input_layout.addWidget(self.kwarg_value)
        self.input_layout.addWidget(self.submit_button)
        self.layout.addLayout(self.input_layout)
        self.layout.addWidget(self.tree_widget)
        self.layout.addWidget(self.delete_button)
        self.setLayout(self.layout)

    def add_item(self):
        name = self.kwarg_name.text()
        value = self.kwarg_value.text()

        if name != "" and value != "":
            self.kwarg_name.setText("")
            self.kwarg_value.setText("")

            item = base_widgets.QTreeWidgetItem(self.tree_widget, [name, value])

            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)

    def delete(self):
        for item in self.tree_widget.selectedItems():
            sip.delete(item)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from pandasgui.datasets import pokemon

    app = QApplication(sys.argv)

    test = FuncUi(df=pokemon,
                  schema=Schema(name='histogram',
                                label='Histogram',
                                function=jotly.scatter,
                                icon_path=os.path.join(pandasgui.__path__[0],
                                                       'resources/images/draggers/trace-type-histogram.svg')),
                  )
    test.finished.connect(lambda: print(test.get_data()))
    test.show()
    sys.exit(app.exec_())
