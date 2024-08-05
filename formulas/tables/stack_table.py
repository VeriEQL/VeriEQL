# -*- coding:utf-8 -*-

from typing import Sequence

from formulas import register_formula
from formulas.tables.base_table import FBaseTable


@register_formula('stack_table')
class FStackTable(FBaseTable):
    def __init__(self,
                 scope,
                 *tables: Sequence[FBaseTable],
                 name: str = None,
                 ):
        name = name or scope._get_new_databases_name()
        tuples = [t for table in tables for t in table]
        super(FStackTable, self).__init__(tuples, name)
        scope.register_database(name, self)
        self.fathers = list(tables)
        self.root = tables[0].root

    def __getitem__(self, index):
        return self.fathers[index]
