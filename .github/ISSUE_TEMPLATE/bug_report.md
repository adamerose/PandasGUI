---
name: Bug report
about: Create a report to help us improve
title: ''
labels: bug
assignees: ''

---

**Before making a bug report, please check that you are able to run the code snippet below with no errors. It should display a window with a button. If this doesn't work, your problem with with PyQt5 and not PandasGUI specifically (and in that case I recommend you try reinstalling `PyQt5`, `PyQtWebEngine`, and `PyQt5-sip`)**

**Also make sure you're still able to reproduce the bug with the latest release (run `pip install --upgrade pandasgui`).**

```
from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets, sip
app = QtWidgets.QApplication([])
test = QtWidgets.QPushButton("test")
test.show()
app.exec_()
```
-----------------------

**Describe the bug**  
A clear and concise description of what the bug is and how to reproduce it. If applicable, add screenshots.

**Package versions. To get all relevant versions, run this command in bash and paste the output**  
```
pip freeze | grep -i "pyqt\|pandasgui\|plotly"
```
```
# Example output
pandasgui==0.2.5.1
plotly==4.9.0
PyQt5==5.15.1
PyQt5-sip==12.8.1
PyQtWebEngine==5.15.1
```
