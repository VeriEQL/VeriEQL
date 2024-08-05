# -*- coding: utf-8 -*-

import operator

from constants import Z3_FALSE
from formulas import register_formula
from formulas.expressions.symbol import FSymbol


@register_formula('digits')
class FDigits(FSymbol):
    def __init__(self, value):
        if isinstance(value, FSymbol):
            value = value.value
        super(FDigits, self).__init__(value)

    def __eq__(self, other):
        if isinstance(other, FSymbol):
            return self.value == other.value
        else:
            return self.value == other

    def _f(self, operator, other):
        if isinstance(other, int | float | bool):
            return operator(self.value, other)
        elif isinstance(other, FSymbol | FDigits):
            return operator(self.value, other.value)
        else:
            raise NotImplementedError(f"{operator}({self}, {other})")

    def __add__(self, other):
        return self._f(operator.__add__, other)

    def __sub__(self, other):
        return self._f(operator.__sub__, other)

    def __mul__(self, other):
        return self._f(operator.__mul__, other)

    def __truediv__(self, other):
        return self._f(operator.__truediv__, other)

    def __floordiv__(self, other):
        return self._f(operator.__floordiv__, other)

    def __and__(self, other):
        return self._f(operator.__and__, other)

    def __or__(self, other):
        return self._f(operator.__or__, other)

    def __neg__(self):
        return self.value == 0

    def __mod__(self, other):
        return self._f(operator.__mod__, other)

    def __gt__(self, other):
        return self._f(operator.__gt__, other)

    def __ge__(self, other):
        return self._f(operator.__ge__, other)

    def __lt__(self, other):
        return self._f(operator.__lt__, other)

    def __le__(self, other):
        return self._f(operator.__le__, other)

    def __ne__(self, other):
        return self._f(operator.__ne__, other)

    def __str__(self):
        return f'Digits_{self.value}'

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return 1

    def __getitem__(self, index):
        # assert index == 0
        return self.value

    def update_alias(self, scope, alias_prefix, alias_name):
        from visitors.interm_function import IntermFunc
        attribute = scope.declare_attribute(alias_prefix, alias_name)
        attribute.EXPR = self.value if isinstance(self, FDigits) else self
        if str.startswith(alias_name, "Digits_"):
            attribute.NULL = IntermFunc(
                z3_function=lambda *args, **kwargs: Z3_FALSE,
                description="False",
            )
            attribute.EXPR_CALL = IntermFunc(
                z3_function=lambda *args, **kwargs: self.value,
                description=str(self.value),
            )
        else:
            attribute.EXPR_CALL = IntermFunc(
                z3_function=lambda x, **kwargs: scope.visitor.visit(self),
                description=str(self),
            )
        return attribute
