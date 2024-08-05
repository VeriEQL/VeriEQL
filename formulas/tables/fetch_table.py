# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.tables.base_table import FBaseTable


def _offset(
        scope,
        table: FBaseTable,
        fetch: int,
):
    new_table = []
    for tuple in table[:fetch]:
        new_table.append(tuple)
    return new_table


@register_formula('fetch_table')
class FFetchTable(FBaseTable):
    def __init__(self,
                 scope,
                 table: FBaseTable,
                 fetch: int,
                 ):
        self.fetch = fetch
        tuples = _offset(scope, table, fetch=fetch)
        name = f"__{table.name}_FETCH_{fetch}__"
        super(FFetchTable, self).__init__(tuples, name)
        scope.register_database(name, self)
        self.fathers = [table]
        self.root = table.root
