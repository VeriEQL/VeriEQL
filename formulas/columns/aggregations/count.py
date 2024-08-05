# -*- coding:utf-8 -*-

from typing import (
    Sequence,
)

from z3 import (
    ExprRef,
)

from constants import (
    Sum,
    If,
    Not,
    Or,
    And,
    Z3_0,
    Z3_1,
    Z3_FALSE,
)
from formulas import register_formula
from formulas.columns.aggregations.aggregation import (
    FAggregation,
    CONSTANT_TYPE,
)
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.expression_tuple import FExpressionTuple
from utils import (
    simplify,
    uuid_hash,
)


@register_formula('agg_count')
class FAggCount(FAggregation):
    def __init__(self, scope, function: str, expression: FBaseExpression | Sequence, **kwargs):
        super(FAggCount, self).__init__(scope, function, expression, **kwargs)

    def __str__(self):
        if self.multi_exprs:
            expr_str = f'{"_".join([str(e) for e in self.EXPR])}_'
            if self.DISTINCT:
                return f'{self.KEY}_DISTINCT_{expr_str}'
            else:
                return f'{self.KEY}_{expr_str}'
        else:
            return super().__str__()

    def __call__(self, *args, **kwargs):
        if isinstance(self.EXPR, str) and self.EXPR == 'ALL':
            # COUNT(*), COUNT(1)
            return FExpressionTuple(NULL=self.scope.COUNT_ALL_NULL_FUNCTION, VALUE=self.scope.COUNT_ALL_FUNCTION)
        elif isinstance(self.EXPR, CONSTANT_TYPE):
            # COUNT(1)
            return FExpressionTuple(NULL=Z3_FALSE, VALUE=self.EXPR)
        elif self.multi_exprs:
            # COUNT(AGE - 1, AGE - 2)
            index = kwargs.pop('index')
            return self.scope.visitor.visit(self.EXPR[index])(*args, **kwargs)
        else:
            # COUNT(AGE - 1)/COUNT(AGE)
            return self.scope.visitor.visit(self.EXPR)(*args, **kwargs)

    def __uuid__(self):
        if isinstance(self.EXPR, str) and self.EXPR == 'ALL':
            return uuid_hash()
        else:
            return super().__uuid__()

    def __expr__(self, y_s, group_func=None, **kwargs):
        if isinstance(y_s, ExprRef):
            y_s = [y_s]
        deleted_func = kwargs.get('deleted_func', self.DELETED_FUNCTION)
        if self.filter_cond is not None and self.DISTINCT:
            prev_filter_conds = []
        if isinstance(self.EXPR, str) and self.EXPR == 'ALL':
            # COUNT(*) FILTER (WHERE CONDITION)
            count_formulas = []
            for y in y_s:
                premise = [deleted_func(y)]
                if self.filter_cond is not None:
                    filter_cond = self.filter_cond(y)
                    premise.extend([filter_cond.NULL, Not(filter_cond.VALUE)])  # if CONDITION is NULL or does not hold
                if group_func is not None:
                    premise.append(Not(group_func(y)))
                premise = simplify(premise, operator=Or)
                count_formulas.append(If(premise, Z3_0, Z3_1))
        else:
            count_formulas = []
            """
            COUNT(expr+) [FILTER_COND]
            1) current tuple is DELETED
            2) current tuple's expressions are NULL
            3) current tuple is NOT DELETED and its expressions are NOT NULL 
                but expressions' value are equal to one of previous tuples (if applicable)
            4) if FILTER_COND exists, 
                i) FILTER_COND is NULL
                ii) FILTER_COND does not hold
            """
            for idx, y in enumerate(y_s):
                if self.multi_exprs:
                    curr_exprs = [self(y, index=i) for i in range(len(self))]
                    premise = [deleted_func(y)] + [expr.NULL for expr in curr_exprs]
                    # In MySQL, COUNT(DISTINCT NULL, NULL) = 0 (we obey with)
                    # In PSQL, COUNT(DISTINCT NULL, NULL) = 1
                else:
                    curr_expr = self(y)
                    premise = [deleted_func(y), curr_expr.NULL]
                if self.DISTINCT and idx > 0:
                    for i, prev_y in enumerate(y_s[:idx]):
                        if self.multi_exprs:
                            prev_exprs = [self(prev_y, index=i) for i in range(len(self))]
                            prev_cond = [
                                Not(deleted_func(prev_y)),
                                # `curr_attr_value.NULL` must be False since we consider self.NULL(y) before
                                simplify([expr.NULL for expr in prev_exprs], operator=And, add_not=True),
                                simplify([
                                    curr_expr.VALUE == prev_expr.VALUE
                                    for curr_expr, prev_expr in zip(curr_exprs, prev_exprs)
                                ], operator=And)
                            ]
                        else:
                            prev_expr = self(prev_y)
                            prev_cond = [
                                Not(deleted_func(prev_y)),
                                Not(prev_expr.NULL),
                                curr_expr.VALUE == prev_expr.VALUE,
                            ]
                        if i != 0 and group_func is not None:
                            prev_cond.append(group_func(prev_y))  # distinct tuple should also belong to this group
                        if self.filter_cond is not None:
                            prev_cond.extend(prev_filter_conds)
                        prev_cond = simplify(prev_cond, operator=And)
                        premise.append(prev_cond)
                if group_func is not None:
                    premise.append(Not(group_func(y)))
                if self.filter_cond is not None:
                    filter_cond = self.filter_cond(y)
                    premise.extend([filter_cond.NULL, Not(filter_cond.VALUE)])
                    if self.DISTINCT:
                        # for later t2 != t1 if filter condition holds for t1 and t2
                        prev_filter_conds.extend([Not(filter_cond.NULL), filter_cond.VALUE])
                premise = simplify(premise, operator=Or)
                count_formulas.append(If(premise, Z3_0, Z3_1))
        return FExpressionTuple(
            NULL=Z3_FALSE,
            VALUE=Sum(*count_formulas),
        )
