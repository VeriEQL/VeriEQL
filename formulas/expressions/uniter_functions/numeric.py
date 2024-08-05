# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.uniter_functions.base_function import FUninterpretedFunction


@register_formula('numeric')
class FNumeric(FUninterpretedFunction):
    def __init__(self):
        super(FNumeric, self).__init__(operands=['NUMERIC'])
