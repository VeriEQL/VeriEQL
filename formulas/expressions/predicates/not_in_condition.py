# -*- coding: utf-8 -*-

from typing import Sequence

from errors import NotSupportedError
from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.expression import FExpression
from formulas.expressions.operator import FOperator
from formulas.expressions.predicates.base_predicate import FBasePredicate


def _fuzzy_check(proj_attrs, groupby_keys):
    from formulas.columns.attribute import FAttribute
    for attr in proj_attrs:
        if not isinstance(attr, FAttribute):
            return False
        if attr.EXPR is None:
            if attr not in groupby_keys:
                return True
        else:
            if isinstance(attr.EXPR, FExpression):
                for opd in attr.EXPR:
                    if _fuzzy_check([opd], groupby_keys):
                        return True


@register_formula('not_in_condition')
class FNotInPredicate(FBasePredicate):
    def __init__(self, attributes: Sequence[FBaseExpression], table):
        super(FNotInPredicate, self).__init__(
            operator=FOperator('nin'),
            operands=[attributes, table],
        )
        from formulas.tables import (
            FBaseTable,
            FProjectionTable,
            FGroupByTable,
            FLimitTable,
            FOrderByTable,
        )

        if isinstance(table, FBaseTable):
            # group by + order + limit
            groupby_table = table
            if isinstance(groupby_table, FProjectionTable):
                groupby_table = groupby_table.fathers[0]
            if isinstance(groupby_table, FLimitTable):
                groupby_table = groupby_table.fathers[0]
            if isinstance(groupby_table, FOrderByTable):
                groupby_table = groupby_table.fathers[0]
            if isinstance(groupby_table, FGroupByTable) and \
                    _fuzzy_check(table.attributes, groupby_table.groupby_keys[0]):
                raise NotSupportedError(
                    f"{self.__class__.__name__} contains a table with fuzzy attributes of GroupBy.")

        self.require_tuples = any(getattr(opd, 'require_tuples', False) for opd in attributes)

    def __str__(self):
        return f'{self.operands[0]}_{self.operator}_{self.operands[1].name}'
