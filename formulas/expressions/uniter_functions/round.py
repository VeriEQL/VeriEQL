# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.uniter_functions.base_function import FUninterpretedFunction


@register_formula('round')
class FRound(FUninterpretedFunction):
    """
    Round(expression, decimals, operation=0)
    uninterpreted function
    """

    def __init__(self, decimals: int = 0, operation: int = 0):
        super(FRound, self).__init__(
            operands=['ROUND', decimals, operation]
        )

    @property
    def decimals(self):
        return self[2]

    @property
    def operation(self):
        return self[3]
