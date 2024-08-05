# -*- coding:utf-8 -*-

from typing import Sequence

from formulas import register_formula
from formulas.expressions.predicates import PredicateType
from formulas.tables.base_table import FBaseTable
from formulas.tables.join_tables._utils import (
    _analyze_using,
    _analyze_default,
)
from formulas.tables.join_tables._utils import alias_check
from formulas.tables.join_tables.join_base_table import FJoinBaseTable
from formulas.tuples.natural_join_tuple import FNaturalJoinTuple


def _natural_join(
        scope,
        tables: Sequence[FBaseTable],
        name: str,
):
    tables = alias_check(scope, tables, name)

    curr_table = []
    # cannot change the order of tuple_pairs
    tuple_pairs = [[lhs_tuple, rhs_tuple] for rhs_tuple in tables[1] for lhs_tuple in tables[0]]
    for tuple_list in tuple_pairs:
        # update condition later
        tuple = FNaturalJoinTuple(*tuple_list, name=scope._get_new_tuple_name())
        scope.register_tuple(tuple.name, tuple)
        tuple.SORT = scope._declare_tuple_sort(tuple.name)
        curr_table.append(tuple)
    return tables, curr_table


@register_formula('natural_join')
class FNaturalJoinTable(FJoinBaseTable):
    def __init__(self,
                 scope,
                 tables: Sequence[FBaseTable],
                 condition: PredicateType = None,
                 name: str = None,
                 ):
        name = name or '_NaturalJoin_'.join(t.name for t in tables)

        # 1) product
        prev_tables, curr_table = _natural_join(scope, tables, name)

        if condition is None:
            equal_conditions, condition = _analyze_default(*[t.attributes for t in prev_tables])
            self.is_using = False
        else:
            equal_conditions, condition = _analyze_using(condition, curr_table[0].attributes)
            self.is_using = False

        for idx in range(len(curr_table)):
            curr_table[idx].condition = condition

        # NATURAL JOIN does not remove duplicate columns
        corresponding_attributes, remove_attributes = list(zip(*equal_conditions))
        attributes = []
        for attr in curr_table[0].attributes:
            if attr in remove_attributes:
                corr_attr = corresponding_attributes[remove_attributes.index(attr)]
                corr_attr._sugar_full_name = str(attr)
                corr_attr._sugar_name = attr.name
            else:
                attributes.append(attr)
        for tuple in curr_table:
            tuple.attributes = attributes

        super(FNaturalJoinTable, self).__init__(scope, curr_table, name)
        self.fathers = prev_tables
        self.root = [t.root for t in prev_tables]
