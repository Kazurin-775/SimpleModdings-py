from PySide6 import QtGui, QtWidgets
from MainWindow import MainWindow

app = QtWidgets.QApplication([])
font = QtGui.QFont()
font.setFamily('Microsoft YaHei UI')
font.setPointSize(app.font().pointSize())
app.setFont(font)
window = MainWindow()
window.show()
app.exec()
