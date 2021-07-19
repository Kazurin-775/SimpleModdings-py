import yaml
from PySide6.QtCore import QObject, QRunnable


class PatchExecutor(QRunnable, QObject):
    def __init__(self, parent: QObject, path: str):
        QRunnable.__init__(self)
        QObject.__init__(self, parent)
        self.parent = parent

        with open(path, 'r', encoding='UTF-8') as file:
            content = file.read()
        self.patch = yaml.load(content, Loader=yaml.SafeLoader)
        self.name = self.patch['name']
        self.default_path = self.patch['default_path']

        self.parent.on_message('已载入补丁：' + self.name)

    def run(self):
        pass
