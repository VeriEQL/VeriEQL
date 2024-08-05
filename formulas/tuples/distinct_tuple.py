# -*- coding:utf-8 -*-

from typing import (
    Sequence,
)

from formulas import register_formula
from formulas.base_formula import BaseFormula
from formulas.tuples.tuple import FTuple


@register_formula('distinct_tuple')
class FDistinctTuple(FTuple):
    def __init__(self,
                 tuples: Sequence[BaseFormula | FTuple],
                 condition: Sequence,
                 name: str = None,
                 ):
        super(FDistinctTuple, self).__init__(tuples, condition, name)
        self.attributes = [attr for attr in self.condition[-1] if attr is not None]

    def __str__(self):
        return f'{self.name} := DistinctProjection({self.fathers}, Cond={self.attributes})'
