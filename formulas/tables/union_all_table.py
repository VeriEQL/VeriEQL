# -*- coding: utf-8 -*-

import itertools
from typing import Sequence

from formulas import register_formula
from formulas.tables.alias_table import FAliasTable
from formulas.tables.base_table import FBaseTable


def _union_all(
        scope,
        tables: Sequence,
):
    first_table_attributes = tables[0].attributes
    following_table_attributes = [table.attributes for table in tables[1:]]
    for idx, table in enumerate(tables[1:]):
        if any(
                type(lhs_attr) != type(rhs_attr) or lhs_attr != rhs_attr
                for lhs_attr, rhs_attr in zip(first_table_attributes, following_table_attributes[idx])
        ):
            condition = [following_table_attributes[idx], first_table_attributes]
            alias_table = FAliasTable(scope, tables[idx + 1], condition, alias_attributes=True)
            tables[idx + 1] = alias_table

    tuples = list(itertools.chain(*[t.tuples for t in tables]))
    return tuples, tables


@register_formula('union_all')
class FUnionAllTable(FBaseTable):
    def __init__(self,
                 scope,
                 tables: Sequence[FBaseTable],
                 name: str = None,
                 ):
        name = name or '_UnionAll_'.join(t.name for t in tables)
        tuples, tables = _union_all(scope, tables)
        super(FUnionAllTable, self).__init__(tuples, name)
        scope.register_database(name, self)
        self.fathers = tables
        self.root = [t.root for t in tables]
