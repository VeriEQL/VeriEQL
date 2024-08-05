# -*- coding: utf-8 -*-


import abc

from formulas import register_formula
from formulas.base_formula import BaseFormula


@register_formula('base_expression')
class FBaseExpression(BaseFormula):
    """
    Expression:
        Attribute, e.g., EMP.age
        | Aggregation, e.g., SUM(EMP.age - AVG(EMP.age))
        | Operator Expression*, e.g., (+ (1, 2))
        | Function, e.g., Round(A-B, 6)
        | Statement, e.g., CASE (WHEN Expression THEN Expression)+ (ELSE Expression)* END
    """

    def __init__(self, NULL=None):
        self.NULL = NULL
        self.uninterpreted_func = None
        self.require_tuples = False

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def __expr__(self, *args, **kwargs):
        pass

    @property
    def is_uninterpreted_func(self):
        return self.uninterpreted_func is not None
