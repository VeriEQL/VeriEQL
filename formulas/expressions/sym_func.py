# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions import FExpression


@register_formula('sym_func')
class FSymbolicFunc(FExpression):
    def __init__(self, func, operands):
        super(FSymbolicFunc, self).__init__(func, operands)

    def __eq__(self, other):
        if isinstance(other, FSymbolicFunc):
            return self.operator == other.operator
        else:
            return False

    def __str__(self):
        return f'{self.operator}({[opd.name for opd in self.operands]})'
