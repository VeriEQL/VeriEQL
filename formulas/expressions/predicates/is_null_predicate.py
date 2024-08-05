# -*- coding:utf-8 -*-

from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.operator import FOperator
from formulas.expressions.predicates.base_predicate import FBasePredicate


@register_formula('is_null')
class FIsNullPredicate(FBasePredicate):
    def __init__(self, operand: FBaseExpression):
        super(FIsNullPredicate, self).__init__(
            operator=FOperator('eq'),
            operands=[operand],
        )

    @property
    def value(self):
        return self.operands[0]

    def __str__(self):
        return f'{self.operands[0]}_IS_NULL'
