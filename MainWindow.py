from PySide6.QtCore import Slot
from PySide6 import QtGui, QtWidgets
from Ui_MainWindow import Ui_MainWindow
from ChoosePatchDialog import ChoosePatchDialog

# pyside6-uic mainwindow.ui -o Ui_MainWindow.py


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.btnChoosePatch.clicked.connect(self.choose_patch)

    @Slot()
    def choose_patch(self) -> None:
        dlg = ChoosePatchDialog(self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.ui.btnChoosePatch.setText(dlg.patch_file())
