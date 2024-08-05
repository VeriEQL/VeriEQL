# -*- coding: utf-8 -*-


from formulas import register_formula
from formulas.expressions.expression import FExpression


@register_formula('base_predicate')
class FBasePredicate(FExpression):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
