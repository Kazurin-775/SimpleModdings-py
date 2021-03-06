import os
from typing import List
from BinaryPatch import BinaryReplacePattern, BinarySearchPattern
import yaml
from PySide6.QtCore import QObject, QRunnable, Signal


class Patch:
    def dry_run(self, data: bytearray) -> None:
        pass

    def run_on(self, data: bytearray) -> bytearray:
        return data


class BytesPatch(Patch):
    def __init__(self, meta):
        super().__init__()
        self.original = BinarySearchPattern(meta['original'])
        self.replaced = BinaryReplacePattern(meta['replaced'])
        assert(self.original.len == self.replaced.len)
        self.occurrences = meta['occurrences'] if 'occurrences' in meta else 1
        self.comments = meta['comments']

    def dry_run(self, data: bytearray, executor) -> None:
        executor.message.emit('  应用补丁：' + self.comments)
        # behavior: non-overlapping
        result = self.original.matches(data)
        executor.message.emit('    找到 ' + str(len(result)) + ' 处匹配：' +
                              '，'.join(map(hex, result)))
        if len(result) != self.occurrences:
            executor.message.emit('    【错误】匹配数量过多或过少，将跳过该补丁')

    def run_on(self, data: bytearray, executor) -> bytearray:
        executor.message.emit('  应用补丁：' + self.comments)
        result = self.original.matches(data)
        executor.message.emit('    找到 ' + str(len(result)) + ' 处匹配：' +
                              '，'.join(map(hex, result)))
        if len(result) == self.occurrences:
            self.replaced.write_at(data, result)
        else:
            executor.message.emit('    【错误】匹配数量过多或过少，将跳过该补丁')
        return data


class StringPatch(Patch):
    def __init__(self, meta):
        super().__init__()
        self.original = meta['original'].encode('UTF-8')
        self.replaced = meta['replaced'].encode('UTF-8')
        self.occurrences = meta['occurrences'] if 'occurrences' in meta else 1
        self.comments = meta['comments']

    def matches(self, data: bytearray) -> List[int]:
        # behavior: non-overlapping
        result = [data.find(self.original)]
        while result[-1] >= 0:
            found = data.find(self.original, result[-1] + len(self.original))
            result.append(found)
        assert(result[-1] == -1)
        result.pop()
        return result

    def dry_run(self, data: bytearray, executor) -> None:
        executor.message.emit('  应用补丁：' + self.comments)
        result = self.matches(data)
        executor.message.emit('    找到 ' + str(len(result)) + ' 处匹配：' +
                              '，'.join(map(hex, result)))
        if len(result) != self.occurrences:
            executor.message.emit('    【错误】匹配数量过多或过少，将跳过该补丁')

    def run_on(self, data: bytearray, executor) -> bytearray:
        executor.message.emit('  应用补丁：' + self.comments)
        result = self.matches(data)
        executor.message.emit('    找到 ' + str(len(result)) + ' 处匹配：' +
                              '，'.join(map(hex, result)))
        if len(result) == self.occurrences:
            data = data.replace(self.original, self.replaced)
        else:
            executor.message.emit('    【错误】匹配数量过多或过少，将跳过该补丁')
        return data


class Patchset(Patch):
    def __init__(self, patches_meta: List[dict], patchsets: dict[str, Patch]) -> None:
        self.patches = list(
            map(lambda x: create_patch(x, patchsets), patches_meta)
        )

    def dry_run(self, data: bytearray, executor) -> None:
        for patch in self.patches:
            patch.dry_run(data, executor)

    def run_on(self, data: bytearray, executor) -> bytearray:
        for patch in self.patches:
            data = patch.run_on(data, executor)
        return data


def create_patch(meta: dict, patchsets: dict[str, Patchset]) -> Patch:
    if meta['kind'] == 'bytes':
        return BytesPatch(meta)
    elif meta['kind'] == 'string':
        return StringPatch(meta)
    elif meta['kind'] == 'patchset':
        return patchsets[meta['name']]
    else:
        raise ValueError('unknown patch kind: ' + meta['kind'])


class PatchedFile:
    def __init__(self, name: str, patches_meta: List[dict], patchsets: dict[str, Patchset]) -> None:
        self.name = name
        self.patchset = Patchset(patches_meta, patchsets)

    def dry_run(self, inpath: str, executor) -> None:
        executor.message.emit('处理文件：' + self.name)
        with open(inpath, 'rb') as file:
            data = bytearray(file.read())
        self.patchset.dry_run(data, executor)

    def run_on(self, inpath: str, executor) -> None:
        executor.message.emit('处理文件：' + self.name)
        with open(inpath, 'rb') as file:
            data = bytearray(file.read())
        # make backup
        if os.access(inpath + '.bak', os.F_OK):
            executor.message.emit('警告：文件 ' + self.name + '.bak 已存在，将不创建备份')
        else:
            executor.message.emit('创建备份文件 ' + self.name + '.bak')
            os.rename(inpath, inpath + '.bak')
        data = self.patchset.run_on(data, executor)
        with open(inpath, 'wb') as file:
            file.write(data)


class PatchExecutor(QObject):
    message = Signal(str)
    finished = Signal()

    def __init__(self, parent: QObject, path: str) -> None:
        super().__init__(parent)
        self.parent = parent

        with open(path, 'r', encoding='UTF-8') as file:
            content = file.read()
        self.patch = yaml.load(content, Loader=yaml.SafeLoader)
        self.name = self.patch['name']
        self.default_path = self.patch['default_path']
        self.compile_patches()

        self.message.connect(self.parent.on_message)
        self.message.emit('已载入补丁：' + self.name)

        self.test_mode = False

    def compile_patches(self) -> None:
        patchsets: dict[str, Patchset] = {}
        # compile patchsets
        if 'patchsets' in self.patch:
            for name, meta in self.patch['patchsets'].items():
                patchsets[name] = Patchset(meta, patchsets)
        # compile patches
        patches: List[PatchedFile] = []
        for name, meta in self.patch['patches'].items():
            patches.append(PatchedFile(name, meta, patchsets))
        self.patches = patches

    def dry_run(self, prog_path: str) -> None:
        self.message.emit('开始执行补丁【测试模式】')
        for patch in self.patches:
            patch.dry_run(os.path.join(prog_path, patch.name), self)
        self.message.emit('补丁执行完成')
        self.finished.emit()

    def run_on(self, prog_path: str) -> None:
        self.message.emit('开始执行补丁')
        for patch in self.patches:
            patch.run_on(os.path.join(prog_path, patch.name), self)
        self.message.emit('补丁执行完成')
        self.finished.emit()

    def run(self) -> None:
        if self.test_mode:
            self.dry_run(self.prog_path)
        else:
            self.run_on(self.prog_path)


class PatchTask(QRunnable):
    def __init__(self, parent: QObject, inner: PatchExecutor) -> None:
        super().__init__(parent)
        self.inner = inner

    def run(self) -> None:
        self.inner.run()
