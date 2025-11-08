# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.operator import FOperator
from formulas.expressions.predicates.base_predicate import FBasePredicate


@register_formula('exists_predicate')
class FExistsPredicate(FBasePredicate):
    """
    This predicate may refer to correlated subquery.

    WHERE EXISTS (
        SELECT XX FROM XX
    )
    """

    def __init__(self, clauses):
        super(FExistsPredicate, self).__init__(
            operator=FOperator('exists'),
            operands=[clauses],
        )

    def __str__(self):
        out = str(self.operands[0]).replace('\n', '')
        return f"EXISTS {out}"
