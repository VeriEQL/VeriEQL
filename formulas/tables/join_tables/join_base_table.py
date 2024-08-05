# -*- coding:utf-8 -*-


from typing import (
    Sequence,
    Optional,
)

from formulas import register_formula
from formulas.tables.base_table import FBaseTable


@register_formula('join')
class FJoinBaseTable(FBaseTable):
    def __init__(self,
                 scope,
                 table: Sequence,
                 name: Optional[str] = None,
                 ):
        super(FJoinBaseTable, self).__init__(table, name)
        scope.register_database(name, self)
