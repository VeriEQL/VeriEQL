# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.uniter_functions.base_function import FUninterpretedFunction


@register_formula('decimal')
class FDecimal(FUninterpretedFunction):
    def __init__(self, *args):
        self.EXPR = args[0]
        super(FDecimal, self).__init__(operands=['DECIMAL', self.EXPR, *args[1:]])
