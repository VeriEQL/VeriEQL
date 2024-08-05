# -*- coding:utf-8 -*-

from formulas import register_formula
from formulas.base_formula import BaseFormula
from formulas.tuples.tuple import FTuple


@register_formula('limit_tuple')
class FLimitTuple(FTuple):
    def __init__(self,
                 tuple: BaseFormula | FTuple,
                 name: str = None,
                 ):
        # set attribute alias in visiting
        super(FLimitTuple, self).__init__(tuple, None, name)

    def __str__(self) -> str:
        return f'{self.name} := Limit({self.fathers})'

    @property
    def attributes(self):
        return self.tuples[0].attributes
