# -*- coding:utf-8 -*-

import copy
import itertools
from typing import Sequence

from formulas.expressions.expression import FExpression
from formulas.expressions.operator import FOperator
from formulas.tables.alias_table import FAliasTable
from formulas.tables.base_table import FBaseTable
from utils import uuid_hash


def _find_overlapping_attributes(left_attrs, right_attrs):
    return [
        lattr.name
        for lattr, rattr in itertools.product(left_attrs, right_attrs)
        if lattr.name == rattr.name
    ]


def _analyze_default(left_attrs, right_attrs):
    equal_conditions = []
    for lattr, rattr in itertools.product(left_attrs, right_attrs):
        if lattr.name == rattr.name:
            pair = [lattr, rattr]
            equal_conditions.append(pair)
    condition = [FExpression(FOperator('eq'), [cond[0], cond[-1]]) for cond in equal_conditions]
    if len(condition) == 1:
        condition = condition[0]
    else:
        condition = FExpression(FOperator('and'), condition)
    return equal_conditions, condition


def _analyze_using(condition, attributes):
    # only works for INNER JOIN
    equal_conditions = []
    for cond in condition:
        pair = [attr for attr in attributes if attr == cond]
        # assert len(pair) == 2
        equal_conditions.append(pair)

    # since we don't remove the duplicate attributes in USING, it might return multiple attributes (greater than 2)
    # therefore, we only consider the 1st and the last attributes as condition
    condition = [FExpression(FOperator('eq'), [cond[0], cond[-1]]) for cond in equal_conditions]
    if len(condition) == 1:
        condition = condition[0]
    else:
        condition = FExpression(FOperator('and'), condition)
    return equal_conditions, condition


def _contain_case(expr):
    # DBChecker does not support case
    if isinstance(expr, list):
        for opd in expr:
            if _contain_case(opd):
                return True
    elif isinstance(expr, dict):
        for key, value in expr.items():
            if key == 'case':
                return True
            else:
                return _contain_case(value)
    return False


def alias_check(
        scope,
        tables: Sequence[FBaseTable],
        name: str,
):
    # since we do not create new attribute for alias, here we need to check whether there exist the same attributes from father tables
    # if there are any same attributes, we need create new attributes for those duplicate attributes
    # to avoid recall the same attribute for later reuse
    lhs_table, rhs_table = tables
    alias_indices = []
    for idx, attr in enumerate(rhs_table.attributes):
        if attr in lhs_table.attributes:
            alias_indices.append(idx)
    if len(alias_indices) > 0:
        condition = [rhs_table.attributes, copy.copy(rhs_table.attributes)]
        for idx in alias_indices:
            attr = condition[-1][idx]
            if isinstance(rhs_table, FAliasTable) and rhs_table.alias_attributes == False:
                condition[-1][idx] = scope.declare_attribute(name=attr.prefix, literal=attr.name, _uuid=uuid_hash())
            else:
                condition[-1][idx] = scope.declare_attribute(name=f'{name}_AS_{attr.prefix}', literal=attr.name,
                                                             _uuid=uuid_hash())
                condition[-1][idx]._sugar_full_name = str(attr)
                condition[-1][idx]._sugar_name = attr.name
        rhs_table = FAliasTable(scope, rhs_table, condition,
                                name=f"Alias_created_for_{rhs_table.name}", alias_attributes=True)
    tables = [lhs_table, rhs_table]
    return tables
