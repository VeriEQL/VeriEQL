# -*- coding: utf-8 -*-

import itertools
from typing import (
    Sequence,
)

from formulas import register_formula
from formulas.expressions import PredicateType
from formulas.tuples.base_tuple import FBaseTuple
from formulas.tuples.tuple import FTuple


@register_formula('outer_join_tuple')
class FOuterJoinTuple(FTuple):
    def __init__(self,
                 *tuples: Sequence[FBaseTuple | FTuple],
                 condition: PredicateType = None,
                 name: str = None,
                 ):
        super(FOuterJoinTuple, self).__init__(tuples, condition, name)
        self.attributes = self._attributes()

    def __getitem__(self, index):
        return self.tuples[index]

    def __str__(self):
        out = f'{self.name} := OuterJoin({", ".join(self.fathers)}'
        if self.condition is not None:
            out += f', cond=({self.condition})'
        if self._mutex is not None:
            out += f', tmux={list(self._mutex)}'
        return out + ')'

    def _attributes(self):
        attributes = list(itertools.chain(*[t.attributes for t in self.tuples]))
        return attributes

    def reverse_attributes(self):
        self.attributes = self.attributes[::-1]
