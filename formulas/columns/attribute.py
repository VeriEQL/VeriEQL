# -*- coding:utf-8 -*-

from copy import copy

from z3 import ArithRef

from constants import (
    NumericType,
    Z3_NULL_VALUE,
    Z3_FALSE,
    Z3_TRUE,
)
from formulas import register_formula
from formulas.columns.base_column import FBaseColumn
from formulas.expressions.expression_tuple import FExpressionTuple
from formulas.expressions.null import FNull


@register_formula('attribute')
class FAttribute(FBaseColumn):
    """
    1) pure attribute
        NULL: NULL(?, StringSort)
        VALUE: attribute(?)
        expression: None
    2) alias attribute for expression
        NULL: NULL(?, StringSort)
        VALUE: attribute(?)
        EXPRESSION: expr | op(expr+)
        EXPR_NULL/EXPR_VALUE: they are only obtained from the `__call__` function
    """

    # why slot? deepcopy take lots of time and memory
    __slots__ = [
        # name
        'prefix', 'name',
        # z3
        'VALUE', 'NULL', '__STRING_SORT__',
        # alias expression
        'EXPR', 'EXPR_CALL', 'require_tuples', '_sugar_name', '_sugar_full_name'
    ]

    def __init__(self,
                 scope,
                 literal: str,
                 prefix: str,
                 _uuid: int = None,
                 ):
        self.prefix = prefix
        self.name = literal
        super(FAttribute, self).__init__(scope.DELETED_FUNCTION, uuid=_uuid)

        self.__STRING_SORT__ = None  # StringSort
        self.EXPR = None  # store its real expression
        self.EXPR_CALL = None  # store its visited expression
        self.require_tuples = False  # only True for alias expression
        # when group-by use sugar index, having and order-by can use its orginial name or alias name
        self._sugar_full_name = self._sugar_name = None

    def detach(self):
        # deepcopy will copy `self.EXPR`
        attribute = copy(self)
        attribute.EXPR = None
        attribute.require_tuples = False
        attribute._sugar_full_name = attribute._sugar_name = None
        attribute.uninterpreted_func = None
        return attribute

    def update_alias(self, scope, alias_prefix, alias_name):
        attr = self.detach()
        attr.prefix = alias_prefix
        attr.name = alias_name
        attr._sugar_full_name = self.__str__()
        attr._sugar_name = self.name
        attr.uninterpreted_func = self.uninterpreted_func
        return attr

    def __str__(self):
        return f'{self.prefix}__{self.name}'

    def __eq__(self, other):
        from visitors.interm_function import IntermFunc
        if isinstance(other, FAttribute):
            return hash(self) == hash(other) and self.VALUE == other.VALUE
        elif isinstance(other, IntermFunc):
            return self in other.attributes
        elif isinstance(other, str):
            return other == self.name or self.__str__() == other or \
                self._sugar_name is not None and self._sugar_name == other or \
                self._sugar_full_name is not None and self._sugar_full_name == other
        else:
            return False

    def __hash__(self):
        return self._uuid

    def __call__(self, *args, **kwargs):
        return FExpressionTuple(self.NULL(*args, **kwargs), self.VALUE(*args, **kwargs))

    def __expr__(self, src_tuples, **kwargs):
        from formulas.columns.aggregations import AggregationType
        from formulas.expressions.expression import FExpression
        from formulas.expressions.predicates.case_predicate import FCasePredicate
        from formulas.expressions.predicates.last_value_predicate import FLastValuePredicate
        from formulas.expressions.digits import FDigits

        if isinstance(self.EXPR, FLastValuePredicate):
            pass
        elif not self.require_tuples and isinstance(src_tuples, list):
            src_tuples = src_tuples[0]

        if isinstance(self.EXPR, AggregationType):  # Aggregation
            return self.EXPR.__expr__(src_tuples, **kwargs)
        elif isinstance(self.EXPR, FCasePredicate | FExpression):
            return self.EXPR_CALL(src_tuples, **kwargs)
        elif isinstance(self.EXPR, FNull):
            return FExpressionTuple(Z3_TRUE, Z3_NULL_VALUE)
        elif isinstance(self.EXPR, FDigits):
            return FExpressionTuple(Z3_FALSE, self.EXPR_CALL(None))
        elif isinstance(self.EXPR, NumericType | ArithRef):
            return FExpressionTuple(Z3_FALSE, self.EXPR)
        elif self.EXPR is None:  # FSymbol
            return FExpressionTuple(Z3_FALSE, self.VALUE(None))
        else:
            raise NotImplementedError(self.EXPR)
