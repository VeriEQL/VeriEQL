# -*- coding:utf-8 -*-


from formulas import register_formula
from formulas.base_formula import BaseFormula
from utils import __pos_hash__


@register_formula('symbol')
class FSymbol(BaseFormula):
    """
    FSymbol only restore a `value` variable to represent
        - literal, i.e., numerals (constant), bools (base predicate),
        - variable name, i.e., symbols,
    """

    def __init__(self, literal: str | int | float, append_prefix=True):
        if isinstance(literal, str) and append_prefix:
            self.value = 'String_' + literal
        else:
            self.value = literal

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, FSymbol):
            return self.value == other.value
        else:
            return self.value == other

    def __hash__(self):
        return __pos_hash__(self.value)
