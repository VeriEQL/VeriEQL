# -*- coding: utf-8 -*-


from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.predicates.base_predicate import FBasePredicate


@register_formula('power_predicate')
class FPowerPredicate(FBasePredicate):
    def __init__(self, expression: FBaseExpression, exponent: FBaseExpression | int | float):
        super(FPowerPredicate, self).__init__(
            operator=None,
            operands=[expression, exponent],
        )

    def __str__(self):
        return f'POWER_{"_".join(str(opd) for opd in self.operands)}'
