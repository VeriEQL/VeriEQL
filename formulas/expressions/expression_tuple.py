# -*- coding: utf-8 -*-


from z3 import (
    ArithRef,
)

from constants import (
    And,
    Not,
)


class FExpressionTuple:
    __slots__ = ['VALUE', 'NULL', 'attribute', 'tuple']

    def __init__(self, NULL=None, VALUE=None, attribute=None, tuple=None):
        # self.VALUE: IntermFunc | Callable | BaseFormula = None
        # self.NULL: IntermFunc | Callable | BaseFormula = None
        self.NULL = NULL
        self.VALUE = VALUE
        self.attribute = attribute
        self.tuple = tuple

    def __call__(self, *args, **kwargs):
        return self.VALUE(*args, **kwargs)

    def __str__(self):
        return f"{self.__class__.__name__}(NULL={self.NULL}, VALUE={self.VALUE})"

    def __eq__(self, other):
        if isinstance(other, FExpressionTuple):
            return And(
                self.NULL == other.NULL,
                self.VALUE == other.VALUE,
            )
        elif isinstance(other, ArithRef):
            return And(Not(self.NULL), self.VALUE == other)
        else:
            raise NotImplementedError

    def __repr__(self):
        return self.__str__()
