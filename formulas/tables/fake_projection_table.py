# -*- coding:utf-8 -*-

from typing import Sequence

from formulas import register_formula
from formulas.tables.base_table import FBaseTable
from formulas.tuples.fake_projection_tuple import FFakeProjectionTuple


def _projection(scope, table, condition):
    tuples = []
    for tuple in table.tuples:
        new_tuple = FFakeProjectionTuple(tuple, condition=condition, name=scope._get_new_tuple_name())
        scope.register_tuple_sort(new_tuple.name, new_tuple.name)
        new_tuple.SORT = tuple.SORT
        tuples.append(new_tuple)
    return tuples


@register_formula('fake_projection_table')
class FFakeProjectionTable(FBaseTable):
    def __init__(self,
                 scope,
                 table: FBaseTable,
                 condition: Sequence[str],
                 is_correlated_subquery: bool = False,
                 name: str = None,
                 ):
        name = name or scope._get_new_databases_name()
        tuples = _projection(scope, table, condition)
        super(FFakeProjectionTable, self).__init__(tuples, name, is_correlated_subquery)
        scope.register_database(name, self)
        self.fathers = [table]
        self.root = table.root or table.name

    def __str__(self):
        context = '\n\t'.join([
            tuple.__str__() for tuple in self.tuples
        ])
        context = f'{self.__class__.__name__}({self.name}): [\n\t{context}\n]'
        return context

    @property
    def condition(self):
        return self[0].condition

    @property
    def attributes(self):
        return self[0].condition[-1]
