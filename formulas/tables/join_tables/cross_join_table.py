# -*- coding:utf-8 -*-

from typing import (
    Sequence,
)

from context import Context
from errors import NotSupportedError
from formulas import register_formula
from formulas.columns.attribute import FAttribute
from formulas.expressions.expression_tuple import FExpressionTuple
from formulas.expressions.predicates import PredicateType
from formulas.tables.base_table import FBaseTable
from formulas.tables.join_tables._utils import (
    _analyze_using,
)
from formulas.tables.join_tables.inner_join_table import _inner_product
from formulas.tables.join_tables.join_base_table import FJoinBaseTable


@register_formula('cross_join')
class FCrossJoinTable(FJoinBaseTable):
    def __init__(self,
                 scope,
                 tables: Sequence[FBaseTable],
                 condition: PredicateType = None,
                 by: str = 'on',
                 name: str = None,
                 ):
        name = name or '_CrossJoin_'.join(t.name for t in tables)

        # 1) product
        prev_tables, curr_table = _inner_product(scope, tables, name)
        self.is_using = by == 'using'
        self._hidden_attributes = None

        if len(curr_table) == 0:
            super(FCrossJoinTable, self).__init__(scope, curr_table, name)
            self.fathers = prev_tables
            self.root = [t.root for t in prev_tables]
            self.condition = None
        else:
            # 2) filter
            if by == 'using':
                equal_conditions, condition = _analyze_using(condition, curr_table[0].attributes)
                corresponding_attributes, remove_attributes = zip(*equal_conditions)
                attributes = []
                for attr in curr_table[0].attributes:
                    if attr in remove_attributes:
                        corr_attr = corresponding_attributes[remove_attributes.index(attr)]
                        corr_attr._sugar_full_name = str(attr)
                        corr_attr._sugar_name = attr.name
                    else:
                        attributes.append(attr)
                for tuple in curr_table:
                    tuple.attributes = attributes
                self._hidden_attributes = remove_attributes
                self.condition = []
            elif by == 'on':
                if condition == True:
                    self.condition = None
                else:
                    self.condition = []
            elif by is None:
                self.condition = condition
            else:
                raise NotImplementedError(f'No such Cross Join operation {by}')

            if self.condition is not None:
                tmp_ctx = Context(databases={'tmp': curr_table})
                tmp_ctx.prev_database = tmp_ctx['tmp']
                tmp_ctx.attributes = curr_table[0].attributes
                for tuple in curr_table:
                    bound_scope = {str(attr): t.SORT for t in tuple for attr in t.attributes}
                    tmp = scope.encoder.parse_expression(condition, bound_scope=bound_scope, ctx=tmp_ctx)
                    if isinstance(tmp, FAttribute | FExpressionTuple):
                        raise NotSupportedError(
                            f"{self.__class__.__name__} ON condition does support only an attribute.")
                    self.condition.append(tmp)

            # CROSS JOIN does not remove duplicate columns
            super(FCrossJoinTable, self).__init__(scope, curr_table, name)
            self.fathers = prev_tables
            self.root = [t.root for t in prev_tables]
