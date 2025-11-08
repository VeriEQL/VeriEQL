# -*- coding:utf-8 -*-

import operator
from typing import Any

from constants import (
    Not,
    And,
    Or,
    If,
    Implies,
    Z3_0,
    Z3_1,
)
from formulas import register_formula
from formulas.base_formula import BaseFormula
from utils import __pos_hash__


class _Operator(BaseFormula):
    def __init__(self,
                 abbr: str,
                 console: str = None,
                 value: Any = None,
                 ):
        self.abbr = abbr  # symbol name from `mo_sql_parsing`
        self.console = console  # for console (debug)
        self.value = value  # `operator` or `z3`

    def __eq__(self, other):
        return (self.abbr == other.abbr) or (self.console == other.console) or \
            (self.value == other.value)

    def __str__(self):
        return self.abbr

    def __call__(self, *args, **kwargs):
        try:
            return self.value(*args, **kwargs)
        except TypeError as err:
            if self.value in {operator.add, operator.sub, operator.mul, operator.truediv}:
                return self.value(*[If(arg, Z3_1, Z3_0) for arg in args])
            elif self.value in {operator.neg}:
                return self.value(*[arg != Z3_0 for arg in args])
            else:
                raise NotImplementedError(self.value, *args)
        except Exception as err:
            return self.value(*args, **kwargs)


_OPERATOR_DICT = {
    'add': _Operator(abbr='add', console='+', value=operator.add),
    'sub': _Operator(abbr='sub', console='-', value=operator.sub),
    'mul': _Operator(abbr='mul', console='*', value=operator.mul),
    'div': _Operator(abbr='div', console='/', value=operator.truediv),
    'neg': _Operator(abbr='neg', console='-', value=operator.neg),

    'gt': _Operator(abbr='gt', console='>', value=operator.gt),
    'gte': _Operator(abbr='gte', console='>=', value=operator.ge),
    'lt': _Operator(abbr='lt', console='<', value=operator.lt),
    'lte': _Operator(abbr='lte', console='<=', value=operator.le),
    'eq': _Operator(abbr='eq', console='=', value=operator.eq),
    'neq': _Operator(abbr='neq', console='!=', value=operator.ne),

    'not': _Operator(abbr='not', console='¬', value=Not),
    'and': _Operator(abbr='and', console='∧', value=And),
    'or': _Operator(abbr='or', console='∨', value=Or),
    'implication': _Operator(abbr='implication', console='→', value=Implies),

    'in': _Operator(abbr='in', console='IN', value=None),
    'nin': _Operator(abbr='nin', console='NOT_IN', value=None),
    'null': _Operator(abbr='null', console='IsNULL', value=None),
    'if': _Operator(abbr='if', console='IF', value=None),
    'function': _Operator(abbr='function', console='f', value=None),
    'distinct': _Operator(abbr='distinct', console='DISTINCT', value=None),
    'coalesce': _Operator(abbr='coalesce', console='COALESCE', value=None),
    'cast': _Operator(abbr='cast', console='CAST', value=None),
    'digit': _Operator(abbr='digit', console='Digits_', value=None),
    'exists': _Operator(abbr='exists', console='EXISTS_', value=None),

    'eq!': _Operator(abbr='eq!', console='IS_DISTINCT_FROM', value=None),
    'ne!': _Operator(abbr='ne!', console='IS_NOT_DISTINCT_FROM', value=None),
}


@register_formula('operator')
class FOperator(BaseFormula):
    def __init__(self, value: str):
        super(FOperator, self).__init__()
        self._operator = self.find(value)

    def __str__(self):
        return self._operator.__str__()

    def __eq__(self, other):
        if isinstance(other, FOperator):
            return self._operator == other._operator
        else:
            return (self.abbr == other) or (self.console == other)

    def __call__(self, *args, **kwargs):
        return self._operator(*args, **kwargs)

    @property
    def abbr(self):
        return self._operator.abbr

    @property
    def console(self):
        return self._operator.console

    @property
    def value(self):
        return self._operator.value

    @staticmethod
    def find(value: str):
        return _OPERATOR_DICT.get(value)

    def __hash__(self):
        return __pos_hash__(self.console)
