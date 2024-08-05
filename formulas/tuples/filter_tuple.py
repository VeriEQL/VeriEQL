# -*- coding:utf-8 -*-


from formulas import register_formula
from formulas.expressions import PredicateType
from formulas.tuples.base_tuple import FBaseTuple
from formulas.tuples.tuple import FTuple


@register_formula('filter_tuple')
class FFilterTuple(FTuple):
    def __init__(self,
                 tuple: FBaseTuple | FTuple,
                 condition: PredicateType,
                 name: str = None,
                 ):
        super(FFilterTuple, self).__init__(tuple, condition, name)

    def __str__(self) -> str:
        return f'{self.name} := Filter({self.fathers}, Cond=({self.condition}))'

    @property
    def attributes(self):
        return self.tuples[0].attributes
