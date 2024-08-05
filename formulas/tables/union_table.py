# -*- coding: utf-8 -*-

from typing import Sequence

from formulas import register_formula
from formulas.tables.base_table import FBaseTable
from formulas.tables.distinct_table import _distinct
from formulas.tables.union_all_table import FUnionAllTable


@register_formula('union')
class FUnionTable(FBaseTable):
    def __init__(self,
                 scope,
                 tables: Sequence[FBaseTable],
                 name: str = None,
                 ):
        father_table = FUnionAllTable(scope, tables)
        table = _distinct(
            scope,
            table=father_table,
            condition=[None, father_table.attributes],
        )
        name = name or '_Union_'.join(t.name for t in tables)
        super(FUnionTable, self).__init__(table, name)
        scope.register_database(name, self)
        self.fathers = [father_table]
        self.root = [t.root for t in tables]
