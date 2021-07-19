from typing import List
from PatchFilter import PatchFilterMonitor
from PySide6.QtCore import Slot
from PySide6 import QtGui, QtWidgets
from Ui_ChoosePatchDialog import Ui_ChoosePatchDialog

# pyside6-uic choosepatchdialog.ui -o Ui_ChoosePatchDialog.py


class ChoosePatchDialog(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.ui = Ui_ChoosePatchDialog()
        self.ui.setupUi(self)

        self.ok_button = self.ui.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        self.ok_button.setEnabled(False)
        self.monitor = PatchFilterMonitor(self)
        self.monitor.updated.connect(self.update_file_list)
        self.ui.edtFilter.textChanged.connect(self.monitor.set_filter)

    @Slot()
    def update_file_list(self, new_list: List[str]) -> None:
        self.ui.lstPatches.clear()
        self.ui.lstPatches.addItems(new_list)
        if new_list:
            self.ui.lstPatches.setCurrentRow(0)
            self.ok_button.setEnabled(True)
        else:
            self.ok_button.setEnabled(False)

    def patch_file(self) -> str:
        return self.ui.lstPatches.currentItem().text()
