from PySide6.QtCore import QObject, QRunnable


class PatchExecutor(QRunnable, QObject):
    def __init__(self, parent: QObject, path: str):
        QRunnable.__init__(self)
        QObject.__init__(self, parent)
        self.parent = parent

        with open(path, 'r', encoding='UTF-8') as file:
            code = file.read()
        locals = dict()
        exec(code, globals(), locals)
        self.name = locals['name']
        self.default_path = locals['default_path']
        self.patch = locals['patch']

        self.parent.on_message('已载入补丁：' + self.name)

    def run(self):
        pass
