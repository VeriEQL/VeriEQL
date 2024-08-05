# -*- coding:utf-8 -*-

from typing import (
    Callable,
)

from z3 import FuncDeclRef

from utils import __pos_hash__


class IntermFunc:
    """
    Intermediate Function:
    Since python builtin lambda functions are ubiquitous, we design a powerful function to store any info of
    anonymous functions or SQL columns/attributes.
    """

    __slots__ = ['z3_function', 'description']

    def __init__(self,
                 z3_function: FuncDeclRef | Callable,
                 description: str = None,
                 ):
        self.z3_function = z3_function
        self.description = description or str(z3_function)

    def __eq__(self, other):
        if isinstance(other, IntermFunc):
            return __pos_hash__(self) == __pos_hash__(other)
        elif isinstance(other, FuncDeclRef):
            return self.z3_function == other
        else:
            raise NotImplementedError

    def __call__(self, *args, **kwargs):
        return self.z3_function(*args, **kwargs)

    def __str__(self):
        return self.description

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return __pos_hash__(self.__str__())
