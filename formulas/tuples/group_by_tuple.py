# -*- coding: utf-8 -*-

from typing import (
    Sequence,
)

from formulas import register_formula
from formulas.tuples.base_tuple import FBaseTuple
from formulas.tuples.tuple import FTuple


@register_formula('group_reduce_tuple')
class FGroupByTuple(FTuple):
    def __init__(self,
                 tuples: Sequence[FBaseTuple | FTuple],
                 keys: Sequence,
                 # agg_attributes: Sequence,
                 name: str = None,
                 ):
        self.keys = keys
        # self.agg_attributes = agg_attributes
        # for aggregation functions, it might map a previous table into a tuple.
        super(FGroupByTuple, self).__init__(tuples, None, name)

    def __str__(self) -> str:
        return f'{self.name} := GroupReduce({self.fathers})'

    @property
    def attributes(self):
        return self.keys

    @property
    def out_attributes(self):
        # for agg
        return self.tuples[0].attributes
