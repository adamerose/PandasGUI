# -*- coding: utf-8 -*-
"""
Created on Tue Dec  1 15:12:20 2015
@author: МакаровАС
https://github.com/Winand/dataframemodel

Modified on 2018-12-05
Adam Rose
"""
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, QSize, QRect, Qt, QPoint
from PyQt5.QtGui import QPainter, QFont, QFontMetrics, QPalette, QBrush, QColor, QTransform
from PyQt5.QtWidgets import QStyleOptionHeader, QHeaderView, QWidget, QStyle
import pandas as pd
import numpy as np
import datetime
import pyqt_fix

# Define role numbers for our custom headers
HorizontalHeaderDataRole = Qt.UserRole
VerticalHeaderDataRole = Qt.UserRole + 1


class QList(list):
    push_back = lambda self, v: self.append(v)

    def indexOf(self, v):
        return self.index(v) if v in self else -1

    push_front = lambda self, v: self.insert(0, v)
    size = lambda self: len(self)
    empty = lambda self: not len(self)


QModelIndexList = QList


class HierarchicalHeaderView(QHeaderView):
    """
    This class is a Python port of
    http://qt-apps.org/content/show.php/HierarchicalHeaderView?content=103154
    """
    options = {"highlightSections": True, "clickable": True}

    class private_data:
        headerModel = None

        def initFromNewModel(self, orientation: int, model: QAbstractItemModel):
            self.headerModel = model.data(QModelIndex(),
                                          HorizontalHeaderDataRole if orientation == Qt.Horizontal else VerticalHeaderDataRole)

        def findRootIndex(self, index: QModelIndex) -> QModelIndex:
            while index.parent().isValid():
                index = index.parent()
            return index

        def parentIndexes(self, index: QModelIndex) -> QModelIndexList:
            indexes = QModelIndexList()
            while index.isValid():
                indexes.push_front(index)
                index = index.parent()
            return indexes

        def findLeaf(self, currentIndex: QModelIndex, sectionIndex: int, currentLeafIndex: int) -> QModelIndex:
            if currentIndex.isValid():
                childCount = currentIndex.model().columnCount(currentIndex)
                if childCount:
                    for i in range(childCount):
                        res, currentLeafIndex = self.findLeaf(currentIndex.child(0, i), sectionIndex, currentLeafIndex)
                        if res.isValid():
                            return res, currentLeafIndex
                else:
                    currentLeafIndex += 1
                    if currentLeafIndex == sectionIndex:
                        return currentIndex, currentLeafIndex
            return QModelIndex(), currentLeafIndex

        def leafIndex(self, sectionIndex: int) -> QModelIndex:
            if self.headerModel:
                currentLeafIndex = -1
                for i in range(self.headerModel.columnCount()):
                    res, currentLeafIndex = self.findLeaf(self.headerModel.index(0, i), sectionIndex, currentLeafIndex)
                    if res.isValid():
                        return res
            return QModelIndex()

        def searchLeafs(self, currentIndex: QModelIndex) -> QModelIndexList:
            res = QModelIndexList()
            if currentIndex.isValid():
                childCount = currentIndex.model().columnCount(currentIndex)
                if childCount:
                    for i in range(childCount):
                        res += self.searchLeafs(currentIndex.child(0, i))
                else:
                    res.push_back(currentIndex)
            return res

        def leafs(self, searchedIndex: QModelIndex) -> QModelIndexList:
            leafs = QModelIndexList()
            if searchedIndex.isValid():
                childCount = searchedIndex.model().columnCount(searchedIndex)
                for i in range(childCount):
                    leafs += self.searchLeafs(searchedIndex.child(0, i))
            return leafs

        def setForegroundBrush(self, opt: QStyleOptionHeader, index: QModelIndex):
            foregroundBrush = index.data(Qt.ForegroundRole)
            if foregroundBrush:
                opt.palette.setBrush(QPalette.ButtonText, QBrush(foregroundBrush))

        def setBackgroundBrush(self, opt: QStyleOptionHeader, index: QModelIndex):
            backgroundBrush = index.data(Qt.BackgroundRole)
            if backgroundBrush:
                opt.palette.setBrush(QPalette.Button, QBrush(backgroundBrush))
                opt.palette.setBrush(QPalette.Window, QBrush(backgroundBrush))

        def cellSize(self, leafIndex: QModelIndex, hv: QHeaderView, styleOptions: QStyleOptionHeader) -> QSize:
            res = QSize()
            variant = leafIndex.data(Qt.SizeHintRole)
            if variant:
                res = variant
            fnt = QFont(hv.font())
            var = leafIndex.data(Qt.FontRole)
            if var:
                fnt = var
            fnt.setBold(True)
            fm = QFontMetrics(fnt)
            size = QSize(fm.size(0, leafIndex.data(Qt.DisplayRole)) + QSize(4, 0))  # WA: add more horizontal size (4px)
            if leafIndex.data(Qt.UserRole):
                size.transpose()
            decorationsSize = QSize(hv.style().sizeFromContents(QStyle.CT_HeaderSection, styleOptions, QSize(), hv))
            emptyTextSize = QSize(fm.size(0, ""))
            return res.expandedTo(size + decorationsSize - emptyTextSize)

        def currentCellWidth(self, searchedIndex: QModelIndex, leafIndex: QModelIndex, sectionIndex: int,
                             hv: QHeaderView) -> int:
            leafsList = QModelIndexList(self.leafs(searchedIndex))
            if leafsList.empty():
                return hv.sectionSize(sectionIndex)
            width = 0
            firstLeafSectionIndex = sectionIndex - leafsList.indexOf(leafIndex)
            for i in range(leafsList.size()):
                width += hv.sectionSize(firstLeafSectionIndex + i)
            return width

        def currentCellLeft(self, searchedIndex: QModelIndex, leafIndex: QModelIndex, sectionIndex: int, left: int,
                            hv: QHeaderView) -> int:
            leafsList = QModelIndexList(self.leafs(searchedIndex))
            if not leafsList.empty():
                n = leafsList.indexOf(leafIndex)
                firstLeafSectionIndex = sectionIndex - n
                n -= 1
                for n in range(n, 0 - 1, -1):
                    left -= hv.sectionSize(firstLeafSectionIndex + n)
            return left

        def paintHorizontalCell(self, painter: QPainter, hv: QHeaderView, cellIndex: QModelIndex,
                                leafIndex: QModelIndex, logicalLeafIndex: int, styleOptions: QStyleOptionHeader,
                                sectionRect: QRect, top: int):
            uniopt = QStyleOptionHeader(styleOptions)
            self.setForegroundBrush(uniopt, cellIndex)
            self.setBackgroundBrush(uniopt, cellIndex)
            height = self.cellSize(cellIndex, hv, uniopt).height()
            if cellIndex == leafIndex:
                height = sectionRect.height() - top
            left = self.currentCellLeft(cellIndex, leafIndex, logicalLeafIndex, sectionRect.left(), hv)
            width = self.currentCellWidth(cellIndex, leafIndex, logicalLeafIndex, hv)
            r = QRect(left, top, width, height)
            uniopt.text = cellIndex.data(Qt.DisplayRole)
            painter.save()
            uniopt.rect = r
            if cellIndex.data(Qt.UserRole):
                hv.style().drawControl(QStyle.CE_HeaderSection, uniopt, painter, hv)
                m = QTransform()
                m.rotate(-90)
                painter.setWorldMatrix(m, True)
                new_r = QRect(0, 0, r.height(), r.width())
                new_r.moveCenter(QPoint(-r.center().y(), r.center().x()))
                uniopt.rect = new_r
                hv.style().drawControl(QStyle.CE_HeaderLabel, uniopt, painter, hv)
            else:
                hv.style().drawControl(QStyle.CE_Header, uniopt, painter, hv)
            painter.restore()
            return top + height

        def paintHorizontalSection(self, painter: QPainter, sectionRect: QRect,
                                   logicalLeafIndex: int, hv: QHeaderView,
                                   styleOptions: QStyleOptionHeader, leafIndex: QModelIndex):
            #            print(logicalLeafIndex)
            oldBO = painter.brushOrigin()
            top = sectionRect.y()
            indexes = QModelIndexList(self.parentIndexes(leafIndex))
            for i in range(indexes.size()):
                realStyleOptions = QStyleOptionHeader(styleOptions)
                if i < indexes.size() - 1 and (
                        realStyleOptions.state & QStyle.State_Sunken or realStyleOptions.state & QStyle.State_On):
                    t = QStyle.State(QStyle.State_Sunken | QStyle.State_On)
                    realStyleOptions.state = realStyleOptions.state & ~t  # FIXME: parent items are not highlighted
                if i < indexes.size() - 1:  # Use sortIndicator for inner level only
                    realStyleOptions.sortIndicator = False
                #                if i==0:
                #                    print(self.leafs(indexes[i]), leafIndex)
                top = self.paintHorizontalCell(painter, hv, indexes[i], leafIndex, logicalLeafIndex, realStyleOptions,
                                               sectionRect, top)
            painter.setBrushOrigin(oldBO)

        def paintVerticalCell(self, painter: QPainter, hv: QHeaderView, cellIndex: QModelIndex, leafIndex: QModelIndex,
                              logicalLeafIndex: int, styleOptions: QStyleOptionHeader, sectionRect: QRect, left: int):
            uniopt = QStyleOptionHeader(styleOptions)
            self.setForegroundBrush(uniopt, cellIndex)
            self.setBackgroundBrush(uniopt, cellIndex)
            width = self.cellSize(cellIndex, hv, uniopt).width()
            if cellIndex == leafIndex:
                width = sectionRect.width() - left
            top = self.currentCellLeft(cellIndex, leafIndex, logicalLeafIndex, sectionRect.top(), hv)
            height = self.currentCellWidth(cellIndex, leafIndex, logicalLeafIndex, hv)
            r = QRect(left, top, width, height)
            uniopt.text = cellIndex.data(Qt.DisplayRole)
            painter.save()
            uniopt.rect = r
            if cellIndex.data(Qt.UserRole):
                hv.style().drawControl(QStyle.CE_HeaderSection, uniopt, painter, hv)
                m = QTransform()
                m.rotate(-90)
                painter.setWorldMatrix(m, True)
                new_r = QRect(0, 0, r.height(), r.width())
                new_r.moveCenter(QPoint(-r.center().y(), r.center().x()))
                uniopt.rect = new_r
                hv.style().drawControl(QStyle.CE_HeaderLabel, uniopt, painter, hv)
            else:
                hv.style().drawControl(QStyle.CE_Header, uniopt, painter, hv)
            painter.restore()
            return left + width

        def paintVerticalSection(self, painter: QPainter, sectionRect: QRect, logicalLeafIndex: int, hv: QHeaderView,
                                 styleOptions: QStyleOptionHeader, leafIndex: QModelIndex):
            oldBO = painter.brushOrigin()
            left = sectionRect.x()
            indexes = QModelIndexList(self.parentIndexes(leafIndex))
            for i in range(indexes.size()):
                realStyleOptions = QStyleOptionHeader(styleOptions)
                if i < indexes.size() - 1 and (
                        realStyleOptions.state & QStyle.State_Sunken or realStyleOptions.state & QStyle.State_On):
                    t = QStyle.State(QStyle.State_Sunken | QStyle.State_On)
                    realStyleOptions.state = realStyleOptions.state & ~t  # FIXME: parent items are not highlighted
                left = self.paintVerticalCell(painter, hv, indexes[i], leafIndex, logicalLeafIndex, realStyleOptions,
                                              sectionRect, left)
            painter.setBrushOrigin(oldBO)

    def __init__(self, orientation: Qt.Orientation, parent: QWidget):
        super().__init__(orientation, parent)
        self._pd = self.private_data()
        self.sectionResized.connect(self.on_sectionResized)
        self.setHighlightSections(self.options.get("highlightSections"))
        self.setSectionsClickable(self.options.get("clickable"))
        self.show()  # force to be visible
        getattr(parent, "set%sHeader" % ("Horizontal", "Vertical")[orientation != Qt.Horizontal])(self)
        self.sectionMoved.connect(self.on_sectionMoved)

    def on_sectionMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        view, model = self.parent(), self.parent().model()
        if not hasattr(model, "reorder"):
            return  # reorder underlying data of models with /reorder/ def only
        if getattr(self, "manual_move", False):
            self.manual_move = False
            return
        self.manual_move = True
        self.moveSection(newVisualIndex, oldVisualIndex)  # cancel move
        if model.reorder(oldVisualIndex, newVisualIndex, self.orientation()):
            # Reorder column widths / row heights
            horizontal = self.orientation() == Qt.Horizontal
            itemSize = (view.rowHeight, view.columnWidth)[horizontal]
            setItemSize = (view.setRowHeight, view.setColumnWidth)[horizontal]
            rng = sorted((oldVisualIndex, newVisualIndex))
            options = [(itemSize(i), i) for i in range(rng[0], rng[1] + 1)]
            options.insert(newVisualIndex - rng[0], options.pop(oldVisualIndex - rng[0]))
            for i, col in enumerate(range(rng[0], rng[1] + 1)):
                setItemSize(col, options[i][0])
            getattr(view, "select" + ("Row", "Column")[horizontal])(
                newVisualIndex)  # FIXME: don't select if sorting is enable?
            if self.isSortIndicatorShown():
                sortIndIndex = next((i for i, o in enumerate(options) if o[1] == self.sortIndicatorSection()), None)
                if sortIndIndex is not None:  # sort indicator is among sections being reordered
                    self.setSortIndicator(sortIndIndex + rng[0],
                                          self.sortIndicatorOrder())  # FIXME: does unnecessary sorting
            model.layoutChanged.emit()  # update view

    def styleOptionForCell(self, logicalInd: int) -> QStyleOptionHeader:
        opt = QStyleOptionHeader()
        self.initStyleOption(opt)
        if self.isSortIndicatorShown() and self.sortIndicatorSection() == logicalInd:
            opt.sortIndicator = (QStyleOptionHeader.SortUp, QStyleOptionHeader.SortDown)[
                self.sortIndicatorOrder() == Qt.AscendingOrder]
        if self.window().isActiveWindow():
            opt.state = opt.state | QStyle.State_Active
        opt.textAlignment = Qt.AlignCenter
        opt.iconAlignment = Qt.AlignVCenter
        opt.section = logicalInd
        visual = self.visualIndex(logicalInd)
        if self.count() == 1:
            opt.position = QStyleOptionHeader.OnlyOneSection
        else:
            if visual == 0:
                opt.position = QStyleOptionHeader.Beginning
            else:
                opt.position = QStyleOptionHeader.End if visual == self.count() - 1 else QStyleOptionHeader.Middle
        if self.sectionsClickable():
            #            if logicalIndex == d.hover:
            #            ...
            if self.highlightSections() and self.selectionModel():
                if self.orientation() == Qt.Horizontal:
                    if self.selectionModel().columnIntersectsSelection(logicalInd, self.rootIndex()):
                        opt.state = opt.state | QStyle.State_On
                    if self.selectionModel().isColumnSelected(logicalInd, self.rootIndex()):
                        opt.state = opt.state | QStyle.State_Sunken
                else:
                    if self.selectionModel().rowIntersectsSelection(logicalInd, self.rootIndex()):
                        opt.state = opt.state | QStyle.State_On
                    if self.selectionModel().isRowSelected(logicalInd, self.rootIndex()):
                        opt.state = opt.state | QStyle.State_Sunken
        if self.selectionModel():
            previousSelected = False
            if self.orientation() == Qt.Horizontal:
                previousSelected = self.selectionModel().isColumnSelected(self.logicalIndex(visual - 1),
                                                                          self.rootIndex())
            else:
                previousSelected = self.selectionModel().isRowSelected(self.logicalIndex(visual - 1), self.rootIndex())
            nextSelected = False
            if self.orientation() == Qt.Horizontal:
                nextSelected = self.selectionModel().isColumnSelected(self.logicalIndex(visual + 1), self.rootIndex())
            else:
                nextSelected = self.selectionModel().isRowSelected(self.logicalIndex(visual + 1), self.rootIndex())
            if previousSelected and nextSelected:
                opt.selectedPosition = QStyleOptionHeader.NextAndPreviousAreSelected
            else:
                if previousSelected:
                    opt.selectedPosition = QStyleOptionHeader.PreviousIsSelected
                else:
                    if nextSelected:
                        opt.selectedPosition = QStyleOptionHeader.NextIsSelected
                    else:
                        opt.selectedPosition = QStyleOptionHeader.NotAdjacent
        return opt

    def sectionSizeFromContents(self, logicalIndex: int) -> QSize:
        if self._pd.headerModel:
            curLeafIndex = QModelIndex(self._pd.leafIndex(logicalIndex))
            if curLeafIndex.isValid():
                styleOption = QStyleOptionHeader(self.styleOptionForCell(logicalIndex))
                s = QSize(self._pd.cellSize(curLeafIndex, self, styleOption))
                curLeafIndex = curLeafIndex.parent()
                while curLeafIndex.isValid():
                    if self.orientation() == Qt.Horizontal:
                        s.setHeight(s.height() + self._pd.cellSize(curLeafIndex, self, styleOption).height())
                    else:
                        s.setWidth(s.width() + self._pd.cellSize(curLeafIndex, self, styleOption).width())
                    curLeafIndex = curLeafIndex.parent()
                return s
        return super().sectionSizeFromContents(logicalIndex)

    def paintSection(self, painter: QPainter, rect: QRect, logicalIndex: int):
        if rect.isValid():
            leafIndex = QModelIndex(self._pd.leafIndex(logicalIndex))
            if leafIndex.isValid():
                if self.orientation() == Qt.Horizontal:
                    self._pd.paintHorizontalSection(painter, rect, logicalIndex, self,
                                                    self.styleOptionForCell(logicalIndex), leafIndex)
                else:
                    self._pd.paintVerticalSection(painter, rect, logicalIndex, self,
                                                  self.styleOptionForCell(logicalIndex), leafIndex)
                return
        super().paintSection(painter, rect, logicalIndex)

    def on_sectionResized(self, logicalIndex: int):
        if self.isSectionHidden(logicalIndex):
            return
        leafIndex = QModelIndex(self._pd.leafIndex(logicalIndex))
        if leafIndex.isValid():
            leafsList = QModelIndexList(self._pd.leafs(self._pd.findRootIndex(leafIndex)))
            for n in range(leafsList.indexOf(leafIndex), 0, -1):
                logicalIndex -= 1
                w = self.viewport().width()
                h = self.viewport().height()
                pos = self.sectionViewportPosition(logicalIndex)
                r = QRect(pos, 0, w - pos, h)
                if self.orientation() == Qt.Horizontal:
                    if self.isRightToLeft():
                        r.setRect(0, 0, pos + self.sectionSize(logicalIndex), h)
                else:
                    r.setRect(0, pos, w, h - pos)
                self.viewport().update(r.normalized())

    def setModel(self, model: QAbstractItemModel):
        super().setModel(model)
        model.layoutChanged.connect(self.layoutChanged)
        self.layoutChanged()

    def layoutChanged(self):
        if self.model():
            self._pd.initFromNewModel(self.orientation(), self.model())
            axis = ("column", "row")[self.orientation() != Qt.Horizontal]
            cnt = getattr(self.model(), axis + "Count")(QModelIndex())
            if cnt:
                self.initializeSections(0, cnt - 1)


class DataFrameModel(QtCore.QAbstractTableModel):
    # na_values:least|greatest - for sorting
    options = {"striped": True,
               "stripesColor": "#fafafa",
               "na_values": "least",
               "tooltip_min_len": 21}

    def __init__(self, dataframe=None):
        super().__init__()

        if dataframe is None:
            self.df = pd.DataFrame()
        else:
            self.df = dataframe.copy()

        self.layoutChanged.emit()

    def rowCount(self, parent):
        return len(self.df)

    def columnCount(self, parent):
        return len(self.df.columns)

    def data(self, index, role):
        """
        Returns the data stored under the given role for the item referred to by the index.
        http://pyqt.sourceforge.net/Docs/PyQt4/qabstractitemmodel.html#data

        Args:
            index ():
            role ():

        Returns:
        """

        row, col = index.row(), index.column()

        if role in (Qt.DisplayRole, Qt.ToolTipRole):
            value = self.df.iat[row, col]
            if not pd.isnull(value):  # If not null then convert to str
                if isinstance(value, float):
                    value = "{:n}".format(value)
                elif isinstance(value, datetime.date):
                    value = value.strftime(("%x", "%c")[isinstance(value, datetime.datetime)])
                else:
                    value = str(value)
                if role == Qt.ToolTipRole:
                    if len(value) < self.options["tooltip_min_len"]: value = ""
                return value
            else:
                return None

        if role == Qt.BackgroundRole:
            # Sets the data cell background shading pattern
            if self.options["striped"] and row % 2:
                return QBrush(QColor(self.options["stripesColor"]))

        if role in (HorizontalHeaderDataRole, VerticalHeaderDataRole):
            hm = QtGui.QStandardItemModel()
            hm.appendRow(self.readLevel(orient=role))
            return hm

    def sort(self, column, order):
        """
        Sort the DataFrame by column according to order

        Args:
            column (int): Index of the column (far left column = 0)
            order (int): Ascending = 0, Descending = 1

        Returns: None
        """

        if len(self.df) == 0:
            return

        # Ascending order flag
        asc = order == Qt.AscendingOrder

        self.layoutAboutToBeChanged.emit()
        # na_pos = 'first' if (self.options["na_values"] == "least") == asc else 'last'
        na_pos = 'last'
        self.df.sort_values(self.df.columns[column], ascending=asc, inplace=True, na_position=na_pos)
        self.layoutChanged.emit()

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole: return
        label = getattr(self.df, ("columns", "index")[orientation != Qt.Horizontal])[section]
        #        return label if type(label) is tuple else label
        return ("\n", " | ")[orientation != Qt.Horizontal].join(str(i) for i in label) if type(label) is tuple else str(
            label)

    def readLevel(self, y=0, xs=0, xe=None, orient=None):
        print("-----------")
        print("readLevel({}, {}, {}, {})".format(y, xs, xe, orient))
        print("y", y)
        print("xs", xs)
        print("xe", xe)
        print("orient", orient)

        c = getattr(self.df, ("columns", "index")[orient != HorizontalHeaderDataRole])
        if not hasattr(c, "levels"):  # not MultiIndex
            return [QtGui.QStandardItem(str(i)) for i in c]
        sibl = []
        section_start, v, xe = xs, None, xe or len(c)
        for i in range(xs, xe):
            label = c.labels[y][i]
            if label != v:
                if y + 1 < len(c.levels) and i > xs:
                    children = self.readLevel(y + 1, section_start, i, orient=orient)
                    sibl[-1].appendRow(children)
                item = QtGui.QStandardItem(str(c.levels[y][label]))
                sibl.append(item)
                section_start = i
                v = label
        if y + 1 < len(c.levels):
            children = self.readLevel(y + 1, section_start, orient=orient)
            sibl[-1].appendRow(children)
        return sibl

    def reorder(self, oldLocation, newLocation, orientation):
        """
        Rearrange rows / columns in the header by rearranging the underlying df index values.
        This happens when you drag around them in the header.

        Args:
            oldLocation (): Index of the
            newLocation ():
            orientation ():

        Returns: True

        """
        print("-----------")
        print("reorder()")
        print("oldIndex", oldLocation)
        print("newIndex", newLocation)
        print("orientation", orientation)

        # # Swap rows
        # old = self.df.iloc[oldLocation].copy()
        # new = self.df.iloc[newLocation].copy()
        # self.df.iloc[oldLocation], self.df.iloc[newLocation] = new, old

        horizontal = orientation == Qt.Horizontal
        print(horizontal)
        if horizontal:
            cols = list(self.df.columns)
            cols.insert(newLocation, cols.pop(oldLocation))
            self.df = self.df[cols]
        else:
            cols = list(self.df.index)
            cols.insert(newLocation, cols.pop(oldLocation))
            self.df = self.df.T[cols].T

        return True

    #    def filter(self, filt=None):
    #        self.df = self.df_full if filt is None else self.df[filt]
    #        self.layoutChanged.emit()


class DataFrameView(QtWidgets.QTableView):
    def __init__(self):
        super().__init__()
        HierarchicalHeaderView(orientation=Qt.Horizontal, parent=self)
        HierarchicalHeaderView(orientation=Qt.Vertical, parent=self)
        self.horizontalHeader().setSectionsMovable(True)
        self.verticalHeader().setSectionsMovable(True)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    # Prepare sample data with 3 index levels
    tuples = [('A', 'one', 'X'), ('A', 'one', 'Y'), ('A', 'two', 'X'), ('A', 'two', 'Y'),
              ('B', 'one', 'X'), ('B', 'one', 'Y'), ('B', 'two', 'X'), ('B', 'two', 'Y')]
    index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second', 'third'])
    df = pd.DataFrame(pd.np.random.randint(0, 10, (8, 8)), index=index[:8], columns=index[:8])

    if 0:
        # Prepare sample data with 2 index levels
        tuples = [('A', 'one'), ('A', 'two'),
                  ('B', 'one'), ('B', 'two')]
        index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second'])
        df = pd.DataFrame(pd.np.random.randint(0, 10, (4, 4)), index=index[:8], columns=index[:8])

    if 1:
        # Prepare sample data basic
        data = pd.np.random.randint(0, 10, (10, 3)).astype(float)
        data[0][0] = pd.np.nan
        print(data)
        df = pd.DataFrame(data, columns=['col1', 'col2', 'col3'])

    print("DataFrame:\n%s" % df)

    # Build GUI
    window = QtWidgets.QWidget()
    view = DataFrameView()
    view.setModel(DataFrameModel(df))
    QtWidgets.QVBoxLayout(window).addWidget(view)
    window.show()

    # Settings & appearance
    window.setMinimumSize(700, 360)
    view.setSortingEnabled(True)
    view.resizeColumnsToContents()
    view.resizeRowsToContents()

    app.exec()
