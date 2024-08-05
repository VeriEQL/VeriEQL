# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.uniter_functions.base_function import FUninterpretedFunction


@register_formula('date')
class FDate(FUninterpretedFunction):
    def __init__(self, value):
        self.EXPR = value
        super(FDate, self).__init__(operands=['DATE', self.EXPR])
