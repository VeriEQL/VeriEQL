# -*- coding:utf-8 -*-


from typing import Sequence

from formulas import register_formula
from formulas.tables.base_table import FBaseTable
from formulas.tuples.alias_tuple import FAliasTuple


def _alias(
        scope,
        table: FBaseTable,
        condition: Sequence,
        alias_attributes: bool = False,
):
    alias_table = []
    for tuple in table:
        if alias_attributes:
            curr_tuple = FAliasTuple(tuple, condition, name=scope._get_new_tuple_name())
            scope.register_tuple(curr_tuple.name, curr_tuple)
            curr_tuple.SORT = scope._declare_tuple_sort(curr_tuple.name)
        else:
            curr_tuple = FAliasTuple(tuple, condition, name=tuple.name)
            curr_tuple.SORT = tuple.SORT
        alias_table.append(curr_tuple)
    return alias_table


@register_formula('alias_table')
class FAliasTable(FBaseTable):
    """
    1) in most cases, we won't create new attributes and mapping values of old attributes to new ones;
    2) in union cases, father tables might have different attributes, therefore, we need to create new attributes if they are different.
    """

    def __init__(self,
                 scope,
                 table: FBaseTable,
                 condition: Sequence,
                 name: str = None,
                 alias_attributes: bool = False,
                 ):
        tuples = _alias(scope, table, condition, alias_attributes)
        self.alias_attributes = alias_attributes
        name = name or scope._get_new_databases_name()
        super(FAliasTable, self).__init__(tuples, name)
        scope.register_database(name, self)
        self.fathers = [table]
        self.root = table.root or table.name
