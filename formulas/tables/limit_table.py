# -*- coding: utf-8 -*-

from typing import Sequence

from formulas import register_formula
from formulas.tables.base_table import FBaseTable
from formulas.tuples.limit_tuple import FLimitTuple


def _limit(
        scope,
        table: FBaseTable,
        limit_a: int,
        limit_b: int,
        drop_deleted_tuples=False,
):
    new_table = []
    if drop_deleted_tuples:
        for idx, tuple in enumerate(table[limit_a:limit_b]):
            curr_tuple = FLimitTuple(tuple, name=scope._get_new_tuple_name(), )
            scope.register_tuple(curr_tuple.name, curr_tuple)
            curr_tuple.SORT = scope._declare_tuple_sort(curr_tuple.name)
            new_table.append(curr_tuple)
    else:
        for tuple in table[limit_a:limit_b]:
            new_table.append(tuple)
    return new_table


@register_formula('limit_table')
class FLimitTable(FBaseTable):
    def __init__(self,
                 scope,
                 table: FBaseTable,
                 limit_a: int,
                 limit_b: int,
                 drop_deleted_tuples=False,
                 ):
        self.limit_a = limit_a
        self.limit_b = min(len(table), limit_b)
        tuples = _limit(scope, table, limit_a, limit_b, drop_deleted_tuples)
        # Since fetch and offset can also appear in the end of non-orderby query,
        # we need this flag to show that this table requires to sort its deleted tuples at the end of the table.
        # However, this procedure is source-consuming.
        self.drop_deleted_tuples = drop_deleted_tuples
        name = f"__{table.name}_LIMIT_{limit_a}_{limit_b}__"
        super(FLimitTable, self).__init__(tuples, name)
        scope.register_database(name, self)
        self.fathers = [table]
        self.root = table.root
        self._attributes = table.attributes

    @property
    def attributes(self):
        return self._attributes

    def set_attributes(self, attributes: Sequence):
        self._attributes = attributes
