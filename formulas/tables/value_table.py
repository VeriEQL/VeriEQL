# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.tables.base_table import FBaseTable


@register_formula('value_table')
class FValueTable(FBaseTable):
    def __init__(self,
                 scope,
                 table: FBaseTable,
                 name: str = None,
                 ):
        """
        if in where clause, 3 > (SELECT COUNT(*) FROM ....)
        we will wrap it into 3 > FValueTable[(SELECT COUNT(*) FROM ....)]
        """
        name = name or scope._get_new_tuple_name()
        super(FValueTable, self).__init__(table, name)
        scope.register_database(name, self)
        self.fathers = [table]
        self.root = table.root or table.name

    def __str__(self):
        return f'{self.fathers[0].attributes[0]}({self[0].name})'
