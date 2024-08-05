# -*- coding: utf-8 -*-

from typing import Sequence

from formulas import register_formula
from formulas.tables.base_table import FBaseTable
from formulas.tuples.deleted_tuple import FDeletedTuple


@register_formula('empty_table')
class FEmptyTable(FBaseTable):
    """
    We will create a deleted tuple for FEmptyTable to verify VALID with other formal tables.
    """

    def __init__(self, scope, attributes: Sequence = [], name: str = None, ):
        deleted_tuple = FDeletedTuple("DELETED_TUPLE", attributes)
        scope.register_tuple(deleted_tuple.name, deleted_tuple)
        deleted_tuple.SORT = scope._declare_tuple_sort(deleted_tuple.name)
        scope.environment.DBMS_facts.append(
            scope.environment.DELETED_FUNCTION(deleted_tuple.SORT)
        )
        super(FEmptyTable, self).__init__([deleted_tuple], "EMPTY_TABLE")
        scope.register_database(name, self)
        self.fathers = self.root = None

    def reset_attributes(self, attributes):
        self[0].attributes = attributes

    def __getitem__(self, index):
        if index > 1:
            raise Exception('Empty table only has a deleted tuple for formulas generation.')
        return self.tuples[index]
