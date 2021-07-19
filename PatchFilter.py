import os
from typing import List
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot


class PatchListFuture(QRunnable, QObject):
    finished = Signal(list)

    def __init__(self, parent: QObject) -> None:
        QRunnable.__init__(self)
        QObject.__init__(self, parent)

    def run(self) -> None:
        self.finished.emit(os.listdir('patches'))


class PatchFilterFuture(QRunnable, QObject):
    finished = Signal(list)

    def __init__(self, parent: QObject, file_list: List[str], filter: str) -> None:
        QRunnable.__init__(self)
        QObject.__init__(self, parent)
        self.file_list = file_list
        self.filter = filter

    def run(self) -> None:
        self.filter = self.filter.lower()
        filtered = []
        for file in self.file_list:
            if file.lower().find(self.filter) >= 0:
                filtered.append(file)
        self.finished.emit(filtered)


class PatchFilterMonitor(QObject):
    updated = Signal(list)

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self.file_list = []
        self.filter = ''
        self.running = False
        self.pending = False
        future = PatchListFuture(self)
        future.finished.connect(self.load_file_list)
        QThreadPool.globalInstance().start(future)

    @Slot(str)
    def set_filter(self, new_filter: str) -> None:
        self.filter = new_filter
        if not self.file_list:
            return
        if not self.running:
            self.running = True
            future = PatchFilterFuture(self, self.file_list, self.filter)
            future.finished.connect(self.finished)
            QThreadPool.globalInstance().start(future)
        else:
            self.pending = True

    @Slot()
    def load_file_list(self, result: List[str]) -> None:
        self.file_list = result
        if self.filter:
            self.set_filter(self.filter)
        else:
            self.updated.emit(self.file_list)

    @Slot(list)
    def finished(self, result: List[str]) -> None:
        self.updated.emit(result)
        self.running = False
        if self.pending:
            self.pending = False
            self.set_filter(self.filter)
