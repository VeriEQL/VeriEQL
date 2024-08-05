# -*- coding: utf-8 -*-

from typing import Sequence

from formulas import register_formula
from formulas.tables.base_table import FBaseTable
from formulas.tuples.projection_tuple import FProjectionTuple


def _except_all(
        scope,
        table: FBaseTable,
):
    new_table = []
    for tuple in table:
        condition = [tuple.attributes, tuple.attributes]
        curr_tuple = FProjectionTuple(tuple, condition, name=scope._get_new_tuple_name())
        scope.register_tuple(curr_tuple.name, curr_tuple)
        curr_tuple.SORT = scope._declare_tuple_sort(curr_tuple.name)
        new_table.append(curr_tuple)
    return new_table


@register_formula('except_all')
class FExceptAllTable(FBaseTable):
    def __init__(self,
                 scope,
                 tables: Sequence[FBaseTable],
                 name: str = None,
                 ):
        table = _except_all(scope, tables[0])
        name = name or '_ExceptAll_'.join(t.name for t in tables)
        super(FExceptAllTable, self).__init__(table, name)
        scope.register_database(name, self)
        self.fathers = tables
        self.root = [t.root for t in tables]
