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
from formulas.tables.join_tables._utils import alias_check
from formulas.tables.join_tables.outer_join_tables.outer_join_base_table import FOuterJoinBaseTable
from formulas.tuples.null_tuple import FNullTuple
from formulas.tuples.outer_join_tuple import FOuterJoinTuple


def _full_outer_product(
        scope,
        tables: Sequence[FBaseTable],
        name: str,
):
    lhs_table, rhs_table = tables
    # return tables, curr_table, left_null_tuple, right_null_tuple, children, pity_tuples
    if len(lhs_table) == 0:
        return tables, lhs_table, None, None, None, None
    if len(rhs_table) == 0:
        return tables, rhs_table, None, None, None, None

    lhs_table, rhs_table = tables = alias_check(scope, tables, name)

    right_null_tuple = FNullTuple(scope, rhs_table.attributes)
    # for this case where (EMPTY_TABLE | XXX) FULL JOIN EMPTY_TABLE <=> EMPTY_TABLE | concate(XXX, EMPTY_TABLE)
    children = {}
    pity_tuples = []

    concate_mapping = {}

    curr_table = []
    for i, ltuple in enumerate(lhs_table, start=1):
        outer_null_tuple = FOuterJoinTuple(ltuple, right_null_tuple, name=scope._get_new_tuple_name())
        scope.register_tuple(outer_null_tuple.name, outer_null_tuple)
        outer_null_tuple.SORT = scope._declare_tuple_sort(outer_null_tuple.name)
        children[ltuple.SORT] = []

        for j, rtuple in enumerate(rhs_table, start=1):
            outer_tuple = FOuterJoinTuple(ltuple, rtuple, name=scope._get_new_tuple_name())
            outer_tuple.SORT = scope._declare_tuple_sort(outer_tuple.name)
            scope.register_tuple(outer_tuple.name, outer_tuple)

            # outer_tuple.add_mutex(outer_null_tuple.SORT)
            # outer_null_tuple.add_mutex(outer_tuple.SORT)
            outer_tuple.add_mutex((len(rhs_table) + 1) * i - 1)
            outer_tuple_index = len(curr_table)
            curr_table.append(outer_tuple)
            outer_null_tuple.add_mutex(outer_tuple_index)

            # children[ltuple.SORT].append(outer_tuple.SORT)
            children[ltuple.SORT].append(outer_tuple_index)
            if rtuple.SORT in children:
                # children[rtuple.SORT].append(outer_tuple.SORT)
                children[rtuple.SORT].append(outer_tuple_index)
            else:
                # children[rtuple.SORT] = [outer_tuple.SORT]
                children[rtuple.SORT] = [outer_tuple_index]

            if rtuple.name not in concate_mapping:
                concate_mapping[rtuple.name] = [outer_tuple]
            else:
                concate_mapping[rtuple.name].append(outer_tuple)

        # children[ltuple.SORT].append(outer_null_tuple.SORT)
        children[ltuple.SORT].append(len(curr_table))
        pity_tuples.append(outer_null_tuple)
        curr_table.append(outer_null_tuple)

    lhs_table, rhs_table = tables
    # lhs_table = tables[0] = deepcopy(lhs_table)
    lhs_table.name = f'{scope._get_new_databases_name()}_COPY_FROM_{lhs_table.name}'
    scope.register_database(lhs_table.name, lhs_table)
    left_null_tuple = FNullTuple(scope, lhs_table.attributes)

    for i, rtuple in enumerate(rhs_table):  # ignore the last tuple because it's an all-null tuple
        outer_null_tuple = FOuterJoinTuple(left_null_tuple, rtuple, name=scope._get_new_tuple_name())
        scope.register_tuple(outer_null_tuple.name, outer_null_tuple)
        outer_null_tuple.SORT = scope._declare_tuple_sort(outer_null_tuple.name)

        for j, t in enumerate(concate_mapping[rtuple.name]):
            # t.add_mutex(outer_null_tuple.SORT)
            # outer_null_tuple.add_mutex(t.SORT)
            t.add_mutex(len(curr_table))
            outer_null_tuple.add_mutex(i + (len(rhs_table) + 1) * j)

        # children[rtuple.SORT].append(outer_null_tuple.SORT)
        children[rtuple.SORT].append(len(curr_table))
        pity_tuples.append(outer_null_tuple)
        curr_table.append(outer_null_tuple)

    children = list(children.values())
    return tables, curr_table, left_null_tuple, right_null_tuple, children, pity_tuples


@register_formula('full_outer_join')
class FFullOuterJoinTable(FOuterJoinBaseTable):
    def __init__(self,
                 scope,
                 tables: Sequence[FBaseTable],
                 condition: PredicateType = None,
                 by: str = 'on',
                 name: str = None,
                 ):
        name = name or '_FullOuterJoin_'.join(t.name for t in tables)

        # 1) product
        prev_tables, curr_table, left_null_tuple, right_null_tuple, self._children, self._pity_tuples = \
            _full_outer_product(scope, tables, name)
        self.left_null_tuple = left_null_tuple
        self.right_null_tuple = right_null_tuple
        self.is_using = by == 'using'
        self._hidden_attributes = None

        if len(curr_table) == 0:
            super(FFullOuterJoinTable, self).__init__(scope, curr_table, name)
            self.fathers = prev_tables
            self.root = [t.root for t in prev_tables]
            self.condition = None
        else:
            # 2) filter
            self.condition = []
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
                self.condition = [
                    None if any(isinstance(t, FNullTuple) for t in tuple) else condition
                    for tuple in curr_table
                ]
            elif by == 'on':
                tmp_ctx = Context(databases={'tmp': curr_table})
                tmp_ctx.prev_database = tmp_ctx['tmp']
                tmp_ctx.attributes = curr_table[0].attributes
                for tuple in curr_table:
                    if any(isinstance(t, FNullTuple) for t in tuple):
                        self.condition.append(None)
                    else:
                        bound_scope = {str(attr): t.SORT for t in tuple for attr in t.attributes}
                        tmp = scope.encoder.parse_expression(condition, bound_scope=bound_scope, ctx=tmp_ctx)
                        if isinstance(tmp, FAttribute | FExpressionTuple):
                            raise NotSupportedError(
                                f"{self.__class__.__name__} ON condition does support only an attribute.")
                        self.condition.append(tmp)
            else:
                raise NotImplementedError(f'No such Inner Join operation {by}')

            super(FFullOuterJoinTable, self).__init__(scope, curr_table, name)
            self.fathers = prev_tables
            self.root = [t.root for t in prev_tables]
