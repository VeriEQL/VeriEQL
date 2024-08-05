# -*- coding: utf-8 -*-

from typing import Sequence

from formulas import register_formula
from formulas.tables.base_table import FBaseTable
from formulas.tuples.projection_tuple import FProjectionTuple


def _intersect_all(
        scope,
        tables: Sequence[FBaseTable],
):
    new_table = []
    for tuple in tables[0]:
        condition = [tuple.attributes, tuple.attributes]
        curr_tuple = FProjectionTuple(tuple, condition, name=scope._get_new_tuple_name())
        scope.register_tuple(curr_tuple.name, curr_tuple)
        curr_tuple.SORT = scope._declare_tuple_sort(curr_tuple.name)
        new_table.append(curr_tuple)
    return new_table


@register_formula('intersect_all')
class FIntersectAllTable(FBaseTable):
    def __init__(self,
                 scope,
                 tables: Sequence[FBaseTable],
                 name: str = None,
                 ):
        # swap tables on their size to reduce future tuple sorts
        if len(tables[0]) > len(tables[1]):
            tables = tables[::-1]
        table = _intersect_all(scope, tables)
        name = name or '_IntersectAll_'.join(t.name for t in tables)
        super(FIntersectAllTable, self).__init__(table, name)
        scope.register_database(name, self)
        self.fathers = tables
        self.root = [t.root for t in tables]
