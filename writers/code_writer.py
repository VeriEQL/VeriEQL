# -*- coding: utf-8 -*-

from typing import (
    Sequence,
    Optional,
)

from utils import CodeSnippet


class CodeWriter(object):
    def __init__(self, code: Optional[Sequence[CodeSnippet]] = None, docstring: str = None):
        self.code = code or []
        self.docstring = '# ' + (docstring or '')

    def __str__(self, comma=False):
        code = f'{"," if comma else ""}\n'.join([str(code) for code in self.code])

        if len(self.docstring) > 2:
            return '{}\n{}'.format(self.docstring, code)
        else:
            return code

    def append(self, code: CodeSnippet):
        self.code.append(code)

    def __getitem__(self, index):
        return self.code[index]

    def __len__(self):
        return len(self.code)
