# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.uniter_functions.base_function import FUninterpretedFunction


@register_formula('cast')
class FCast(FUninterpretedFunction):
    def __init__(self, value, type):
        self.EXPR = value
        super(FCast, self).__init__(operands=['CAST', self.EXPR, type])

    @property
    def type(self):
        return self[2]
