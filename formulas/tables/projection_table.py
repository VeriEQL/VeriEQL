# -*- coding:utf-8 -*-

from typing import Sequence

from formulas import register_formula
from formulas.tables.base_table import FBaseTable
from formulas.tables.order_by_table import FOrderByTable
from formulas.tuples.projection_pity_tuple import FProjectionPityTuple
from formulas.tuples.projection_tuple import FProjectionTuple


def _projection(
        scope,
        table: FBaseTable,
        condition: Sequence[str],
        name: str,
):
    from formulas.tables.groupby_tables.groupby_table import FGroupByTable

    pity_flag = any([attr.require_tuples for attr in condition[-1]])

    new_table = []
    if (not isinstance(table, FGroupByTable)) and \
            not (isinstance(table, FOrderByTable) and isinstance(table.fathers[0], FGroupByTable)) and \
            pity_flag:
        # if contain any aggregation functions or their alias
        curr_tuple = FProjectionTuple(table.tuples, condition, name=scope._get_new_tuple_name())
        scope.register_tuple(curr_tuple.name, curr_tuple)
        curr_tuple.SORT = scope._declare_tuple_sort(curr_tuple.name)
        new_table.append(curr_tuple)

        # for aggregation operations in empty table
        # e.g., 'SELECT COUNT(*), SUM(EMPNO) FROM EMP WHERE FALSE'
        # 1) for this example, 'SELECT 1, DEPTNO, count(*) FROM EMP WHERE FALSE'
        # we will not raise an error, but output 1, NULL, 0
        # 2) for this example, 'SELECT 1, DEPTNO FROM EMP WHERE FALSE'
        # we will not raise an error, but output an empty table
        # BTW, it does not work for group by
        pity_tuple = FProjectionPityTuple(table.tuples, condition, name=f'pity_tuple_of_{name}')
        scope.register_tuple(pity_tuple.name, pity_tuple)
        pity_tuple.SORT = scope._declare_tuple_sort(pity_tuple.name)
        new_table.append(pity_tuple)
    else:
        for tuple in table:
            curr_tuple = FProjectionTuple(tuple, condition, name=scope._get_new_tuple_name())
            scope.register_tuple(curr_tuple.name, curr_tuple)
            curr_tuple.SORT = scope._declare_tuple_sort(curr_tuple.name)
            new_table.append(curr_tuple)
        pity_flag = False
    return new_table, pity_flag


@register_formula('projection_table')
class FProjectionTable(FBaseTable):
    def __init__(self,
                 scope,
                 table: FBaseTable,
                 condition: Sequence[str],
                 name: str = None,
                 ):
        name = name or scope._get_new_databases_name()
        tuples, self.pity_flag = _projection(scope, table, condition, name)
        super(FProjectionTable, self).__init__(tuples, name)
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
