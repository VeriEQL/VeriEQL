# -*- coding:utf-8 -*-

from formulas import register_formula
from formulas.expressions import (
    PredicateType,
)
from formulas.tables.base_table import FBaseTable
from formulas.tables.join_tables.cross_join_table import FCrossJoinTable
from formulas.tables.join_tables.inner_join_table import FInnerJoinTable
from formulas.tables.join_tables.outer_join_tables import FOuterJoinBaseTable
from formulas.tuples.filter_tuple import FFilterTuple


def _filter(
        scope,
        table: FBaseTable,
        condition: PredicateType,
):
    new_table = []
    for idx, prev_tuple in enumerate(table):
        if isinstance(condition, list):
            tuple = FFilterTuple(prev_tuple, condition[idx], name=scope._get_new_tuple_name())
        else:
            tuple = FFilterTuple(prev_tuple, condition, name=scope._get_new_tuple_name())
        scope.register_tuple(tuple.name, tuple)
        tuple.SORT = scope._declare_tuple_sort(tuple.name)
        new_table.append(tuple)

    if isinstance(table, FOuterJoinBaseTable):
        for mutex_indices in table._children:
            mutex_ids, null_idx = mutex_indices[:-1], mutex_indices[-1]
            new_table[null_idx].add_mutex([new_table[idx].SORT for idx in mutex_ids])
    return new_table


@register_formula('filter_table')
class FFilterTable(FBaseTable):
    def __init__(self,
                 scope,
                 table: FBaseTable,
                 condition: PredicateType | list,
                 is_correlated_subquery: bool = False,
                 name: str = None,
                 ):
        tuples = _filter(scope, table, condition)
        if name is None:
            name = scope._get_new_databases_name()
        super(FFilterTable, self).__init__(tuples, name, is_correlated_subquery)
        scope.register_database(name, self)
        self.fathers = [table]
        self.root = table.root or table.name
        if isinstance(table, FInnerJoinTable | FOuterJoinBaseTable | FCrossJoinTable):
            self.__class__.__name__ = f"F{table.__class__.__name__[1:-5]}FilterTable"

    @property
    def condition(self):
        return self[0].attributes

    @property
    def attributes(self):
        return self.fathers[0].attributes
