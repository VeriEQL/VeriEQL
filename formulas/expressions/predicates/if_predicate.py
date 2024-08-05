# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.operator import FOperator
from formulas.expressions.predicates.base_predicate import FBasePredicate


@register_formula('if_predicate')
class FIfPredicate(FBasePredicate):
    def __init__(self, cond: FBaseExpression, then_clause: FBaseExpression, else_clause: FBaseExpression):
        super(FIfPredicate, self).__init__(
            operator=FOperator('if'),
            operands=[cond, then_clause, else_clause],
        )

    def __str__(self):
        return f'{self.operator}_{"_".join([str(clause) for clause in self.operands])}'
