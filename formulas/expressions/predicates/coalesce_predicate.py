# -*- coding: utf-8 -*-
from typing import Sequence

from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.operator import FOperator
from formulas.expressions.predicates.base_predicate import FBasePredicate


@register_formula('coalesce_predicate')
class FCoalescePredicate(FBasePredicate):
    def __init__(self, expressions: Sequence[FBaseExpression]):
        super(FCoalescePredicate, self).__init__(
            operator=FOperator('coalesce'),
            operands=expressions,
        )

    def __str__(self):
        return f'{self.operator}_{"_".join(str(operand) for operand in self.operands)}'
