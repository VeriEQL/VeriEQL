# -*- coding:utf-8 -*-

from typing import (
    Sequence,
)

from formulas import register_formula
from formulas.base_formula import BaseFormula
from formulas.tuples.tuple import FTuple


@register_formula('alias_tuple')
class FAliasTuple(FTuple):
    def __init__(self,
                 tuple: BaseFormula | FTuple,
                 condition: Sequence = None,
                 name: str = None,
                 ):
        # set attribute alias in visiting
        super(FAliasTuple, self).__init__(tuple, condition, name)
        self.attributes = self._attributes()

    def __str__(self):
        if len(self.attributes) == 0:
            return f'{self.name} := Alias({self.fathers}, Cond=[])'
        else:
            return f'{self.name} := Alias({self.fathers}, Cond=({self.condition[0][0]}->{self.condition[1][0]}, ...)'

    def _attributes(self):
        # return deepcopy(self.condition[-1])
        return self.condition[-1]
