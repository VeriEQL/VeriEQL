# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.predicates.base_predicate import FBasePredicate


@register_formula('mod_predicate')
class FModPredicate(FBasePredicate):
    def __init__(self, expression: FBaseExpression, arg):
        super(FModPredicate, self).__init__(
            operator=None,
            operands=[expression, arg],
        )

    def __str__(self):
        return f'MOD_{self.operands[0]}_{self.operands[1]}'
