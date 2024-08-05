# -*- coding:utf-8 -*-

from typing import (
    Sequence,
)

from formulas import register_formula
from formulas.tuples.base_tuple import FBaseTuple
from formulas.tuples.tuple import FTuple


@register_formula('fake_projection_tuple')
class FFakeProjectionTuple(FTuple):
    def __init__(self,
                 tuples: Sequence[FBaseTuple | FTuple],
                 condition: Sequence,
                 name: str = None,
                 ):
        # for aggregation functions, it might map a previous table into a tuple.
        super(FFakeProjectionTuple, self).__init__(tuples, condition, name)
        self.attributes = [attr for attr in self.condition[-1] if attr is not None]

    def __str__(self) -> str:
        return f'{self.name} := FakeProjection({self.fathers}, Cond={self.attributes})'
