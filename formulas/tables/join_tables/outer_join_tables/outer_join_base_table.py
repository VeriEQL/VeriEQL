# -*- coding:utf-8 -*-

from formulas import register_formula
from formulas.tables.join_tables.join_base_table import FJoinBaseTable


@register_formula('outer_join')
class FOuterJoinBaseTable(FJoinBaseTable):
    def __init__(self, *args, **kwargs):
        super(FOuterJoinBaseTable, self).__init__(*args, **kwargs)
