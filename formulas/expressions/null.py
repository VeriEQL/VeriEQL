# -*- coding: utf-8 -*-

from constants import Z3_TRUE
from formulas import register_formula
from formulas.expressions.symbol import FSymbol
from utils import uuid_hash


@register_formula('null')
class FNull(FSymbol):
    def __init__(self):
        super(FNull, self).__init__('NULL')

    def __eq__(self, other):
        if isinstance(other, FSymbol):
            return self.value == other.value
        else:
            return self.value == other

    def update_alias(self, scope, alias_prefix, alias_name):
        from visitors.interm_function import IntermFunc
        attribute = scope.declare_attribute(alias_prefix, alias_name, _uuid=uuid_hash())
        attribute.NULL = IntermFunc(
            z3_function=lambda *args, **kwargs: Z3_TRUE,
            description='True',
        )
        attribute.EXPR = self
        attribute.EXPR_CALL = IntermFunc(
            z3_function=lambda x, **kwargs: scope.visitor.visit(self),
            description=str(self),
        )
        return attribute

    def __add__(self, other):
        return self

    def __sub__(self, other):
        return self

    def __mul__(self, other):
        return self

    def __divmod__(self, other):
        return self
