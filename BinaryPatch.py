import re
from typing import List


class BinarySearchPattern:
    REGEX_ESCAPE = set(b'\\^$.|?*+()[]{}')

    def __init__(self, repr: str) -> None:
        repr = repr.replace(' ', '')
        assert(len(repr) % 2 == 0)
        self.len = len(repr) // 2
        regex = b''
        for i in range(0, len(repr), 2):
            byte = repr[i:i + 2]
            if byte == '??':
                regex += b'.'
            else:
                byte = bytes([int('0x' + byte, 16)])
                if byte[0] in BinarySearchPattern.REGEX_ESCAPE:
                    regex += b'\\' + byte
                else:
                    regex += byte
        self.regex = re.compile(regex, re.RegexFlag.DOTALL)

    def matches(self, target: bytes) -> List[int]:
        matches = []
        for match in self.regex.finditer(target):
            matches.append(match.start())
        return matches


class BinaryReplacePattern:
    class PatternByte:
        def __init__(self, repr: str) -> None:
            if repr == '??':
                self.value = None
            else:
                self.value = int('0x' + repr, 16)

        def write_at(self, dest: bytearray, index: int) -> None:
            if self.value:
                dest[index] = self.value

    def __init__(self, repr: str) -> None:
        repr = repr.replace(' ', '')
        assert(len(repr) % 2 == 0)
        self.len = len(repr) // 2
        self.pat_bytes = []
        for i in range(0, len(repr), 2):
            self.pat_bytes.append(
                BinaryReplacePattern.PatternByte(repr[i:i + 2]))

    def write_at(self, dest: bytearray, indices: List[int]) -> None:
        for i in indices:
            for j in range(len(self.pat_bytes)):
                self.pat_bytes[j].write_at(dest, i + j)
