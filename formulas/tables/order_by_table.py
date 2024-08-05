# -*- coding: utf-8 -*-

from typing import Sequence

from formulas import register_formula
from formulas.tables.base_table import FBaseTable
from formulas.tuples.orderby_tuple import FOrderByTuple


def _orderby(
        scope,
        table: FBaseTable,
        keys: Sequence[str],
        ascending_flags: Sequence[bool] = None,
):
    new_table = []
    for idx, tuple in enumerate(table):
        curr_tuple = FOrderByTuple(tuple, keys, ascending_flags, name=scope._get_new_tuple_name(), )
        scope.register_tuple(curr_tuple.name, curr_tuple)
        curr_tuple.SORT = scope._declare_tuple_sort(curr_tuple.name)
        new_table.append(curr_tuple)
    return new_table


@register_formula('orderby_table')
class FOrderByTable(FBaseTable):
    def __init__(self,
                 scope,
                 table: FBaseTable,
                 keys: Sequence[str],
                 ascending_flags: Sequence[bool] = None,
                 name: str = None,
                 ):
        self.keys = keys
        self.ascending_flags = ascending_flags or [True] * len(keys)
        tuples = _orderby(scope, table, keys, ascending_flags)
        if name is None:
            name = scope._get_new_databases_name()
        super(FOrderByTable, self).__init__(tuples, name)
        scope.register_database(name, self)
        self.fathers = [table]
        self.root = table.root or table.name
        self._attributes = self[0].attributes

    @property
    def attributes(self):
        return self._attributes

    def set_attributes(self, attributes: Sequence):
        self._attributes = attributes
