# -*- coding:utf-8 -*-

from copy import deepcopy
from typing import Sequence

from formulas import register_formula
from formulas.base_formula import BaseFormula


@register_formula('base_table')
class FBaseTable(BaseFormula):
    def __init__(self,
                 tuples: Sequence,
                 name: str,
                 is_correlated_subquery: bool = False,
                 ):
        self.tuples = tuples or []
        self.name = name
        self.fathers = None
        self.root = self.name
        self.is_correlated_subquery = is_correlated_subquery

    def __getitem__(self, idx):
        return self.tuples[idx]

    def __len__(self):
        return len(self.tuples)

    def __iter__(self):
        for idx in range(len(self)):
            yield self[idx]

    def __eq__(self, other):
        return (self.name == other.name) and (self.tuples == other.tuples)

    def __str__(self):
        if len(self.tuples) == 0:
            context = f'{self.__class__.__name__}({self.name}): []'
        else:
            tuples = [
                tuple.__str__() for tuple in self.tuples
            ]
            context = '\n\t'.join(tuples)
            context = f'{self.__class__.__name__}({self.name}): [\n\t{context}\n]'
        return context

    def __repr__(self):
        return self.__str__()

    @property
    def attributes(self):
        return self[0].attributes

    def add_attributes(self, attributes: Sequence):
        for tuple in self:
            tuple.add_attributes(attributes)

    def clear_alias_info(self):
        for attr in self.attributes:
            attr._sugar_full_name = attr._sugar_name = None

    def detach(self, scope, postfix):
        out = deepcopy(self)
        out.name = f"{out.name}_{postfix}"
        for idx, tuple in enumerate(out.tuples):
            tuple.name = f"{tuple.name}_{postfix}"
            tuple.SORT = scope._declare_tuple_sort(tuple.name)
        return out
