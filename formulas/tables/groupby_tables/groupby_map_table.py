# -*- coding: utf-8 -*-

from typing import (
    Sequence,
    Callable,
)

from formulas import register_formula
from formulas.expressions import PredicateType
from formulas.tables.base_table import FBaseTable
from formulas.tuples.group_by_tuple import FGroupByTuple


def _reduce(
        scope,
        table: FBaseTable,
        keys: Sequence,
):
    new_table = []
    for idx in range(len(table)):
        row_tuples = table[idx:]
        curr_tuple = FGroupByTuple(row_tuples, keys[idx], name=scope._get_new_tuple_name())
        scope.register_tuple(curr_tuple.name, curr_tuple)
        curr_tuple.SORT = scope._declare_tuple_sort(curr_tuple.name)
        new_table.append(curr_tuple)
    return new_table


@register_formula('group_by_map_table')
class FGroupByMapTable(FBaseTable):
    def __init__(self,
                 scope,
                 table: FBaseTable,
                 keys: Sequence,
                 group_function: Callable,
                 having_clause: PredicateType = None,
                 attributes: Sequence = None,
                 out_attributes: Sequence = None,
                 name: str = None,
                 ):
        """
        GROUP BY is quite complicated, we better incorporate FGroupReduce, filter and projection together.
        """
        self.group_function = group_function
        tuples = _reduce(scope, table, keys)
        self.keys = keys
        self.having_clause = having_clause
        self._attributes = attributes
        self.out_attributes = out_attributes
        name = name or scope._get_new_databases_name()
        super(FGroupByMapTable, self).__init__(tuples, name)
        scope.register_database(name, self)
        self.fathers = [table]
        self.root = table.root or table.name

    def __str__(self):
        out = f'{self.__class__.__name__}({self.name}): {self.attributes}'
        if self.keys is not None:
            out += f' GroupBy: {self.keys}'
        if self.having_clause is not None:
            out += f' Having: {self.having_clause}'
        return out

    def __repr__(self):
        return self.__str__()

    @property
    def attributes(self):
        return self._attributes

    def update_having_clause(self, having_clause):
        self.having_clause = having_clause
