# -*- coding:utf-8 -*-

from z3 import (
    ExprRef,
)

from constants import (
    If,
    Not,
    Or,
    And,
    Z3_NULL_VALUE,
    POS_INF__Int,
)
from formulas import register_formula
from formulas.columns.aggregations.aggregation import (
    FAggregation,
    CONSTANT_TYPE,
)
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.expression_tuple import FExpressionTuple
from utils import (
    _MIN,
    simplify,
)


@register_formula('agg_min')
class FAggMin(FAggregation):
    def __init__(self, scope, function: str, expression: FBaseExpression, **kwargs):
        super(FAggMin, self).__init__(scope, function, expression, **kwargs)

    def __expr__(self, y_s, group_func=None, **kwargs):
        deleted_func = kwargs.get('deleted_func', self.DELETED_FUNCTION)
        if isinstance(y_s, ExprRef):
            y_s = [y_s]
        if isinstance(self.EXPR, CONSTANT_TYPE):
            return self(None)
        else:
            value_formulas = []
            count_formulas = []
            for y in y_s:
                curr_expr = self(y)
                premise = [deleted_func(y), curr_expr.NULL]
                if group_func is not None:
                    premise.append(Not(group_func(y)))
                if self.filter_cond is not None:
                    filter_cond = self.filter_cond(y)
                    premise.extend([filter_cond.NULL, Not(filter_cond.VALUE)])
                premise = simplify(premise, operator=Or)
                count_formulas.append(premise)
                value_formulas.append(
                    If(premise, POS_INF__Int, self._safe_value(curr_expr.VALUE))
                )
                # register bound constraint for MAX(EXPR)
                self.scope.bound_constraints.add(POS_INF__Int > curr_expr.VALUE)
            NULL = simplify(count_formulas, operator=And)
            return FExpressionTuple(
                NULL=NULL,
                VALUE=If(
                    NULL,  # all DELETED/NULL
                    Z3_NULL_VALUE,  # if all DELETED/NULL, its value does not matter
                    _MIN(*value_formulas),
                ),
            )
