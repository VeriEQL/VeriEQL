# -*- coding:utf-8 -*-

from z3 import (
    BoolRef,
    ArithRef,
)

from constants import (
    If,
    Z3_FALSE,
    IntVal,
    Z3_1,
    Z3_0,
)
from errors import SyntaxError
from formulas import register_formula
from formulas.columns.attribute import FAttribute
from formulas.columns.base_column import FBaseColumn
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.digits import FDigits
from formulas.expressions.expression import FExpression
from formulas.expressions.expression_tuple import FExpressionTuple
from utils import __pos_hash__

CONSTANT_TYPE = int | float | ArithRef


@register_formula('aggregation')
class FAggregation(FBaseColumn):
    def __init__(self,
                 scope,
                 function: str,
                 expression: FBaseExpression,
                 distinct=False,
                 _uuid: int = None,
                 **kwargs,
                 ):
        self.scope = scope
        self.KEY = str.upper(function)
        if isinstance(expression, str) and expression == '*':
            self.EXPR = 'ALL'
        elif isinstance(expression, FDigits):
            self.EXPR = expression.value
        elif expression is None:
            # empty table
            self.EXPR = expression
        else:
            self.EXPR = expression
        self.DISTINCT = distinct
        if self.__class__.__name__ == 'FAggCount' and not distinct and isinstance(expression, list):
            raise SyntaxError("Only COUNT(DISTINCT EXPR+) is allowed.")
        self.multi_exprs = isinstance(expression, list)
        self.filter_cond = kwargs.get('filter_cond', None)
        if self.filter_cond is not None:
            self.filter_cond = scope.visitor.visit(self.filter_cond)
        super(FAggregation, self).__init__(scope.DELETED_FUNCTION, _uuid)
        self.require_tuples = True

    def _safe_value(self, formulas):
        if isinstance(formulas, BoolRef):
            formulas = If(formulas, Z3_1, Z3_0)
        if isinstance(formulas, int):
            formulas = IntVal(str(formulas))
        return formulas

    def __uuid__(self):
        return __pos_hash__(self.__str__())

    def __eq__(self, other):
        return __pos_hash__(self) == __pos_hash__(other)

    def __str__(self):
        if self.DISTINCT:
            return f'{self.KEY}_DISTINCT_{self.EXPR}'
        else:
            return f'{self.KEY}_{self.EXPR}'

    def __hash__(self):
        return self._uuid

    def __len__(self):
        return len(self.EXPR) if isinstance(self.EXPR, list) else 1

    def __call__(self, *args, **kwargs):
        # applicable for SUM/MAX/MIN/AVG/BOOL_OP/STD
        if isinstance(self.EXPR, CONSTANT_TYPE):
            # AGG(1)/AGG('literal')
            return FExpressionTuple(NULL=Z3_FALSE, VALUE=self.EXPR)
        else:
            # AGG(AGE - 1)/AGG(AGE)
            return self.scope.visitor.visit(self.EXPR)(*args, **kwargs)

    def update_alias(self, scope, alias_prefix, alias_name):
        """
        transform a `FAggregation` into a `FAttribute`,
        declare a new attribute and assign FAggregation info into it
        """
        if isinstance(self.EXPR, FAttribute):
            # Agg(age)
            if self._uuid in scope.attributes:
                attribute = scope.attributes[self._uuid]
                attribute.value = alias_name
            else:
                attribute = scope.declare_attribute(alias_prefix, alias_name, self._uuid)
            attribute.EXPR = self
        elif isinstance(self.EXPR, FExpression):
            attribute = scope.declare_attribute(alias_prefix, alias_name, self._uuid)
            attribute.EXPR = self
            # self.alias_update(self, attribute)
        else:
            attribute = scope.declare_attribute(alias_prefix, alias_name, self._uuid)
            attribute.EXPR = self
        attribute.uninterpreted_func = self.uninterpreted_func
        attribute.require_tuples = self.require_tuples
        return attribute
