# -*- coding:utf-8 -*-

from typing import Sequence

from formulas import register_formula
from formulas.tables.base_table import FBaseTable
from formulas.tuples.distinct_tuple import FDistinctTuple


def _distinct(
        scope,
        table: FBaseTable,
        condition: Sequence[str],
):
    new_table = []
    for idx, tuple in enumerate(table):
        curr_tuple = FDistinctTuple(tuple, condition, name=scope._get_new_tuple_name(), )
        scope.register_tuple(curr_tuple.name, curr_tuple)
        curr_tuple.SORT = scope._declare_tuple_sort(curr_tuple.name)
        new_table.append(curr_tuple)
    return new_table


@register_formula('distinct_table')
class FDistinctTable(FBaseTable):
    def __init__(self,
                 scope,
                 table: FBaseTable,
                 condition: Sequence[str],
                 name: str = None,
                 ):
        tuples = _distinct(scope, table, condition)
        if name is None:
            name = scope._get_new_databases_name()
        super(FDistinctTable, self).__init__(tuples, name)
        scope.register_database(name, self)
        self.fathers = [table]
        self.root = table.root or table.name

    @property
    def condition(self):
        return self[0].condition
