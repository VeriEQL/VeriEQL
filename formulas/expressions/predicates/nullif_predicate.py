# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.operator import FOperator
from formulas.expressions.predicates.base_predicate import FBasePredicate


@register_formula('nullif_predicate')
class FNullIfPredicate(FBasePredicate):
    def __init__(self, operands):
        super(FNullIfPredicate, self).__init__(
            operator=FOperator('if'),
            operands=operands,
        )

    def __str__(self):
        return f'{self.operator}_{"_".join([str(clause) for clause in self.operands])}'
