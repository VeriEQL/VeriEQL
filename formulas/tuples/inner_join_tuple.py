# -*- coding: utf-8 -*-

import itertools
from typing import (
    Sequence,
)

from formulas import register_formula
from formulas.expressions import PredicateType
from formulas.tuples.base_tuple import FBaseTuple
from formulas.tuples.tuple import FTuple


@register_formula('inner_join_tuple')
class FInnerJoinTuple(FTuple):
    def __init__(self,
                 *tuples: Sequence[FBaseTuple | FTuple],
                 condition: PredicateType,
                 name: str = None,
                 ):
        super(FInnerJoinTuple, self).__init__(tuples, condition, name)
        self.attributes = self._attributes()

    def __getitem__(self, index):
        return self.tuples[index]

    def __str__(self):
        return f'{self.name} := InnerJoin({", ".join(self.fathers)}, {self.condition})'

    def _attributes(self):
        attributes = list(itertools.chain(*[t.attributes for t in self.tuples]))
        # return deepcopy(attributes)
        return attributes
