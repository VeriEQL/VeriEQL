# -*- coding: utf-8 -*-

from typing import Sequence

import utils
from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.operator import FOperator


@register_formula('expression')
class FExpression(FBaseExpression):
    """
    Expression := Operator Expression*, e.g., (+ (1, 2))
    """

    def __init__(
            self,
            operator: FOperator,
            operands: Sequence[FBaseExpression],
    ):
        self.operator = operator
        self.operands = operands
        super().__init__()
        self.require_tuples = any(getattr(opd, 'require_tuples', False) for opd in self.operands)

    def __len__(self):
        return len(self.operands)

    def __str__(self):
        from formulas.tables.base_table import FBaseTable
        return f'{self.operator}_' + \
            '_'.join([operand.__class__.__name__ if isinstance(operand, FBaseTable) else str(operand).replace('-', '_') \
                      for operand in self.operands])

    def __eq__(self, other):
        if isinstance(other, FExpression):
            return (self.operator == other.operator) and all(
                type(operand1) == type(operand2) and operand1 == operand2
                for operand1, operand2 in zip(self.operands, other.operands)
            )
        else:
            return False

    def __getitem__(self, index):
        return self.operands[index]

    def __setitem__(self, key, value):
        self.operands[key] = value

    def __hash__(self):
        return utils.__pos_hash__(self.__str__())

    def update_alias(self, scope, alias_prefix, alias_name):
        from visitors.interm_function import IntermFunc
        attribute = scope.declare_attribute(alias_prefix, alias_name, _uuid=utils.uuid_hash())
        attribute.EXPR = self
        attribute.EXPR_CALL = IntermFunc(scope.visitor.visit(self), str(self))
        if self.uninterpreted_func is not None:
            attribute.uninterpreted_func = self.uninterpreted_func
            self.uninterpreted_func = None
        attribute.require_tuples = self.require_tuples
        return attribute

    def __call__(self, *args, **kwargs):
        raise NotImplementedError

    def __expr__(self, *args, **kwargs):
        raise NotImplementedError
