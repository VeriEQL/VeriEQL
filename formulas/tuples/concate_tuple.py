# -*- coding:utf-8 -*-

import itertools
from typing import (
    Sequence,
)

from formulas import register_formula
from formulas.tuples.base_tuple import FBaseTuple
from formulas.tuples.tuple import FTuple


@register_formula('concate_tuple')
class FConcateTuple(FTuple):
    def __init__(self,
                 *tuples: Sequence[FBaseTuple | FTuple],
                 name: str = None,
                 ):
        super(FConcateTuple, self).__init__(tuples, None, name)
        self.attributes = self._attributes()

    def __getitem__(self, index):
        return self.tuple[index]

    def __str__(self):
        return f'{self.name} := Concate({", ".join(self.fathers)})'

    def _attributes(self):
        attributes = list(itertools.chain(*[t.attributes for t in self.tuples]))
        # return deepcopy(attributes)
        return attributes
