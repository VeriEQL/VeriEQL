# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.tables.base_table import FBaseTable


def _offset(
        scope,
        table: FBaseTable,
        offset: int,
):
    new_table = []
    for tuple in table[offset:]:
        new_table.append(tuple)
    return new_table


@register_formula('offset_table')
class FOffsetTable(FBaseTable):
    def __init__(self,
                 scope,
                 table: FBaseTable,
                 offset: int,
                 ):
        tuples = _offset(scope, table, offset=offset)
        name = f"__{table.name}_OFFSET_{offset}__"
        super(FOffsetTable, self).__init__(tuples, name)
        scope.register_database(name, self)
        self.fathers = table.fathers
        self.root = table.root
