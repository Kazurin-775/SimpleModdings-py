from PySide6.QtCore import QThreadPool, Slot
from PySide6 import QtGui, QtWidgets
from Ui_MainWindow import Ui_MainWindow
from ChoosePatchDialog import ChoosePatchDialog
from PatchExecutor import PatchExecutor, PatchTask

# pyside6-uic mainwindow.ui -o Ui_MainWindow.py


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.btnChoosePatch.clicked.connect(self.choose_patch)
        self.ui.btnExecute.clicked.connect(self.execute_patch)

    @Slot(str)
    def on_message(self, msg: str) -> None:
        self.ui.txtStatus.appendPlainText(msg)

    @Slot()
    def choose_patch(self) -> None:
        dlg = ChoosePatchDialog(self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            patch_file = dlg.patch_file()
            self.load_patch(patch_file)

    def load_patch(self, patch_file: str) -> None:
        self.ui.btnChoosePatch.setText(patch_file)
        self.pe = PatchExecutor(self, 'patches/' + patch_file)
        self.ui.txtProgramPath.setText(self.pe.default_path)
        self.pe.prog_path = self.pe.default_path
        self.pe.finished.connect(
            lambda: self.ui.btnExecute.setEnabled(True)
        )

    @Slot()
    def execute_patch(self) -> None:
        self.ui.btnExecute.setEnabled(False)
        self.pe.test_mode = self.ui.chkTestMode.isChecked()
        self.pe.prog_path = self.ui.txtProgramPath.text()
        # `start()`` always creates a new `QThread`, and when the thread exits,
        # the `QRunnable` gets deleted.
        # `PatchTask` prevents this from causing a double free.
        QThreadPool.globalInstance().start(PatchTask(self, self.pe))
