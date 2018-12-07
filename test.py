#!/usr/bin/env python3
# -*- coding: utf-8 -*-
 
import sys
from PyQt5.QtGui import QIcon
 
from PyQt5.QtCore import (QDate, QDateTime, QRegExp, QSortFilterProxyModel, Qt,
        QTime)
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
        QGroupBox, QHBoxLayout, QLabel, QLineEdit, QTreeView, QVBoxLayout,
        QWidget)
 
 
class App(QWidget):
 
    FROM, SUBJECT, DATE = range(3)
 
    def __init__(self):
        super().__init__()
        self.title = 'PyQt5 Treeview Example - pythonspot.com'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 240
        self.initUI()
 
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
 
        self.dataGroupBox = QGroupBox("Inbox")
        self.dataView = QTreeView()
        self.dataView.setRootIsDecorated(False)
        self.dataView.setAlternatingRowColors(True)
 
        dataLayout = QHBoxLayout()
        dataLayout.addWidget(self.dataView)
        self.dataGroupBox.setLayout(dataLayout)
 
        model = self.createMailModel(self)
        self.dataView.setModel(model)
        self.addMail(model, 'service@github.com', 'Your Github Donation','03/25/2017 02:05 PM')
        self.addMail(model, 'support@github.com', 'Github Projects','02/02/2017 03:05 PM')
        self.addMail(model, 'service@phone.com', 'Your Phone Bill','01/01/2017 04:05 PM')
 
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.dataGroupBox)
        self.setLayout(mainLayout)
 
        self.show()
 
    def createMailModel(self,parent):
        model = QStandardItemModel(0, 3, parent)
        model.setHeaderData(self.FROM, Qt.Horizontal, "ok")
        model.setHeaderData(self.SUBJECT, Qt.Horizontal, "Subject")
        model.setHeaderData(self.DATE, Qt.Horizontal, "Date")
        return model
 
    def addMail(self,model, mailFrom, subject, date):
        model.insertRow(0)
        model.setData(model.index(0, self.FROM), mailFrom)
        model.setData(model.index(0, self.SUBJECT), subject)
        model.setData(model.index(0, self.DATE), date)
 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())