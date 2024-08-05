# -*- coding:utf-8 -*-

from typing import Sequence

from formulas import register_formula
from formulas.tables.base_table import FBaseTable
from formulas.tables.join_tables._utils import alias_check
from formulas.tuples.concate_tuple import FConcateTuple


def _cartesian_product(
        scope,
        tables: Sequence[FBaseTable],
        name: str,
):
    tables = alias_check(scope, tables, name)

    curr_table = []
    # cannot change the order of tuple_pairs
    tuple_pairs = [[lhs_tuple, rhs_tuple] for rhs_tuple in tables[1] for lhs_tuple in tables[0]]
    for tuple_list in tuple_pairs:
        tuple = FConcateTuple(*tuple_list, name=scope._get_new_tuple_name())
        scope.register_tuple(tuple.name, tuple)
        tuple.SORT = scope._declare_tuple_sort(tuple.name)
        curr_table.append(tuple)
    return tables, curr_table


@register_formula('product_table')
class FProductTable(FBaseTable):
    def __init__(self,
                 scope,
                 tables: Sequence[FBaseTable],
                 name: str = None,
                 ):
        name = name or '_CROSS_'.join(t.name for t in tables)
        prev_tables, curr_table = _cartesian_product(scope, tables, name)
        super(FProductTable, self).__init__(curr_table, name)
        scope.register_database(name, self)
        self.fathers = prev_tables
        self.root = [t.root for t in prev_tables]
        self._hidden_attributes = None
