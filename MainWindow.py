from PySide6.QtCore import Slot
from PySide6 import QtGui, QtWidgets
from Ui_MainWindow import Ui_MainWindow
from ChoosePatchDialog import ChoosePatchDialog
from PatchExecutor import PatchExecutor

# pyside6-uic mainwindow.ui -o Ui_MainWindow.py


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.btnChoosePatch.clicked.connect(self.choose_patch)

    @Slot(str)
    def on_message(self, msg: str) -> None:
        self.ui.txtStatus.appendPlainText(msg + '\n')

    @Slot()
    def choose_patch(self) -> None:
        dlg = ChoosePatchDialog(self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            patch_file = dlg.patch_file()
            self.ui.btnChoosePatch.setText(patch_file)
            pe = PatchExecutor(self, 'patches/' + patch_file)
            self.ui.txtProgramPath.setText(pe.default_path)
