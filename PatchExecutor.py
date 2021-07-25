import os
from typing import List
from BinaryPatch import BinaryReplacePattern, BinarySearchPattern
import yaml
from PySide6.QtCore import QObject, QRunnable, Signal


class Patch:
    def dry_run(self, data: bytearray) -> None:
        pass


class BytesPatch(Patch):
    def __init__(self, meta):
        super().__init__()
        self.original = BinarySearchPattern(meta['original'])
        self.replaced = BinaryReplacePattern(meta['replaced'])
        assert(self.original.len == self.replaced.len)
        self.occurrences = meta['occurrences'] if 'occurrences' in meta else 1
        self.comments = meta['comments']

    def dry_run(self, data: bytearray, executor) -> None:
        executor.message.emit('应用补丁：' + self.comments)
        result = self.original.matches(data)
        executor.message.emit('    找到 ' + str(len(result)) + ' 处匹配：' +
                              '，'.join(map(hex, result)))
        if len(result) != self.occurrences:
            executor.message.emit('    【错误】匹配数量过多或过少，将跳过该补丁')


def create_patch(meta: dict) -> Patch:
    if meta['kind'] == 'bytes':
        return BytesPatch(meta)
    else:
        raise ValueError('unknown patch kind: ' + meta['kind'])


class PatchedFile:
    def __init__(self, name: str, patches_meta: dict) -> None:
        self.name = name
        self.patches = list(map(create_patch, patches_meta))

    def dry_run(self, inpath: str, executor) -> None:
        executor.message.emit('处理文件：' + self.name)
        with open(inpath, 'rb') as file:
            data = bytearray(file.read())
        for patch in self.patches:
            patch.dry_run(data, executor)


class PatchExecutor(QRunnable, QObject):
    message = Signal(str)
    finished = Signal()

    def __init__(self, parent: QObject, path: str) -> None:
        QRunnable.__init__(self)
        QObject.__init__(self, parent)
        self.parent = parent

        with open(path, 'r', encoding='UTF-8') as file:
            content = file.read()
        self.patch = yaml.load(content, Loader=yaml.SafeLoader)
        self.name = self.patch['name']
        self.default_path = self.patch['default_path']
        self.compile_patches()

        self.message.connect(self.parent.on_message)
        self.message.emit('已载入补丁：' + self.name)

    def compile_patches(self) -> None:
        patches: List[PatchedFile] = []
        for name, meta in self.patch['patches'].items():
            patches.append(PatchedFile(name, meta))
        self.patches = patches

    def dry_run(self, prog_path: str) -> None:
        self.message.emit('开始执行补丁')
        for patch in self.patches:
            patch.dry_run(os.path.join(prog_path, patch.name), self)
        self.message.emit('补丁执行完成')
        self.finished.emit()

    def run(self) -> None:
        self.dry_run(self.prog_path)
