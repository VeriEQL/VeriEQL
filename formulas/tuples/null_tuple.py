# -*- coding:utf-8 -*-

from typing import Sequence

from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.null import FNull
from formulas.tuples._field import FField
from formulas.tuples.base_tuple import FBaseTuple
from formulas.tuples.tuple import FTuple


@register_formula('null_tuple')
class FNullTuple(FTuple):
    def __init__(self,
                 scope,
                 attributes: Sequence[FBaseExpression],
                 name: str = None,
                 ):
        name = name or scope._get_new_tuple_name()
        tuple = FBaseTuple([FField(attr, FNull()) for attr in attributes], name)
        scope.register_tuple(tuple.name, tuple)
        super(FNullTuple, self).__init__(tuple, None, name=name)
        self.SORT = scope._declare_tuple_sort(tuple.name)

    def __str__(self):
        return f'{self.name} := NullTuple({self.attributes})'

    def __repr__(self):
        return self.__str__()

    @property
    def attributes(self):
        return self.tuples[0].attributes
