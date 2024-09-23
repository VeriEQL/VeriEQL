# -*- coding:utf-8 -*-
import itertools
import math
import re
from copy import deepcopy, copy
from typing import *

from ordered_set import OrderedSet
from z3 import (
    ArithRef,
    ExprRef,
    is_true,
    is_false
)

import utils
from constants import (
    NumericType,
    SPACE_STRING,
    IS_TRUE,
    IS_FALSE,
    BACKUP_SUFFIX,
    SQL_NULL,
    And,
    Not,
    IntVal,
    RealVal,
    Z3_FALSE,
    Z3_TRUE,
    DIALECT,
)
from context import Context, GroupbyContext
from errors import *
from formulas.columns import *
from formulas.expressions import *
from formulas.tables import *
from formulas.tuples import *
from logger import LOGGER
from utils import (
    CodeSnippet, ValuesTable, now
)
from visitors.interm_function import IntermFunc

ExcutableType = NumericType | FDigits | bool


def is_literal(query):
    return isinstance(query, dict) and len(query) == 1 and 'literal' in query


def eval_operation(operator: FOperator, operands: list):
    if all(isinstance(opd, ExcutableType) for opd in operands):
        out = operator(*operands)
        if isinstance(out, ExprRef):
            return out
        else:
            return FDigits(out)
    else:
        return FExpression(operator, operands)


def _inner_product(conds):
    # [con1, [cond2, cond3]] => [[con1, cond2], [con1, cond3]]
    MAX_COND_NUM = max(len(cond) if isinstance(cond, list | tuple) else 1 for cond in conds)
    if MAX_COND_NUM == 1:
        return conds
    else:
        new_conds = [[] for _ in range(MAX_COND_NUM)]
        for cond in conds:
            if isinstance(cond, list | tuple):
                for idx in range(MAX_COND_NUM):
                    new_conds[idx].append(cond[idx])
            else:
                for idx in range(MAX_COND_NUM):
                    new_conds[idx].append(cond)
        out = []
        for conds in new_conds:
            tmp = OrderedSet()
            for c in conds:
                if is_false(c):
                    tmp = [Z3_FALSE]
                    break
                elif is_true(c):
                    continue
                else:
                    tmp.add(c)
            if len(tmp) > 0:
                out.append(list(tmp))
        return out


def _contain_case(expr):
    if isinstance(expr, FCasePredicate):
        return True
    elif isinstance(expr, FExpression):
        for opd in expr.operands:
            if _contain_case(opd) == True:
                return True
    else:
        return False


def linearize_case(expr):
    if isinstance(expr, FCasePredicate):
        conds, exprs = expr.when_clauses, expr.then_clauses
        # TODO: case condition is a nested case is too complicate, we do not support right now
        if any(_contain_case(cond) for cond in conds):
            raise NotSupportedError("case condition is a nested case is too complicate")

        if len(conds) == 1:
            else_cond = FExpression(FOperator('not'), copy(conds))
            else_cond = FIsNullOrHoldPredicate(else_cond)
        else:
            else_cond = FExpression(FOperator('not'), [FExpression(FOperator('or'), copy(conds))])
            else_cond = FIsNullOrHoldPredicate(else_cond)
        conds.append(else_cond)
        exprs.append(expr.else_clause)
        cases = []
        for idx, expr in enumerate(exprs):
            contain_case = _contain_case(expr)
            linearized_expr = linearize_case(expr)
            case = _inner_product([conds[idx], linearized_expr])
            if contain_case:
                cases.extend(case)
            else:
                cases.append(case)
        return cases
    elif isinstance(expr, FInPredicate | FNotInPredicate):
        return expr
    elif isinstance(expr, FIsNullPredicate) and isinstance(expr.value, FCasePredicate):
        operands = linearize_case(expr.value)
        for idx, opds in enumerate(operands):
            if isinstance(opds[-1], FNull):
                # [cond => NULL] is NULL <=> cond
                operands[idx] = opds[0]
            elif isinstance(opds[-1], ExcutableType):
                # [cond => 1] is NULL <=> False
                operands[idx] = Z3_FALSE
            else:
                # [cond => f] is NULL <=> cond /\ f is NULL
                operands[idx] = FExpression(FOperator('and'), [opds[0], FIsNullPredicate(opds[-1])])
        return operands
    elif isinstance(expr, FIsNotNullPredicate) and isinstance(expr.value, FCasePredicate):
        operands = linearize_case(expr.value)
        for idx, opds in enumerate(operands):
            if isinstance(opds[-1], FNull):
                # [cond => NULL] is NOT NULL <=> False
                operands[idx] = FDigits(0)  # False
            elif isinstance(opds[-1], ExcutableType):
                # [cond => 1] is NOT NULL <=> True
                operands[idx] = Z3_TRUE
            else:
                # [cond => f] is NOT NULL <=> cond /\ f is NOT NULL
                operands[idx] = FExpression(FOperator('and'), [opds[0], FIsNotNullPredicate(opds[-1])])

        return operands
    elif isinstance(expr, FIsTruePredicate | FIsNotFalsePredicate) and isinstance(expr.value, FCasePredicate):
        operands = linearize_case(expr.value)
        for idx, opds in enumerate(operands):
            if len(opds) == 1:
                operands[idx] = opds[0]
            else:
                operands[idx] = FExpression(FOperator('and'), opds)
        return operands
    elif isinstance(expr, FIsFalsePredicate | FIsNotTruePredicate) and isinstance(expr.value, FCasePredicate):
        operands = linearize_case(expr.value)
        for idx, opds in enumerate(operands):
            if len(opds) == 1:
                operands[idx] = FExpression(FOperator('not'), opds)
            else:
                operands[idx] = FExpression(FOperator('not'), [FExpression(FOperator('and'), opds)])
        return operands
    elif isinstance(expr, FExpression):
        case_indces = set()
        for idx, operand in enumerate(expr.operands):
            expr.operands[idx] = linearize_case(operand)
            if isinstance(expr.operands[idx], list):
                # expr.operands[idx] = expr.operands[idx]
                case_indces.add(idx)
        if expr.operator == 'not' and case_indces == {0}:
            scatter_expr = []
            for e in expr[0]:
                if isinstance(e, FExpression):
                    scatter_expr.append(FExpression(e.operator, [e[0], FExpression(expr.operator, [e[1]])]))
                else:
                    scatter_expr.append(FExpression(FOperator('and'), [e[0], FExpression(expr.operator, [e[1]])]))
            # expr = [FExpression(e.operator, [e[0], FExpression(expr.operator, [e[1]])]) for e in expr[0]]
            return scatter_expr
        if len(case_indces) > 0:
            # extend case
            for idx, operand in enumerate(expr.operands):
                if idx not in case_indces:
                    expr.operands[idx] = [operand]
            operator = expr.operator
            operands = expr.operands
            expr = []
            if operator == 'and':  # logical operations
                for opds in itertools.product(*operands):
                    new_opds = []
                    for opd in opds:
                        if isinstance(opd, list | tuple):
                            new_opds.extend(opd)
                        else:
                            new_opds.append(opd)
                    expr.append(FExpression(operator, new_opds))
            elif operator == 'or':
                new_opds = []
                for opd in list(itertools.chain(*operands)):
                    if isinstance(opd, list | tuple):
                        new_opds.extend(opd)
                    else:
                        new_opds.append(opd)
                expr.append(FExpression(operator, new_opds))
            elif len(operands) == 2:
                # CASE ... END = 1 | 1 = CASE ... END | CASE1 = CASE2
                if len(case_indces) == 1:
                    if case_indces == {0}:
                        # CASE ... END = 1
                        for opd1, opd2 in itertools.product(*operands):
                            tmp = opd1[:-1] + [FExpression(operator, [opd1[-1], opd2])]
                            if len(tmp) > 1:
                                tmp = FExpression(FOperator('and'), tmp)
                            else:
                                tmp = tmp[0]
                            expr.append(tmp)
                    else:
                        # 1 = CASE ... END
                        for opd1, opd2 in itertools.product(*operands):
                            # tmp = [FExpression(operator, [opd1, opd2[0]])] + opd2[1:]
                            tmp = opd2[:-1] + [FExpression(operator, [opd1, opd2[-1]])]
                            if len(tmp) > 1:
                                tmp = FExpression(FOperator('and'), tmp)
                            else:
                                tmp = tmp[0]
                            expr.append(tmp)
                else:
                    #  CASE1 = CASE2
                    for opd1, opd2 in itertools.product(*operands):
                        tmp = opd1[:-1] + opd2[:-1] + [FExpression(operator, [opd1[-1], opd2[-1]])]
                        if len(tmp) > 1:
                            tmp = FExpression(FOperator('and'), tmp)
                        else:
                            tmp = tmp[0]
                        expr.append(tmp)
            else:
                raise NotImplementedError(expr)
        return expr
    else:
        return expr


def _refine_expression(expr):
    if isinstance(expr, FCast):
        # 1) remove CAST in condition
        return _refine_expression(expr.EXPR)
    elif isinstance(expr, list):
        for idx, k in enumerate(expr):
            expr[idx] = _refine_expression(k)
        return expr
    elif isinstance(expr, FExpression):
        """
        2) if it includes NULL, return NULL. only NULL in where clause return False
        NULL op * => NULL
        """
        for idx, operand in enumerate(expr.operands):
            expr.operands[idx] = _refine_expression(operand)
            if isinstance(expr.operands[idx], FNull):
                return expr.operands[idx]
        return expr
    else:
        return expr


def _empty_table_check(tables: Sequence[FBaseTable]):
    for table in tables:
        if table.root == 'EMPTY_TABLE' or table.name == 'EMPTY_TABLE':
            return table
    return None


def is_cross_join(join_query):
    return isinstance(join_query[1], dict) and ('cross join' in join_query[1])


def is_natural_join(join_query):
    return (
            isinstance(join_query[0], dict) \
            and ('value' in join_query[0]) and join_query[0].get('name', None) in ['NATURAL', 'natural'] \
            and isinstance(join_query[1], dict) and ('join' in join_query[1])
    ) or (
            len(join_query) == 3 and join_query[-1] == 'NATURAL'
    )


def is_inner_join(join_query):
    return isinstance(join_query[1], dict) \
        and (('inner join' in join_query[1]) ^ ('join' in join_query[1])) \
        and (('using' in join_query[1]) ^ ('on' in join_query[1]))


def is_outer_join(join_query):
    return isinstance(join_query[1], dict) \
        and (
                ('left outer join' in join_query[1]) ^ ('left join' in join_query[1]) ^ \
                ('right outer join' in join_query[1]) ^ ('right join' in join_query[1]) ^ \
                ('full outer join' in join_query[1]) ^ ('full join' in join_query[1])
        ) and (
                ('using' in join_query[1]) ^ ('on' in join_query[1])
        )


def is_outer_join2(join_query):
    return isinstance(join_query[0], dict) \
        and ('value' in join_query[0]) and join_query[0].get('name', None) in ['NATURAL', 'natural'] \
        and isinstance(join_query[1], dict) and (
                ('left join' in join_query[1]) ^ ('left outer join' in join_query[1]) ^ \
                ('right join' in join_query[1]) ^ ('right outer join' in join_query[1])
        )


def is_cartesian_product1(join_query):
    return isinstance(join_query[1], str) or isinstance(join_query[1], FBaseTable) or ('value' in join_query[1])


def is_cartesian_product2(join_query):
    return isinstance(join_query[1], dict) \
        and (bool(join_query[1].get('inner join', False)) ^ bool(join_query[1].get('join', False)))


def is_cartesian_product3(join_query):
    return isinstance(join_query[1], dict) and len(join_query[1]) == 1 and (
            bool(join_query[1].get('full join', False)) | bool(join_query[1].get('full outer join', False))
    )


class Encoder:
    def __init__(self, scope):
        self.scope = scope

    ############################ Display ############################

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

    ############################ join ############################

    def parse_values_table(self, values_table, ctx):
        tuples = []
        saved_attributes = {}
        formulas = []
        for row in values_table.rows:
            fields = []
            for idx, attr in enumerate(values_table.attributes):
                if attr in saved_attributes:
                    attribute = saved_attributes[attr]
                else:
                    attribute = self.scope.environment.declare_attribute(values_table.name, literal=attr)
                    saved_attributes[attr] = attribute
                value = self.parse_expression(row[idx], ctx)
                # value = self.scope.visitor.visit(value)(None).VALUE
                fields.append(FField(attribute, value))
            base_tuple = self.scope.environment._declare_tuple(fields)
            tuples.append(base_tuple)
            formulas.append(Not(self.scope.DELETED_FUNCTION(base_tuple.SORT)))  # Not(Deleted(tuple))
            # for operand in base_tuple:
            #     attr = self.scope.visitor.visit(operand.attribute)(base_tuple.SORT)
            #     if isinstance(operand.value, FNull):
            #         formulas.append(attr.NULL)
            #     elif isinstance(operand.value, FDate | FTime | FTimestamp):
            #         formulas.extend([operand.operator.value(attr, operand.value.EXPR), Not(attr.NULL)])
            #     else:
            #         formulas.extend([operand.operator.value(attr.VALUE, operand.value), Not(attr.NULL)])
            for operand in base_tuple:
                attr = operand.attribute(base_tuple.SORT)
                if isinstance(operand.value, FNull):
                    formulas.append(attr.NULL)
                elif isinstance(operand.value, Union[FDate, FTime, FTimestamp]):
                    formulas.extend([operand.operator.value(attr, operand.value.EXPR), Not(attr.NULL)])
                else:
                    value_tuple = self.scope.visitor.visit(operand.value)(base_tuple.SORT)
                    formulas.extend([operand.operator.value(attr.VALUE, value_tuple.VALUE), Not(attr.NULL)])
        table = self.scope.environment._declare_table(tuples, values_table.name)
        self.scope.register_formulas(
            formulas=CodeSnippet(code=And(*formulas), docstring=f'{table.name} VALUES database', docstring_first=True)
        )
        return table

    def parse_join_clause(self, join_query, ctx: Context):
        def _find_tables(join_query):
            if is_cross_join(join_query):
                # CROSS JOIN
                # ['EMP', {'cross join': 'DEPT'}]
                # ['EMP', {'full join': 'DEPT'}]
                lhs_table = self.analyze(join_query[0], ctx).prev_database
                ctx.pop(lhs_table.name)
                rhs_table = self.analyze(join_query[1]['cross join'], ctx).prev_database
                ctx.pop(rhs_table.name)
                table_list = [lhs_table, rhs_table]
                empty_table = _empty_table_check(table_list)
                if empty_table is None:
                    if 'on' in join_query[1]:
                        condition = join_query[1]['on']
                        by = 'on'
                    elif 'using' in join_query[1]:
                        condition = join_query[1]['using']
                        if isinstance(condition, str):
                            condition = [condition]
                        by = 'using'
                    else:
                        condition = by = None
                        # raise NotImplementedError(f"CROSS JOIN only supports ON/USING, not {join_query[1]['using']}")
                    table = FCrossJoinTable(self.scope, table_list, condition, by)
                    if table.condition is not None:
                        # note that ON condition could be VERY complicate, we use a filter table to deal with it
                        table = FFilterTable(self.scope, table, table.condition)
                    # table = FCrossJoinTable(self.scope, table_list)
                else:
                    table = FEmptyTable(
                        self.scope,
                        attributes=list(itertools.chain(*[t.attributes for t in table_list])),
                    )
            elif is_natural_join(join_query):
                # table_reference NATURAL [INNER | {LEFT|RIGHT} [OUTER]] JOIN table_factor
                # [{'value': 'EMP', 'name': 'NATURAL'}, {'join': 'DEPT'}]
                # [{'value': 'EMP', 'name': 'NATURAL'}, {'left join': 'DEPT'}]
                # [{'value': 'EMP', 'name': 'NATURAL'}, {'join': 'DEPT', 'using': 'name'}]
                # [{'value': 'EMP', 'name': 'NATURAL'}, {'join': 'DEPT', 'using': ['id', 'name']}]
                if isinstance(join_query[0], FJoinBaseTable):
                    lhs_table = join_query[0]
                else:
                    lhs_table = self.analyze(join_query[0]['value'], ctx).prev_database
                if 'join' in join_query[1]:
                    if isinstance(join_query[1]['join'], dict):
                        rhs_table_name = join_query[1]['join']['value']
                    elif isinstance(join_query[1]['join'], str):
                        rhs_table_name = join_query[1]['join']
                    else:
                        raise NotImplementedError(join_query)

                    rhs_table = self.analyze(rhs_table_name, ctx).prev_database
                # elif 'left join' in join_query[1]:
                #     rhs_table = self.analyze(join_query[1]['left join'], ctx).prev_database
                # elif 'left outer join' in join_query[1]:
                #     rhs_table = self.analyze(join_query[1]['left outer join'], ctx).prev_database
                # elif 'right join' in join_query[1]:
                #     rhs_table = self.analyze(join_query[1]['right join'], ctx).prev_database
                # elif 'right outer join' in join_query[1]:
                #     rhs_table = self.analyze(join_query[1]['right outer join'], ctx).prev_database
                else:
                    raise NotImplementedError(f"Unknown NATURAL JOIN `{join_query}`")
                ctx.pop(rhs_table.name)
                table_list = [lhs_table, rhs_table]

                empty_table = _empty_table_check(table_list)
                if empty_table is None:
                    if len(join_query[1]) == 1:
                        condition = None
                    elif join_query[1].get('using', False):
                        condition = join_query[1].get('using', None)
                        if isinstance(condition, str):
                            condition = [condition]
                    else:
                        raise NotImplementedError(
                            f"NATURAL JOIN only supports USING, not {join_query[1]}")
                    table = FNaturalJoinTable(self.scope, table_list, condition)
                else:
                    table = FEmptyTable(
                        self.scope,
                        attributes=list(itertools.chain(*[t.attributes for t in table_list])),
                    )
            elif is_inner_join(join_query):
                # (INNER) JOIN
                # ['EMP', {'inner join': 'DEPT', 'on': {'eq': ['EMP.dept_id', 'DEPT.id']}}]
                # ['EMP', {'inner join': 'DEPT', 'using': 'name'}]
                lhs_table = self.analyze(join_query[0], ctx).prev_database
                ctx.pop(lhs_table.name)
                rhs_table = join_query[1].get('inner join', None) or join_query[1].get('join', None)
                rhs_table = self.analyze(rhs_table, ctx).prev_database
                ctx.pop(rhs_table.name)
                table_list = [lhs_table, rhs_table]
                empty_table = _empty_table_check(table_list)
                if empty_table is None:
                    if 'on' in join_query[1]:
                        condition = join_query[1]['on']
                        by = 'on'
                    elif 'using' in join_query[1]:
                        condition = join_query[1]['using']
                        if isinstance(condition, str):
                            condition = [condition]
                        by = 'using'
                    else:
                        raise NotImplementedError(f"INNER JOIN only supports ON/USING, not {join_query[1]['using']}")
                    table = FInnerJoinTable(self.scope, table_list, condition, by)
                    if table.condition is not None:
                        # note that ON condition could be VERY complicate, we use a filter table to deal with it
                        table = FFilterTable(self.scope, table, table.condition)
                else:
                    table = FEmptyTable(
                        self.scope,
                        attributes=list(itertools.chain(*[t.attributes for t in table_list])),
                    )
            elif is_outer_join(join_query):
                # ['EMP', {'left outer join': 'DEPT', 'on': {'eq': ['EMP.dept_id', 'DEPT.id']}}]
                # [{'value': 'EMP', 'name': 'A'}, {'right outer join': {'value': 'EMP', 'name': 'B'}, 'on': {'eq': ['A.id', 'B.id']}}]
                # [{'value': 'EMP', 'name': 'A'}, {'full outer join': {'value': 'EMP', 'name': 'B'}, 'on': {'eq': ['A.id', 'B.id']}}]
                # ['visits', {'left join': 'transactions', 'on': {'eq': ['visits.visit_id', 'transactions.visit_id']}}]
                join_type = right_table = None
                for k, v in join_query[1].items():
                    if str.endswith(k, 'join'):
                        join_type = k
                        right_table = v
                # assert (join_type is not None) and (right_table is not None)
                lhs_table = self.analyze(join_query[0], ctx).prev_database
                ctx.pop(lhs_table.name)
                rhs_table = self.analyze(right_table, ctx).prev_database
                ctx.pop(rhs_table.name)
                table_list = [lhs_table, rhs_table]

                if 'on' in join_query[1]:
                    condition = join_query[1]['on']
                    by = 'on'
                elif 'using' in join_query[1]:
                    condition = join_query[1]['using']
                    if isinstance(condition, str):
                        condition = [condition]
                    by = 'using'
                else:
                    raise SyntaxError(f"OUTER JOIN only supports ON/USING, not `{join_query[1]['using']}`")
                if join_type == 'left outer join' or join_type == 'left join':
                    table = FLeftOuterJoinTable(self.scope, table_list, condition, by)
                    if table.condition is not None:
                        # note that ON condition could be VERY complicate, we use a filter table to deal with it
                        table = FFilterTable(self.scope, table, table.condition)
                elif join_type == 'right outer join' or join_type == 'right join':
                    table = FRightOuterJoinTable(self.scope, table_list, condition, by)
                    ctx.right_outer_table = True
                    if table.condition is not None:
                        # note that ON condition could be VERY complicate, we use a filter table to deal with it
                        table = FFilterTable(self.scope, table, table.condition)
                elif join_type == 'full outer join' or join_type == 'full join':
                    table = FFullOuterJoinTable(self.scope, table_list, condition, by)
                    if table.condition is not None:
                        # note that ON condition could be VERY complicate, we use a filter table to deal with it
                        table = FFilterTable(self.scope, table, table.condition)
                else:
                    raise NotImplementedError(join_query)
            elif is_outer_join2(join_query):
                # [{'value': 'PERSON', 'name': 'NATURAL'}, {'left outer join': 'ADDRESS'}]
                join_type = list(join_query[1])[0]
                left_table = join_query[0]['value']
                right_table = join_query[1][join_type]
                lhs_table = self.analyze(left_table, ctx).prev_database
                ctx.pop(lhs_table.name)
                rhs_table = self.analyze(right_table, ctx).prev_database
                ctx.pop(rhs_table.name)
                table_list = [lhs_table, rhs_table]
                if 'on' in join_query[1]:
                    condition = join_query[1]['on']
                    by = 'on'
                # elif 'using' in join_query[1]:
                else:
                    by = 'using'
                    if 'using' in join_query[1]:
                        condition = join_query[1]['using']
                        if isinstance(condition, str):
                            condition = [condition]
                    else:
                        # natural outer join
                        from formulas.tables.join_tables._utils import _find_overlapping_attributes
                        condition = _find_overlapping_attributes(*[t.attributes for t in table_list])

                if join_type == 'left outer join' or join_type == 'left join':
                    table = FLeftOuterJoinTable(self.scope, table_list, condition, by)
                    if table.condition is not None:
                        # note that ON condition could be VERY complicate, we use a filter table to deal with it
                        table = FFilterTable(self.scope, table, table.condition)
                elif join_type == 'right outer join' or join_type == 'right join':
                    table = FRightOuterJoinTable(self.scope, table_list, condition, by)
                    ctx.right_outer_table = True
                    if table.condition is not None:
                        # note that ON condition could be VERY complicate, we use a filter table to deal with it
                        table = FFilterTable(self.scope, table, table.condition)
                elif join_type == 'full outer join' or join_type == 'full join':
                    table = FFullOuterJoinTable(self.scope, table_list, condition, by)
                    if table.condition is not None:
                        # note that ON condition could be VERY complicate, we use a filter table to deal with it
                        table = FFilterTable(self.scope, table, table.condition)
                else:
                    raise NotImplementedError(join_query)

            elif is_cartesian_product1(join_query):
                # pure cartesian product:
                # FROM TABLE1 (AS T1), TABLE2 (AS T2)
                lhs_table = self.analyze(join_query[0], ctx).prev_database
                ctx.pop(lhs_table.name)
                rhs_table = self.analyze(join_query[1], ctx).prev_database
                ctx.pop(rhs_table.name)
                table_list = [lhs_table, rhs_table]
                empty_table = _empty_table_check(table_list)
                if empty_table is None:
                    table = FProductTable(self.scope, tables=table_list)
                else:
                    table = FEmptyTable(
                        self.scope,
                        attributes=list(itertools.chain(*[t.attributes for t in table_list])),
                    )
            elif is_cartesian_product2(join_query) or is_cartesian_product3(join_query):
                # pure cartesian product:
                # FROM TABLE1 (AS T1), TABLE2 (AS T2)
                lhs_table = self.analyze(join_query[0], ctx).prev_database
                ctx.pop(lhs_table.name)
                rhs_table = join_query[1]
                rhs_table = rhs_table[list(rhs_table)[0]]
                rhs_table = self.analyze(rhs_table, ctx).prev_database
                ctx.pop(rhs_table.name)
                table_list = [lhs_table, rhs_table]
                empty_table = _empty_table_check(table_list)
                if empty_table is None:
                    table = FProductTable(self.scope, tables=table_list)
                else:
                    table = FEmptyTable(
                        self.scope,
                        attributes=list(itertools.chain(*[t.attributes for t in table_list])),
                    )
            else:
                raise NotImplementedError(join_query)
            return table

        tables = []
        # special deal with `X JOIN X ON`
        for idx, query in enumerate(join_query[:2]):
            if isinstance(query, ValuesTable):
                query = self.parse_values_table(values_table=query, ctx=ctx)
            elif isinstance(query, dict):
                key = list(query)[0]
                if isinstance(query[key], ValuesTable):
                    query[key] = self.parse_values_table(values_table=query[key], ctx=ctx)
            tables.append(query)
        table = _find_tables(tables)
        for idx, query in enumerate(join_query[2:], start=2):
            if isinstance(query, ValuesTable):
                query = self.parse_values_table(values_table=query, ctx=ctx)

            if 'join' in join_query[idx - 1] and 'name' in join_query[idx - 1]['join'] and \
                    join_query[idx - 1]['join']['name'] in {'natural', 'NATURAL'}:
                # A NATURAL JOIN B NATURAL JOIN C
                table = _find_tables([table, query, 'NATURAL'])
            else:
                table = _find_tables([table, query])
        return table

    ############################ alias ############################

    def _is_alias(self, table_query):
        return isinstance(table_query, dict) and len(table_query) == 2 and \
            table_query.get('value', None) is not None and \
            (table_query.get('name', None) is not None and table_query.get('name', False) not in ['NATURAL', 'natural'])

    def _get_alias_condition(self, src_attributes, dst_table_name, dst_attributes=None):
        # condition = [src_attributes, deepcopy(src_attributes)]
        if dst_attributes is not None and len(src_attributes) != len(dst_attributes):
            raise SyntaxError(f"Alias attributes must keep the same with the original")

        condition = [src_attributes, []]
        for idx, attr in enumerate(src_attributes):
            if isinstance(attr, FAttribute):
                condition[-1].append(attr.detach())
                condition[-1][-1].prefix = dst_table_name
                if dst_attributes is not None:
                    condition[-1][-1].name = dst_attributes[idx]
            else:
                raise NotSupportedError(f"Alias does not support {attr.__class__.__name__} in `PROJECTION`")
        return condition

    ############################ FROM clause ############################

    def parse_from_clause(self, from_clause, ctx: Context):
        if isinstance(from_clause, str):
            if from_clause in ctx.databases:
                table = ctx.databases[from_clause]
            else:
                # create an empty table
                if from_clause == 'VALUES':
                    table = FEmptyTable(self.scope)
                else:
                    raise UnknownDatabaseError(from_clause)
        elif isinstance(from_clause, list):
            try:
                table = self.parse_join_clause(from_clause, ctx)
            except UnknownColumnError as err:
                print(f"\033[1;31;40mPlease de-correlated the ON clause of JOIN into a WHERE clause.\033[0m")
                raise err
        elif isinstance(from_clause, dict):  # nested query
            if ctx.with_clause is None:
                with_databases = None
            else:
                with_databases = {name: ctx.databases[name] for name in ctx.with_clause}
            if self._is_alias(from_clause):
                if from_clause.get('value', None) == from_clause.get('name', None):
                    table = self.analyze(from_clause['value'], with_databases=with_databases,
                                         skip_orderby=True).prev_database
                else:
                    # src_name, dst_name = from_clause.pop('value'), from_clause.pop('name')
                    src_name, dst_name = from_clause['value'], from_clause['name']
                    src_table = self.analyze(src_name, with_databases=with_databases, skip_orderby=True).prev_database
                    if isinstance(dst_name, dict):
                        dst_table_name = list(dst_name)[0]
                        dst_attributes = dst_name[dst_table_name]
                        if isinstance(dst_attributes, str):
                            dst_attributes = [dst_attributes]
                    else:
                        dst_table_name = dst_name
                        dst_attributes = None
                    condition = self._get_alias_condition(src_table.attributes, dst_table_name, dst_attributes)
                    table = FAliasTable(self.scope, src_table, condition=condition, name=dst_table_name)
            else:
                table = self.analyze(from_clause, with_databases=with_databases, skip_orderby=True).prev_database
        elif isinstance(from_clause, ValuesTable):
            table = self.parse_values_table(from_clause, ctx)
        else:
            raise NotImplementedError
        ctx.update_from_clause(table)
        return table

    ############################ predicate/condition ############################

    def _find_attributes(self, name: str, attributes: Sequence[FAttribute], shadow_copy=False, ctx: Context = None):
        """
        no_alias = True, means that SELECT clauses might use an alias attributes and ORDER/GROUPY BY clauses also employ
        this names, but we prefer not use alias names here only in SELECT clauses
        """
        # MySQL does not support T__EXPR$0 replaced by EXPR_DOLLAR_
        index = str.find(name, 'EXPR_DOLLAR_')
        if index >= 0:
            # `t1.EXPR$0` is just a name
            for attr in attributes:
                if attr == name:
                    if shadow_copy:
                        return [attr.detach()]
                    else:
                        return [attr]
            # we cannot find an attribute called `t1.EXPR$0`, so it's an index
            if index > 0:
                table_name = name[:index - 2]
                table_attributes = [attr for attr in attributes if attr.prefix == table_name]
                if len(table_attributes) == 0:
                    raise SyntaxError(f"No such table name `{table_name}`")
            else:
                table_attributes = attributes
            attribute = table_attributes[int(name[index + len('EXPR_DOLLAR_'):])]
            if shadow_copy:
                attribute = attribute.detach()
            return [attribute]

        candidates = []
        # directly find the attribute with the same (alias) name
        # there might be a problem, if we want to user removed attributes from USING of OUTER JOIN, e.g.,
        # SELECT T2.ID FROM T1 LEFT OUTER JOIN DELETED_T2 USING (id), T2.ID could be NULL
        if ('__' in name) and (ctx is not None) and isinstance(ctx.prev_database, FFilterTable) and \
                ctx.prev_database.fathers is not None and \
                isinstance(ctx.prev_database.fathers[0], OuterJoinTableType) and \
                ctx.prev_database.fathers[0]._hidden_attributes is not None:
            for attr in ctx.prev_database.fathers[0]._hidden_attributes:
                if attr == name:
                    if shadow_copy:
                        attr = attr.detach()
                    candidates.append(attr)
        if len(candidates) == 0:
            for attr in attributes:  # DO NOT CHANGE!!!!
                if attr == name:
                    if shadow_copy:
                        attr = attr.detach()
                    candidates.append(attr)
        if len(candidates) == 0:
            LOGGER.debug(f'Unknown column [{name}] in field list. We will create a string constant.')
        elif len(candidates) > 1:
            # if this GROUP-BY/ORDER-BY attribute is ambiguous, refer attribute in SELECT CLAUSE
            if ctx is not None and ctx.select_clause is not None:
                for attr in ctx.select_clause:
                    if attr in candidates:
                        return [attr]
            return [candidates[-1]]
        return candidates

    def _return_non_null_variable_formulas(self, condition: PredicateType):
        formulas = []
        for operand in condition.operands:
            if isinstance(operand, FAttribute):
                formulas.append(FIsNotNullPredicate(operand))
            elif isinstance(operand, PredicateType):
                formulas.extend(self._return_non_null_variable_formulas(operand))
        return formulas

    def _contrain_numeric(self, condition: PredicateType):
        if isinstance(condition, PredicateType):
            for operand in condition.operands:
                if self._contrain_numeric(operand):
                    return True
            return False
        else:
            return isinstance(condition, NumericType)

    def _add_non_null_constraint(self, condition: PredicateType):
        attributes = []
        for operand in condition.operands:
            if isinstance(operand, FAttribute):
                attributes.append(operand)
        condition.update_constraints(attributes)
        return condition

    def _parse_agg_expr(self, agg_cls, operator, operands, ctx, **kwargs):
        distinct = False
        if isinstance(operands, Dict) and len(operands) == 1 and operands.get('distinct', False):
            operands = operands['distinct']
            distinct = True
        if ctx.groupby_ctx is None:
            expr = self.parse_expression(operands, ctx)
        else:
            # first search attribute in FROM clauses
            if isinstance(operands, str) and operands in ctx.from_clause.attributes:
                ori_idx = ctx.from_clause.attributes.index(operands)
            else:
                ori_idx = -1
            if ori_idx != -1:
                expr = ctx.from_clause.attributes[ori_idx]
            else:
                # then in GROUP-BY and SELECT clauses
                expr = self.parse_expression(operands, ctx.groupby_ctx)
        if isinstance(expr, FNull):
            return expr
        elif isinstance(expr, AggregationType):
            raise SyntaxError(f"MySQL does not support agg-nested-agg functions: {agg_cls.__name__}({operands})")
        return agg_cls(self.scope, operator, expr, distinct=distinct, **kwargs)

    def parse_expression(self, expr, ctx: Context, **kwargs):
        if isinstance(expr, FAttribute | ArithRef | FExpression):
            return expr
        elif isinstance(expr, bool):
            return FDigits(int(expr))
        elif isinstance(expr, NumericType):
            return FDigits(expr)
        elif isinstance(expr, str):
            if kwargs.get('temporary_function', False):
                if expr in self.scope.databases:
                    return self.scope.databases[expr]
                else:
                    raise NotImplementedError
            else:
                new_expr = self._find_select_expressions(expr, ctx, **kwargs)
                return new_expr[0]
        elif isinstance(expr, dict):
            if len(expr) > 1 and self.is_nested_query(expr, **kwargs):  # is nested query
                # 3 > ( SELECT count(DISTINCT(e2.Salary)) from Employee e2 Where e2.Salary > A.Salary AND A.DepartmentId = e2.DepartmentId )
                # expr = self.analyze(expr)  # FBaseTable, we need to convert it into a symbolic value
                # expr = FValueTable(self.scope, expr)
                try:
                    # correlated_subquery_ctx = self.analyze(copy(expr))
                    correlated_subquery_ctx = self.analyze(expr, outer_ctx=ctx)
                    referred_table = correlated_subquery_ctx.prev_database
                except UnknownColumnError as uc_err:
                    raise CorrelatedQueryError(expr)
                return referred_table

            operator = list(expr.keys())[0]
            operands = expr[operator]
            match operator:
                case 'value':
                    return self.parse_expression(operands, ctx, **kwargs)
                case 'literal':
                    def _f(operands):
                        if str.startswith(operands, 'Digits_'):
                            opd = operands[7:]
                        else:
                            opd = operands
                        try:
                            symbol = float(opd)
                            if symbol == int(symbol):
                                symbol = int(symbol)
                        except:
                            # operands = operands.replace(':', '_').replace('-', '_').replace('/', '_')
                            symbol = self.scope._declare_value(FSymbol(operands), register=True)
                        return symbol  # string

                    if isinstance(operands, list):
                        operands = [_f(opd) for opd in operands]
                    elif isinstance(operands, str):
                        if len(operands) == 0:
                            operands = SPACE_STRING
                        operands = _f(operands)
                    else:
                        raise NotImplementedError(expr)
                    return operands
                case 'null':
                    return FNull()
                case 'neg':
                    return eval_operation(FOperator('neg'), [self.parse_expression(operands, ctx, **kwargs)])
                case 'pos':
                    return self.parse_expression(operands, ctx, **kwargs)
                case 'coalesce':
                    exprs = []
                    if isinstance(operands, dict | str):
                        operands = [operands]
                    for opd in operands:
                        if opd == {'null': None}:
                            continue
                        opd = self.parse_expression(opd, ctx, **kwargs)
                        exprs.append(opd)
                    if len(exprs) == 1 or utils.is_uninterpreted_func(exprs[0]):
                        return exprs[0]
                    else:
                        return FCoalescePredicate(exprs)
                case 'round':
                    if not isinstance(operands, list):
                        operands = [operands]
                    expression = self.parse_expression(operands[0], ctx, **kwargs)
                    expression.uninterpreted_func = FRound(*operands[1:])
                    return expression
                case 'exists':
                    if isinstance(operands, NumericType):
                        return FDigits(1)
                    elif operands == {'null': None}:  # NULL is not NULL = False
                        return FDigits(0)
                    else:
                        if self.is_nested_query(operands, **kwargs):
                            try:
                                correlated_subquery_ctx = self.analyze(operands, outer_ctx=ctx)
                                ctx.is_correlated_subquery = correlated_subquery_ctx.is_correlated_subquery
                            except UnknownColumnError as uc_err:
                                raise CorrelatedQueryError(operands[1])
                            return FExistsPredicate(correlated_subquery_ctx.prev_database)
                            # raise NotSupportedError('EXISTS')
                        return FIsNotNullPredicate(self.parse_expression(operands, ctx, **kwargs))
                case 'missing' | 'isnull':
                    if isinstance(operands, NumericType):
                        return FDigits(0)
                    elif operands == {'null': None}:  # NULL is NULL = True
                        return FDigits(1)
                    else:
                        return FIsNullPredicate(self.parse_expression(operands, ctx, **kwargs))
                case 'between':
                    attribute = expr['between'][0]
                    lower_bound, upper_bound = expr['between'][1:]
                    expr = {'and': [{'lte': [lower_bound, attribute]}, {'lte': [attribute, upper_bound]}]}
                    return self.parse_expression(expr, ctx, **kwargs)
                case 'not_between':
                    attribute = expr['not_between'][0]
                    lower_bound, upper_bound = expr['not_between'][1:]
                    expr = {'or': [{'lt': [attribute, lower_bound]}, {'gt': [attribute, upper_bound]}]}
                    return self.parse_expression(expr, ctx, **kwargs)
                case 'case':
                    if not isinstance(operands, list):
                        operands = [operands]
                    clauses = []
                    for clause in operands:
                        if isinstance(clause, Dict) and \
                                clause.get('when', None) is not None and clause.get('then', None) is not None:
                            if clause['when'] == True:
                                clauses.append(clause['then'])
                                break

                            clauses.append(self.parse_expression(clause['when'], ctx, **kwargs))
                            clauses.append(self.parse_expression(clause['then'], ctx, **kwargs))
                        else:
                            clauses.append(self.parse_expression(clause, ctx, **kwargs))
                    if len(clauses) % 2 == 0:
                        clauses.append(FNull())  # No else clause, add NULL by default
                    if len(clauses) == 1:
                        return self.parse_expression(clauses[0], ctx, **kwargs)
                    else:
                        return FCasePredicate(clauses)
                case 'if':
                    expr = [self.parse_expression(opd, ctx, **kwargs) for opd in operands]
                    return FCasePredicate(expr)
                case 'ifnull':
                    cond_clause, else_clause = self.parse_expression(operands, ctx, **kwargs)
                    if isinstance(cond_clause, FBaseTable) or isinstance(else_clause, FBaseTable):
                        raise NotSupportedError('IFNULL contains a table.')
                    if isinstance(cond_clause, FNull):
                        return else_clause
                    if isinstance(cond_clause, ExcutableType):
                        return cond_clause
                    if utils.is_uninterpreted_func(cond_clause):
                        # TODO
                        # IFNULL(ROUND(X1), X2)
                        cond_clause.uninterpreted_func = None
                    return FCasePredicate([FIsNullPredicate(cond_clause), else_clause, cond_clause])
                case 'nullif':
                    # return NULL if operands are equal, else return the 1st operand
                    operands = [self.parse_expression(opd, ctx, **kwargs) for opd in operands]
                    return FNullIfPredicate(operands)
                case 'count':
                    if isinstance(operands, int) or operands == '*':
                        return FAggCount(self.scope, operator, '*', **kwargs)
                    elif operands == {'distinct': '*'}:
                        raise SyntaxError('COUNT(DISTINCT *)')
                    else:
                        if isinstance(operands, Dict) and len(operands) == 1 and operands.get('distinct', False):
                            if isinstance(operands['distinct'], list):
                                expr = []
                                for opd in operands['distinct']:
                                    if ctx.groupby_ctx is None:
                                        opd = self.parse_expression(opd['value'], ctx, **kwargs)
                                    else:
                                        opd = self.parse_expression(opd['value'], ctx.groupby_ctx, **kwargs)
                                    if isinstance(opd, FNull | float | int | str | AggregationType):
                                        raise SyntaxError(
                                            f'`COUNT({operands})` contains NULL | constants | Aggregations')
                                    expr.append(opd)
                            else:
                                if ctx.groupby_ctx is None:
                                    expr = self.parse_expression(operands['distinct'], ctx, **kwargs)
                                else:
                                    expr = self.parse_expression(operands['distinct'], ctx.groupby_ctx, **kwargs)
                                if isinstance(expr, list):
                                    # attributes = FPairAttribute(self.scope, attributes, prefix=ctx.prev_database.name)
                                    raise NotImplementedError(f"COUNT EXPRs `{expr}` is not supported.")
                                elif isinstance(expr, FNull):
                                    return expr
                            return FAggCount(self.scope, operator, expr, distinct=True, **kwargs)
                        else:
                            if isinstance(operands, list):
                                expr = []
                                for opd in operands:
                                    if ctx.groupby_ctx is None:
                                        opd = self.parse_expression(opd, ctx, **kwargs)
                                    else:
                                        opd = self.parse_expression(opd, ctx, **kwargs)
                                    if isinstance(opd, FNull | ExcutableType | str | AggregationType):
                                        raise SyntaxError(
                                            f'`COUNT({operands})` contains NULL | constants | Aggregations')
                                    expr.append(opd)
                            else:
                                if ctx.groupby_ctx is None:
                                    expr = self.parse_expression(operands, ctx, **kwargs)
                                else:
                                    expr = self.parse_expression(operands, ctx.groupby_ctx, **kwargs)
                                if isinstance(expr, FNull):
                                    return expr
                                elif isinstance(expr, AggregationType):
                                    raise SyntaxError(
                                        f"MySQL does not support agg-nested-agg functions: COUNT({operands})")
                            return FAggCount(self.scope, operator, expr, **kwargs)
                case 'max':
                    return self._parse_agg_expr(FAggMax, operator, operands, ctx, **kwargs)
                case 'min':
                    return self._parse_agg_expr(FAggMin, operator, operands, ctx, **kwargs)
                case 'avg':
                    return self._parse_agg_expr(FAggAvg, operator, operands, ctx, **kwargs)
                case 'sum':
                    return self._parse_agg_expr(FAggSum, operator, operands, ctx, **kwargs)
                case 'bool_and':
                    return self._parse_agg_expr(FBoolAnd, operator, operands, ctx, **kwargs)
                case 'bool_or':
                    return self._parse_agg_expr(FBoolOr, operator, operands, ctx, **kwargs)
                case 'stddev_pop':
                    # return self._parse_agg_expr(FStddevPop, operator, operands, ctx, **kwargs)
                    raise NotSupportedError('`stddev_pop` might bring unknown.')
                case 'var_pop':
                    # return self._parse_agg_expr(FVarPop, operator, operands, ctx, **kwargs)
                    raise NotSupportedError('`var_pop` might bring unknown.')
                case 'stddev_samp':
                    # return self._parse_agg_expr(FStddevSamp, operator, operands, ctx, **kwargs)
                    raise NotSupportedError('`stddev_samp` might bring unknown.')
                case 'var_samp':
                    # return self._parse_agg_expr(FVarSamp, operator, operands, ctx, **kwargs)
                    raise NotSupportedError('`stddev_samp` might bring unknown.')
                case 'power':
                    expr = [self.parse_expression(opd, ctx, **kwargs) for opd in operands]
                    return FPowerPredicate(*expr)
                case 'in':
                    attributes = self.parse_expression(operands[0], ctx, **kwargs)
                    if not isinstance(attributes, list):
                        attributes = [attributes]
                    if isinstance(operands[1], dict) and len(operands[1]) == 1 and \
                            'literal' in operands[1] and isinstance(operands[1]['literal'], list):
                        operands[1] = [{'literal': v} for v in operands[1]['literal']]
                    if self.is_nested_query(operands[1], **kwargs):
                        try:
                            # correlated_subquery_ctx = self.analyze(copy(operands[1]), outer_ctx=ctx)
                            correlated_subquery_ctx = self.analyze(operands[1], outer_ctx=ctx, groupby_fuzzy=True)
                            # why fuzzy = true ?
                            # SESSION_ID NOT IN (SELECT SESSION_ID FROM PLAYBACK P JOIN ADS A USING (CUSTOMER_ID) WHERE A.TIMESTAMP BETWEEN START_TIME AND END_TIME GROUP BY CUSTOMER_ID)
                            values = correlated_subquery_ctx.prev_database
                            ctx.is_correlated_subquery = correlated_subquery_ctx.is_correlated_subquery
                        except UnknownColumnError as uc_err:
                            raise CorrelatedQueryError(operands[1])
                        return FInPredicate(attributes, values)
                    else:
                        if not isinstance(operands[1], list):
                            operands[1] = [operands[1]]
                        values = [self.parse_expression(opd, ctx, **kwargs) for opd in operands[1]]
                        if any(not isinstance(v, list) for v in values):
                            values = [[v] for v in values]
                        new_expr = []
                        for attrs, pair in zip(itertools.repeat(attributes), values):
                            new_expr.append(
                                eval_operation(FOperator('and'), [
                                    eval_operation(FOperator('eq'), [attr, value])
                                    for attr, value in zip(attrs, pair)
                                ])
                            )
                        new_expr = eval_operation(FOperator('or'), new_expr)
                        return new_expr
                case 'nin':
                    attributes = self.parse_expression(operands[0], ctx, **kwargs)
                    if not isinstance(attributes, list):
                        attributes = [attributes]
                    if isinstance(operands[1], dict) and len(operands[1]) == 1 and \
                            'literal' in operands[1] and isinstance(operands[1]['literal'], list):
                        operands[1] = [{'literal': v} if isinstance(v, str) else v for v in operands[1]['literal']]
                    if self.is_nested_query(operands[1], **kwargs):
                        try:
                            # correlated_subquery_ctx = self.analyze(copy(operands[1]))
                            correlated_subquery_ctx = self.analyze(operands[1], outer_ctx=ctx, groupby_fuzzy=True)
                            # why fuzzy = true ?
                            # SESSION_ID NOT IN (SELECT SESSION_ID FROM PLAYBACK P JOIN ADS A USING (CUSTOMER_ID) WHERE A.TIMESTAMP BETWEEN START_TIME AND END_TIME GROUP BY CUSTOMER_ID)
                            values = correlated_subquery_ctx.prev_database
                            ctx.is_correlated_subquery = correlated_subquery_ctx.is_correlated_subquery
                        except UnknownColumnError as uc_err:
                            raise CorrelatedQueryError(operands[1])
                        return FNotInPredicate(attributes, values)
                    else:
                        if not isinstance(operands[1], list):
                            operands[1] = [operands[1]]
                        values = [self.parse_expression(opd, ctx, **kwargs) for opd in operands[1]]
                        if any(not isinstance(v, list) for v in values):
                            values = [[v] for v in values]
                        new_expr = []
                        for attrs, pair in zip(itertools.repeat(attributes), values):
                            tmp_expr = [
                                eval_operation(FOperator('eq'), [attr, value])
                                for attr, value in zip(attrs, pair)
                            ]
                            if len(tmp_expr) == 1:
                                new_expr.extend(tmp_expr)
                            else:
                                new_expr.append(eval_operation(FOperator('and'), tmp_expr))
                        if len(new_expr) == 1:
                            return eval_operation(FOperator('not'), new_expr)
                        else:
                            new_expr = eval_operation(FOperator('and'),
                                                      [eval_operation(FOperator('not'), [e]) for e in new_expr])
                        return new_expr
                case 'lt' | 'lte' | 'gt' | 'gte':
                    # A (<|<=, >|>=) expr (<|<=, >|>=) B
                    expr = [self.parse_expression(opd, ctx, **kwargs) for opd in operands]
                    if isinstance(operands[0], Dict) and len(operands[0]) > 0:
                        inner_operator = list(operands[0])[0]
                        if all(op in {'lt', 'lte'} for op in (inner_operator, operator)) or \
                                all(op in {'gt', 'gte'} for op in (inner_operator, operator)):
                            expr = eval_operation(FOperator(operator), [expr[0][-1], expr[-1]])
                            return eval_operation(FOperator('and'), [expr[0], expr])
                    return eval_operation(FOperator(operator), expr)
                case 'timestampdiff':
                    if operands[0] != 'DAY':
                        raise NotSupportedError(f"TIMESTAMPDIFF only support DAY, not MONTH and YEAR. {expr}")
                    else:
                        operands = [self.parse_expression(opd, ctx, **kwargs) for opd in operands[1:]]
                        return eval_operation(FOperator('sub'), operands[::-1])
                case 'cast':
                    # CAST(expr, BOOLEAN) => expr != 0
                    if operands[1] == {'boolean': {}} or operands[1] == 'BOOLEAN':
                        # CAST(1, BOOLEAN)
                        return self.parse_expression({'neq': [operands[0], 0]}, ctx, **kwargs)
                    elif 'decimal' in operands[1]:
                        expression = self.parse_expression(operands[0], ctx, **kwargs)
                        if len(operands[1]['decimal']) > 0:
                            expression.uninterpreted_func = FRound(operands[1]['decimal'][-1])
                        return expression
                    elif operands[0] == {'null': None}:
                        return FNull()
                    elif operands[1] == {'date': {}}:
                        return self.parse_expression(operands[0], ctx, **kwargs)
                    else:
                        if isinstance(operands[0], dict) and len(operands[0]) == 2 and \
                                'filter' in operands[0] and 'value' in operands[0]:
                            # {'value': {'count': 'DEPTNO'}, 'filter': {'gt': ['DEPTNO', 10]}}
                            filter_cond = self.parse_expression(operands[0]['filter'], ctx, **kwargs)
                            # _filter_cond = kwargs.pop('filter_cond')
                            _filter_cond = kwargs.pop('filter_cond')
                            expr = [self.parse_expression(operands[0]['value'], ctx, filter_cond=filter_cond, **kwargs)]
                            kwargs['filter_cond'] = _filter_cond
                            expr.append(self.parse_expression(operands[1], ctx, **kwargs))
                        else:
                            expr = [self.parse_expression(opd, ctx, **kwargs) for opd in operands]
                        if isinstance(expr[1], FInteger | FNumeric | FFloat | FDouble):
                            return expr[0]
                        return FCast(*expr)
                case 'integer' | 'bigint':
                    return FInteger()
                case 'numeric':
                    return FNumeric()
                case 'boolean':
                    return FBoolean()
                case 'float':
                    return FFloat()
                case 'double' | 'double_precision':
                    return FDouble()
                # case 'time':
                #     expr = self.parse_expression(operands, ctx, **kwargs)
                #     expr.uninterpreted_func = FTime()
                #     return expr
                case 'date':
                    if isinstance(operands, dict) and len(operands) == 1:
                        if 'literal' in operands:
                            # PSQL: only support (DATE '2022-01-01')
                            return FDigits(utils.strptime_to_int(operands['literal']))
                        elif 'date' in operands:
                            # DATE('2022-01-01')
                            return FDigits(utils.strptime_to_int(operands['date']))
                        elif 'add' in operands:
                            # DATE(MIN(EVENT_DATE) + 1)
                            operands = self.parse_expression(operands['add'], ctx, **kwargs)
                            return eval_operation(FOperator('add'), operands)
                        elif 'sub' in operands:
                            # DATE('2019-07-27' -INTERVAL 29 DAY)
                            operands = self.parse_expression(operands['sub'], ctx, **kwargs)
                            return eval_operation(FOperator('sub'), operands)
                        else:
                            raise NotSupportedError(expr)
                    elif isinstance(operands, str):
                        attributes = self._find_attributes(operands, ctx.attributes)
                        if len(attributes) > 0:
                            return attributes[0]
                        else:
                            return FDigits(utils.strptime_to_int(operands))
                    else:
                        raise NotSupportedError(expr)
                case 'str_to_date' | 'date_format':
                    if isinstance(operands[0], dict) and len(operands[0]) == 1 and 'date' in operands[0]:
                        format = operands[1]['literal']
                        format = re.findall(r'[a-zA-Z]', format)
                        if format == ['Y', 'M', 'D']:
                            date = self.parse_expression(operands[0], ctx, **kwargs)
                            return date
                        else:
                            raise NotSupportedError(f'Not supported DATE format: {operands[1]["literal"]}')
                    else:
                        raise NotImplementedError(expr)
                # case  'timestamp':
                #     return FTimestamp(operands)
                # case  'decimal':
                #     return FDecimal(*operands)
                # case  'varchar':
                #     return FVarchar(operands)
                # case  'upper':
                #     return FUpper(self.parse_expression(operands, ctx, **kwargs))
                # case  'to_days':
                #     if isinstance(operands, dict) and 'literal' in operands:
                #         # since we do not support DATE type
                #         # YYYY-MM-DD (HH:mm:SS)
                #         day = operands['literal']
                #         if str.startswith(day, 'String_'):
                #             day = day[7:]
                #         day = day.strip().split(' ')[0]
                #         day = day.split('_')[-1]
                #         try:
                #             day = int(day)
                #         except:
                #             raise SyntaxError(f"error time stamp format: `{expr}`")
                #         return FDigits(day)
                #     else:
                #         raise NotSupportedError("We only support `TO_DAYS` for string.")
                case 'add' | 'sub' | 'and' | 'or':
                    if isinstance(operands, str | NumericType) or \
                            (isinstance(operands, dict) and len(operands) == 1):
                        operands = [operands]
                    operands = [self.parse_expression(0 if is_literal(opd) else opd, ctx, **kwargs) for opd in operands]
                    return eval_operation(FOperator(operator), operands)
                case 'neq' | 'eq':
                    # NAME IS TRUE => {'eq': ['NAME', True]}
                    # NAME IS NOT TRUE => {'neq': ['NAME', True]}
                    # NAME IS FALSE => {'eq': ['NAME', False]}
                    # NAME IS NOT FALSE => {'neq': ['NAME', FALSE]}
                    if operator == 'eq' and operands[-1] == IS_TRUE:
                        return FIsTruePredicate(self.parse_expression(operands[0], ctx, **kwargs))
                    elif operator == 'eq' and operands[-1] == IS_FALSE:
                        return FIsFalsePredicate(self.parse_expression(operands[0], ctx, **kwargs))
                    elif operator == 'neq' and operands[-1] == IS_TRUE:
                        return FIsNotTruePredicate(self.parse_expression(operands[0], ctx, **kwargs))
                    elif operator == 'neq' and operands[-1] == IS_FALSE:
                        return FIsNotFalsePredicate(self.parse_expression(operands[0], ctx, **kwargs))

                    # string =/!= 1 <=> 0 =/!= 1
                    if (is_literal(operands[0]) and isinstance(operands[1], ExcutableType)):
                        return self.parse_expression(FOperator(operator)(0, operands[1]), ctx, **kwargs)
                    if (is_literal(operands[1]) and isinstance(operands[0], ExcutableType)):
                        return self.parse_expression(FOperator(operator)(operands[0], 0), ctx, **kwargs)
                    if isinstance(operands, str | NumericType) or \
                            (isinstance(operands, dict) and len(operands) == 1):
                        operands = [operands]
                    # lhs_nested_query, rhs_nested_query = [self.is_nested_query(opd, **kwargs) for opd in operands]
                    operands = [self.parse_expression(opd, ctx, **kwargs) for opd in operands]
                    # if lhs_nested_query:
                    #     if len(operands[0].attributes) != 1:
                    #         raise NotSupportedError('(A, B, ...) = XX')
                    # if rhs_nested_query:
                    #     if len(operands[1].attributes) != 1:
                    #         raise NotSupportedError('XX = (A, B, ...)')
                    if all(isinstance(opd, list) for opd in operands):
                        tmp = [eval_operation(FOperator('eq'), list(opds)) for opds in zip(*operands)]
                        operands = eval_operation(FOperator('and'), tmp)
                        if operator == 'neq':
                            operands = FExpression(FOperator('not'), operands)
                    else:
                        operands = eval_operation(FOperator(operator), operands)
                    return operands
                case 'not':
                    if is_literal(operands):
                        return self.parse_expression(1, ctx, **kwargs)
                    elif isinstance(operands, bool):  # NOT False
                        return self.parse_expression(not operands, ctx, **kwargs)
                    elif isinstance(operands, NumericType):  # NOT 0
                        return self.parse_expression(operands != 0, ctx, **kwargs)
                    elif (isinstance(operands, dict) and len(operands) == 1):
                        operands = [self.parse_expression(operands, ctx, **kwargs)]
                    else:
                        operands = [self.parse_expression(opd, ctx, **kwargs) for opd in operands]
                    expr = eval_operation(FOperator(operator), operands)
                    return expr
                case 'mul':
                    if is_literal(operands[0]) or is_literal(operands[1]):
                        return self.parse_expression(0, ctx, **kwargs)
                    else:
                        expr = eval_operation(
                            FOperator(operator),
                            [self.parse_expression(0 if is_literal(opd) else opd, ctx, **kwargs) for opd in operands]
                        )
                        if len(expr) == 2:
                            # only for round *
                            if isinstance(expr[1], FDigits) and utils.is_uninterpreted_func(expr[0]) and \
                                    isinstance(expr[0].uninterpreted_func, FRound):
                                expr[0].uninterpreted_func[1] -= math.log10(expr[1].value)  # decimals
                                expr.uninterpreted_func = expr[0].uninterpreted_func
                                expr[0].uninterpreted_func = None
                            if isinstance(expr[0], FDigits) and utils.is_uninterpreted_func(expr[1]) and \
                                    isinstance(expr[1].uninterpreted_func, FRound):
                                expr[1].uninterpreted_func[1] -= math.log10(expr[0].value)
                                expr.uninterpreted_func = expr[1].uninterpreted_func
                                expr[1].uninterpreted_func = None
                        return expr
                case 'div':
                    if is_literal(operands[0]):
                        return self.parse_expression(0, ctx, **kwargs)
                    elif is_literal(operands[1]):
                        return FNull()
                    else:
                        expr = eval_operation(FOperator(operator),
                                              [self.parse_expression(opd, ctx, **kwargs) for opd in operands])
                        if len(expr) == 2:
                            # only for round /
                            if isinstance(expr[1], FDigits) and isinstance(expr[0].uninterpreted_func, FRound):
                                expr[0].uninterpreted_func[1] += math.log10(expr[1].value)  # decimals
                                expr.uninterpreted_func = expr[0].uninterpreted_func
                                expr[0].uninterpreted_func = None
                            if isinstance(expr[0], FDigits) and isinstance(expr[1].uninterpreted_func, FRound):
                                expr[1].uninterpreted_func[1] += math.log10(expr[0].value)
                                expr.uninterpreted_func = expr[1].uninterpreted_func
                                expr[1].uninterpreted_func = None
                        return expr
                case 'abs':
                    if is_literal(operands):
                        return self.parse_expression(0, ctx, **kwargs)
                    else:
                        return FAbsPredicate(self.parse_expression(operands, ctx, **kwargs))
                case 'ne!':
                    return FExpression(FOperator('ne!'),
                                       [self.parse_expression(opd, ctx, **kwargs) for opd in operands])
                case 'eq!':
                    return FExpression(FOperator('eq!'),
                                       [self.parse_expression(opd, ctx, **kwargs) for opd in operands])
                case 'any_value' | 'first_value':
                    # return FAnyValuePredicate(self.parse_expression(operands, ctx))
                    # return FFirstValuePredicate(self.parse_expression(operands, ctx))
                    return self.parse_expression(operands, ctx, **kwargs)
                case 'last_value':
                    return FLastValuePredicate(self.parse_expression(operands, ctx, **kwargs))
                case 'mod':
                    if is_literal(operands[0]):
                        return self.parse_expression(0, ctx, **kwargs)
                    else:
                        return FModPredicate(*[self.parse_expression(opd, ctx, **kwargs) for opd in operands])
                case 'date_add' | 'adddate':
                    operands = [self.parse_expression(opd, ctx, **kwargs) for opd in operands]
                    return eval_operation(FOperator('add'), operands)
                case 'date_sub' | 'subdate' | 'datediff':
                    operands = [self.parse_expression(opd, ctx, **kwargs) for opd in operands]
                    return eval_operation(FOperator('sub'), operands)
                case 'interval':
                    if operands[1] == 'day':
                        return self.parse_expression(operands[0], ctx, **kwargs)
                    else:
                        raise NotSupportedError("we only support the DAY interval.")
                # -------------- Literature benchmark's symbolic predicates -------------- #
                case 'b' | 'b0' | 'b1' | 'b2':
                    if isinstance(operands, ExcutableType | str):
                        operands = [operands]
                    kwargs['temporary_function'] = True
                    operands = [self.parse_expression(opd, ctx, **kwargs) for opd in operands]
                    return FSymbolicFunc(operator, operands)
                # -------------- Literature benchmark's symbolic predicates -------------- #
                case _:
                    raise NotImplementedError(expr)
        elif isinstance(expr, Sequence):
            return [self.parse_expression(c, ctx, **kwargs) for c in expr]
        else:
            raise NotImplementedError(expr)

    ############################ with ############################

    def parse_with_clause(self, with_clause, ctx: Context):
        tables = []
        for clause in with_clause:
            # tmp_ctx = self.analyze(clause.pop('value'), with_databases=ctx.with_databases)
            tmp_ctx = self.analyze(clause['value'], with_databases=ctx.with_databases)
            src_table = tmp_ctx.prev_database
            if isinstance(clause['name'], str):
                # alias_table = clause.pop('name')
                alias_table = clause['name']
                alias_names = None
            elif isinstance(clause['name'], dict):
                # c = clause.pop('name')
                c = clause['name']
                alias_table = list(c)[0]
                alias_names = c[alias_table]
                if isinstance(alias_names, str):
                    alias_names = [alias_names]
            else:
                raise NotImplementedError

            if alias_names is None:
                condition = self._get_alias_condition(src_table.attributes, alias_table)
            else:
                dst_attributes = []
                for idx, (attr, alias_name) in enumerate(zip(src_table.attributes, alias_names)):
                    dst_attributes.append(attr.update_alias(self.scope, alias_table, alias_name))
                # dst_attributes = deepcopy(src_table.attributes)
                # for attr, alias_attr in zip(dst_attributes, alias_names):
                #     attr.prefix = alias_table
                #     attr.value = alias_attr
                condition = [src_table.attributes, dst_attributes]
            dst_table = FAliasTable(self.scope, src_table, condition=condition, name=alias_table)
            ctx.update_with_clause([dst_table])
            if dst_table.name in self.scope.base_databases:
                self.scope.base_databases[f'{dst_table.name}{BACKUP_SUFFIX}'] = self.scope.base_databases[
                    dst_table.name]
            self.scope.base_databases[dst_table.name] = dst_table  # register as base table
            # clear intermediate tables
            pop_tables = [name for name, table in self.scope.databases.items()
                          if type(table) is not FBaseTable and name not in ctx.with_clause]
            for table in pop_tables:
                self.scope.databases.pop(table)
            self.scope.databases[dst_table.name] = dst_table
            tables.append(dst_table)
        return tables

    ############################ filter(where) ############################

    def parse_case_condition_in_where_clause(self, cond, ctx, **kwargs):
        # swap_func = kwargs.get('swap_func', None)  # swap function from `JOIN ON`
        cond = self.parse_expression(cond, ctx)
        if cond is not None and not isinstance(cond, FExpression | ExcutableType):
            cond = FIsTruePredicate(cond)

        rewritten_conds = linearize_case(cond)
        if cond == rewritten_conds:
            return cond
        else:
            if isinstance(cond, FCasePredicate):
                for idx, cond in enumerate(rewritten_conds):
                    rewritten_conds[idx] = FExpression(FOperator('and'), list(cond))
            if isinstance(rewritten_conds, FExpression | NumericType | bool | FDigits):
                rewritten_conds = [rewritten_conds]
            filtered_conds = []
            for cond in rewritten_conds:
                if isinstance(cond, FNull) or is_false(cond):
                    continue
                elif is_true(cond):
                    filtered_conds.append(cond)
                else:
                    cond = _refine_expression(cond)
                    if isinstance(cond, FNull) or is_false(cond):
                        continue
                    else:
                        filtered_conds.append(cond)
            return filtered_conds

    def parse_where_clause(self, cond: Optional[PredicateType], ctx: Context) -> TableType:
        if cond == False:  # WHERE FALSE
            # table = FEmptyTable(self.scope, attributes=ctx.attributes)
            table = FFilterTable(self.scope, ctx.prev_database, False)
        elif cond is None:
            table = ctx.prev_database
        else:
            conds = self.parse_case_condition_in_where_clause(cond, ctx)
            if isinstance(conds, list):
                tables = []
                for cond in conds:
                    if cond == True:
                        table = ctx.prev_database
                    else:
                        table = FFilterTable(self.scope, ctx.prev_database, cond)
                    tables.append(table)
            else:
                tables = [FFilterTable(self.scope, ctx.prev_database, conds, ctx.is_correlated_subquery)]
            if len(tables) == 0:
                table = FEmptyTable(self.scope, attributes=ctx.attributes)
            elif len(tables) == 1:
                table = tables[0]
            else:
                table = FUnionAllTable(self.scope, tables)
        ctx.update_where_clause(table)
        return table

    ############################ projection ############################

    def _find_select_expressions(self, selected_attrs, ctx: Context, auto_alias=False, filter_cond=None,
                                 **kwargs) -> Sequence:
        if isinstance(selected_attrs, dict):
            alias_flag = self._is_alias(selected_attrs)
            if 'over' in selected_attrs:
                raise NotSupportedError('OVER')
            if selected_attrs.get('value', False):
                if 'filter' in selected_attrs:
                    filter_cond = self.parse_expression(selected_attrs['filter'], ctx)
                else:
                    filter_cond = None
                attributes = self._find_select_expressions(selected_attrs['value'], ctx, filter_cond=filter_cond)
            else:
                attributes = [self.parse_expression(selected_attrs, ctx, filter_cond=filter_cond,
                                                    select_block=kwargs.get('select_block', False))]

            if alias_flag or isinstance(attributes[0], ArithRef | FDigits):
                if utils.is_uninterpreted_func(attributes[0]):
                    attributes[0] = attributes[0].update_alias(
                        self.scope, ctx.prev_database.name, selected_attrs['name']
                    )
                elif isinstance(attributes[0], FAttribute):
                    attributes[0] = attributes[0].update_alias(
                        self.scope, ctx.prev_database.name, selected_attrs['name'],
                    )
                elif isinstance(attributes[0], AggregationType | FExpression | FNull):
                    attributes[0] = attributes[0].update_alias(
                        self.scope,
                        alias_prefix=ctx.prev_database.name,
                        alias_name=selected_attrs['name'],
                    )
                elif isinstance(attributes[0], ArithRef | FDigits):
                    attr = self.scope.declare_attribute(
                        name=ctx.prev_database.name,
                        literal=selected_attrs.get('name', f'ATTR_{attributes[0]}'),
                        _uuid=utils.uuid_hash(),
                    )
                    if isinstance(attributes[0], ArithRef):
                        _const_ = deepcopy(attributes[0])
                    elif isinstance(attributes[0], FDigits):
                        _const_ = IntVal(str(attributes[0].value)) if isinstance(attributes[0].value, int) \
                            else RealVal(str(attributes[0].value))
                    else:
                        raise NotImplementedError(str(attributes[0]))
                    attr.NULL = IntermFunc(
                        z3_function=lambda *args, **kwargs: Z3_FALSE,
                        description="False",
                    )
                    attr.VALUE = IntermFunc(
                        z3_function=lambda *args, **kwargs: _const_,
                        description=str(_const_),
                    )
                    attr.EXPR = _const_  # 10 AS EMP.EMPNO, if comment this line, we cannot get a correct script
                    attr.EXPR_CALL = lambda *args, **kwargs: _const_
                    attributes = [attr]
                elif isinstance(attributes[0], FBaseTable):
                    raise NotSupportedError("Subquery in select clause is not allowed.")
                else:
                    raise UnknownColumnError(attributes[0])
                # register attributes into the caches
                # self.scope._caches[selected_attrs['name']] = attributes[0]

        elif isinstance(selected_attrs, list):
            attributes = list(itertools.chain(*[
                self._find_select_expressions(attr, ctx) for attr in selected_attrs
            ]))
        elif isinstance(selected_attrs, str):
            if selected_attrs == '*':
                attributes = ctx.attributes
                if ctx.right_outer_table:
                    attributes = attributes[::-1]
            elif selected_attrs[-1] == '*':
                table_name = selected_attrs[:selected_attrs.find('__')]
                attributes = [attr for attr in ctx.attributes if attr.prefix == table_name]
                if ctx.right_outer_table:
                    attributes = attributes[::-1]
            elif selected_attrs == 'CURRENT_TIMESTAMP':
                attributes = [FDigits(utils.strptime_to_int(now()))]
            elif isinstance(ctx, GroupbyContext):
                # only works for HAVING
                attributes = self._find_attributes(selected_attrs, ctx.attributes)
                if attributes[0].EXPR is not None:
                    attributes = [attributes[0].EXPR]
                if len(attributes) == 0:
                    raise UnknownColumnError(f'Unknown attribute {selected_attrs}')
            else:
                if isinstance(ctx.prev_database, FEmptyTable):
                    if ctx.attributes is None:
                        raise SyntaxError(f'The attribute of `{selected_attrs}` is not in an EMPTY table')
                    attributes = self._find_attributes(selected_attrs, ctx.attributes, shadow_copy=True)
                    if len(attributes) == 0:
                        # use alias attributes from select clause in groupby/having/orderby
                        if ctx.select_clause is None:
                            raise SyntaxError(f'Unknown attribute {selected_attrs}')
                        attributes = self._find_attributes(selected_attrs, ctx.select_clause)
                # elif ctx.attributes is None and ctx.groupby_ctx is not None:
                #     attributes = self._find_attributes(selected_attrs, ctx.groupby_ctx.attributes, shadow_copy=True)
                #     if len(attributes) == 0:
                #         raise UnknownColumnError(f'Unknown attribute {selected_attrs}')
                elif len(ctx.attributes) == 0:
                    # attributes = []
                    # _selected_attrs = str.split(selected_attrs, '__', 1)[-1]
                    # for attr in self.scope.attributes.values():
                    #     if attr == _selected_attrs:
                    #         attributes.append(attr)
                    # assert len(attributes) > 0, NotImplementedError(f'Cannot find an attributes of {selected_attrs}')
                    # attributes = attributes[:1]  # only select the first one
                    raise UnknownColumnError(f'Unknown attribute {selected_attrs}')
                else:
                    # try to find attribute in FROM/SELECT/GROUP-BY
                    attributes = self._find_attributes(selected_attrs, ctx.attributes, shadow_copy=True, ctx=ctx)
                    if len(attributes) == 0 and 'outer_attrs' in kwargs:
                        # use alias attributes from select clause in groupby/having/orderby
                        for outer_attrs in kwargs['outer_attrs']:
                            attributes = self._find_attributes(selected_attrs, outer_attrs)
                            if len(attributes) > 0:
                                break
                    # cannot find in current context, if we can find it in outer context, raise Correlated Subquery
                    if len(attributes) == 0:
                        if ctx.outer_ctx is not None:
                            # correlated subquery
                            attributes = self._find_attributes(selected_attrs, ctx.outer_ctx.attributes,
                                                               shadow_copy=True)
                            # if len(attributes) != 0:
                            #     raise CorrelatedQueryError(selected_attrs)
                            if len(attributes) > 1:
                                raise UnknownError(f"find {len(attributes)} attributes")
                            ctx.is_correlated_subquery = True
                            return attributes
                        else:
                            # still cannot find such attribute
                            if len(attributes) == 0:
                                raise UnknownColumnError(f'Unknown attribute {selected_attrs}')
                                # attributes = self._find_attributes(selected_attrs, ctx.select_clause)
        elif isinstance(selected_attrs, NumericType):
            attributes = [self.parse_expression(selected_attrs, ctx)]
        else:
            raise NotImplementedError
        if auto_alias:
            # alias expressions in select clauses
            def _alias(attributes):
                for idx, attr in enumerate(attributes):
                    # we only alias expression including 1) Aggregations functions with nested expression, 2) expression, 3) expression in uninterpreted functions
                    if isinstance(attr, AggregationType | FExpression | FDigits | FNull):
                        attributes[idx] = attr.update_alias(
                            self.scope,
                            alias_prefix='' if ctx.prev_database is None else ctx.prev_database.name,
                            alias_name=str(attr),
                        )
                return attributes

            attributes = _alias(attributes)
        if 'bound_scope' in kwargs:
            # for ON condition
            attributes = [self.scope.visitor.visit(attr)(kwargs['bound_scope'][str(attr)]) for attr in attributes]
        return attributes

    def _is_fake_projection(self, table, dst_attributes):
        # all pure attribute
        return (not isinstance(table, FGroupByTable)) and \
            not (isinstance(table, FOrderByTable) and isinstance(table.fathers[0], FGroupByTable)) and \
            all(not attr.require_tuples and attr.EXPR is None for attr in dst_attributes)

    def parse_select_clause(self, selected_clause: Any, ctx: Context, DISTINCT: bool = False) -> TableType:
        if isinstance(ctx.prev_database, FStackTable):
            tables = []
            for sub_table in ctx.prev_database.fathers:
                condition = [sub_table.attributes, selected_clause]
                if self._is_fake_projection(sub_table, selected_clause):
                    table = FFakeProjectionTable(self.scope, sub_table, condition, ctx.is_correlated_subquery)
                else:
                    table = FProjectionTable(self.scope, sub_table, condition, ctx.is_correlated_subquery)
                # table = FProjectionTable(self.scope, sub_table, condition)
                if DISTINCT:
                    table = FDistinctTable(self.scope, table, condition, ctx.is_correlated_subquery)
                tables.append(table)
            table = FUnionAllTable(self.scope, tables)
        else:
            condition = [ctx.attributes, selected_clause]
            if self._is_fake_projection(ctx.prev_database, selected_clause):
                table = FFakeProjectionTable(self.scope, ctx.prev_database, condition, ctx.is_correlated_subquery)
            else:
                table = FProjectionTable(self.scope, ctx.prev_database, condition, ctx.is_correlated_subquery)
            # table = FProjectionTable(self.scope, ctx.prev_database, condition)
            if DISTINCT:
                table = FDistinctTable(self.scope, table, condition, ctx.is_correlated_subquery)
                # ctx.update_select_clause(table)
        ctx.update_select_clause(table)
        LOGGER.debug(table)
        return table

    ############################ group by ############################

    def _linear_case_groupby(self, groupby_clause, select_clause):
        # if GROUB-BY includes CASE, we need distribute cases
        # condition, key
        groupby_keys = []
        for clause in groupby_clause:
            if isinstance(clause, FCasePredicate):
                conds, exprs = clause.when_clauses, clause.then_clauses
                if len(conds) == 1:
                    # Not(cond) or cond is NULL
                    else_cond = FExpression(FOperator('not'), copy(conds))
                    else_cond = FIsNullOrHoldPredicate(else_cond)
                else:
                    else_cond = FExpression(FOperator('not'), [FExpression(FOperator('or'), copy(conds))])
                    else_cond = FIsNullOrHoldPredicate(else_cond)
                conds.append(else_cond)
                exprs.append(clause.else_clause)
                for idx, expr in enumerate(exprs):
                    if isinstance(expr, FDigits):
                        if expr.value > len(select_clause):
                            raise SyntaxError(f'Group-by sugar index `{expr.value}` is out-of-index.')
                        else:
                            exprs[idx] = select_clause[expr.value - 1]
                groupby_keys.append(list(zip(conds, exprs)))
            else:
                groupby_keys.append([(None, clause)])
        groupby_keys = list(itertools.product(*groupby_keys))
        return groupby_keys

    def parse_groupby_clause(self, groupby_clause, select_clause, ctx: Context, groupby_fuzzy=False) -> TableType:
        # we apply groupby, having, orderby, projection together.
        if isinstance(ctx.prev_database, FEmptyTable):
            table = ctx.prev_database
        else:
            groupby_clause = self._linear_case_groupby(groupby_clause, select_clause)
            table = FGroupByTable.build(self.scope, ctx.prev_database, groupby_clause, select_clause,
                                        groupby_fuzzy=groupby_fuzzy)
            if len(table) == 0:
                table = FEmptyTable(self, attributes=ctx.attributes)
        ctx.update_groupby_clause(table)
        return table

    ############################ ORDER BY ############################

    def parse_orderby_clause(self, orderby_clause, limit_clause=None, offset_clause=None, fetch_clause=None,
                             ctx: Context = None) -> TableType:
        if isinstance(ctx.prev_database, FEmptyTable):
            table = ctx.prev_database
        else:
            # ignore CAST in orderby
            order_keys, ascending_list = map(list, zip(*orderby_clause))
            order_keys = list(map(_refine_expression, order_keys))
            table = FOrderByTable(self.scope, ctx.prev_database, order_keys, ascending_list)
            # we should truncate table after ordering, otherwise it will produce wrong tale
            # (limit and offset) and (fetch) cannot co-exist
            # mysql: limit a,b <=> psql: limit b offset a <=> list[a:a+b]
            # psql: fetch = offset
            if (limit_clause is not None) and (offset_clause is None) and (fetch_clause is None):
                if isinstance(limit_clause, list):
                    # mysql
                    limit_a, limit_b = limit_clause[0], limit_clause[0] + limit_clause[1]
                else:
                    # mysql/psql
                    limit_a, limit_b = 0, limit_clause
                table = FLimitTable(self.scope, table, limit_a, limit_b)
            elif (limit_clause is not None) and isinstance(limit_clause, int) and (offset_clause is not None) and \
                    (fetch_clause is None):
                # psql
                limit_a, limit_b = offset_clause, offset_clause + limit_clause
                table = FLimitTable(self.scope, table, limit_a, limit_b)
            elif (limit_clause is None) and (offset_clause is None) and (fetch_clause is not None):
                # psql
                # table = FFetchTable(self.scope, table, fetch_clause)
                limit_a, limit_b = 0, fetch_clause
                table = FLimitTable(self.scope, table, limit_a, limit_b)
            elif (limit_clause is None) and (offset_clause is not None) and (fetch_clause is None):
                limit_a, limit_b = offset_clause, len(table)
                table = FLimitTable(self.scope, table, limit_a, limit_b)
            elif (limit_clause is None) and (offset_clause is None) and (fetch_clause is None):
                pass
            else:
                raise SyntaxError(f"Unknown `{limit_clause}`, `{offset_clause}`, `{fetch_clause}`")
            if len(table) == 0:
                table = FEmptyTable(self.scope, attributes=ctx.attributes)
        ctx.update_orderby_clause(table)
        return table

    ############################ OFFSET ############################
    def parse_slice_clause(self, offset_clause=None, fetch_clause=None, ctx: Context = None) -> TableType:
        if isinstance(ctx.prev_database, FEmptyTable):
            table = ctx.prev_database
        else:
            # we do not just offset the table tuples because it might change BaseTables in schemas
            table = FLimitTable(self.scope, ctx.prev_database, offset_clause, offset_clause + fetch_clause,
                                drop_deleted_tuples=True)
            if len(table) == 0:
                table = FEmptyTable(self.scope, attributes=ctx.attributes)
        ctx.update_slice_clause(table)
        return table

    ############################ UNION/INTERSECT/EXCEPT ############################
    def parse_union_clause(self, union_clauses, union_all=False, ctx=None):
        tables = [self.analyze(clause).prev_database for clause in union_clauses]
        if union_all:
            table = FUnionAllTable(self.scope, tables)
        else:
            table = FUnionTable(self.scope, tables)
        ctx.prev_database = table
        ctx.attributes = table.attributes
        return ctx

    def parse_intersect_clause(self, intersect_clauses, intersect_all=False, ctx=None):
        tables = [self.analyze(clause).prev_database for clause in intersect_clauses]
        if intersect_all:
            table = FIntersectAllTable(self.scope, tables)
        else:
            table = FIntersectTable(self.scope, tables)
        ctx.prev_database = table
        ctx.attributes = table.attributes
        return ctx

    def parse_except_clause(self, except_clauses, except_all=False, ctx=None):
        tables = [self.analyze(clause).prev_database for clause in except_clauses]
        # attributes are the same
        if except_all:
            table = FExceptAllTable(self.scope, tables)
        else:
            table = FExceptTable(self.scope, tables)
        ctx.prev_database = table
        ctx.attributes = table.attributes
        return ctx

    ############################ pipeline of analyze ############################

    def _replace_clause(self, clauses, ctx: Context, group_by=False, having=False, order_by=False, **kwargs):
        if clauses is None:
            return clauses
        if isinstance(clauses, dict) and clauses.get('value', None) == 'GROUPING' and \
                isinstance(clauses.get('name', None), dict) and 'SETS' in clauses['name']:
            # {'value': 'GROUPING', 'name': {'SETS': ['EMPNO', 'DEPTNO']}}
            clauses = clauses['name']['SETS']
        if isinstance(clauses, Dict):
            clauses = [clauses]

        # ignore literal
        for idx, clause in enumerate(clauses):
            if isinstance(clause, dict) and 'value' in clause and \
                    isinstance(clause['value'], dict) and 'literal' in clause['value']:
                clauses[idx] = {'value': clause['value']['literal']}

        # it will ignore ORDER-BY clauses' SORT properties
        parsed_clauses = self.parse_expression(clauses, ctx, **kwargs)

        if group_by:
            clauses = []
            for clause in parsed_clauses:
                if isinstance(clause, AggregationType):
                    # GOURPBY must be pure attributes
                    # raise NotImplementedError(f"Can't group on '{clause}'")
                    raise SyntaxError(f"Can't group on '{clause}'")
                elif (isinstance(clause, FAttribute) and isinstance(clause.EXPR, AggregationType)):
                    # GOURPBY must be pure attributes
                    # raise NotImplementedError(f"Can't group on '{clause.EXPR}'")
                    raise SyntaxError(f"Can't group on '{clause.EXPR}'")
                elif isinstance(clause, FDigits):
                    if clause.value > len(ctx.select_clause):
                        raise SyntaxError(f'Group-by sugar index `{clause.value}` is out-of-index.')
                    else:
                        clause = ctx.select_clause[clause.value - 1]
                        if clause.EXPR is not None:
                            clause = clause.EXPR
                    if clause not in clauses:  # ignore duplicate columns
                        clauses.append(clause)
                else:
                    if clause not in clauses:  # ignore duplicate columns
                        clauses.append(clause)
            for idx, clause in enumerate(clauses):
                clauses[idx] = clause
        elif having:
            def _simplify_having_clause(having_clause):
                from formulas.columns.attribute import FAttribute
                from formulas.expressions.expression import FExpression

                def _f(having_clause):
                    if isinstance(having_clause, FExpression):
                        for idx, operand in enumerate(having_clause):
                            if isinstance(operand, FAttribute) and operand.EXPR is not None:
                                having_clause.operands[idx] = operand.EXPR
                                having_clause.operands[idx].require_tuples = operand.require_tuples
                            else:
                                _f(operand)

                _f(having_clause)
                if having_clause is not None and not isinstance(having_clause, FExpression):
                    if having_clause.EXPR is None:
                        having_clause = FIsTruePredicate(having_clause)
                    else:
                        having_clause = FIsTruePredicate(having_clause.EXPR)
                return having_clause

            if isinstance(parsed_clauses, FAttribute):
                return _simplify_having_clause(parsed_clauses)
            else:
                return _simplify_having_clause(parsed_clauses[0])
        elif order_by:
            new_clauses = []
            for clause, clause_sort in zip(parsed_clauses, clauses):
                if isinstance(clause, FDigits):
                    if ctx.select_clause is None:
                        clause = ctx.attributes[clause.value - 1]
                    else:
                        clause = ctx.select_clause[clause.value - 1]
                new_clauses.append([clause, clause_sort.get('sort', 'asc') == 'asc'])
            clauses = new_clauses
        return clauses

    def create_ctx(self, with_databases=None, outer_ctx: Context = None):
        # for correlated subquery
        ctx = Context(databases=copy(self.scope.base_databases))
        if with_databases is not None:
            ctx.update_with_clause(list(with_databases.values()))
        if outer_ctx is not None:
            ctx.outer_ctx = outer_ctx
            ctx.prev_database = getattr(outer_ctx, 'prev_database', None)
        return ctx

    def is_nested_query(self, query, **kwargs):
        if kwargs.get('select_block', False):
            raise NotSupportedError(f'Query in SELECT')
        return isinstance(query, dict) and (
                any(
                    key in query
                    for key in ['select', 'select_distinct', 'union_all', 'union_distinct', 'union', 'intersect_all',
                                'intersect', 'except_all', 'except']
                ) or (
                    # alias table
                        'value' in query and 'name' in query and self.is_nested_query(query['value'], **kwargs)
                )
        )

    def analyze(self, query, ctx: Context = None, with_databases=None, outer_ctx: Context = None,
                **kwargs) -> TableType:
        if ctx is None:
            ctx = self.create_ctx(with_databases, outer_ctx)
        if isinstance(query, dict):
            # --------- WITH ---------#
            with_flag = False
            if 'with' in query:
                with_flag = True
                # with_clause = query.pop('with')
                with_clause = query['with']
                if isinstance(with_clause, dict):
                    with_clause = [with_clause]
                LOGGER.debug(with_clause)
                self.parse_with_clause(with_clause, ctx)

            if ('select' in query) or ('select_distinct' in query):
                # --------- FROM ---------#
                if 'from' in query:
                    # from_clause = query.pop('from')
                    from_clause = query['from']
                    LOGGER.debug(from_clause)
                    self.parse_from_clause(from_clause, ctx)
                else:
                    raise NotSupportedError("Query must have a FROM clause")
                # --------- WHERE ---------#
                if 'where' in query:  # WHERE FALSE is valid
                    # where_clause = query.pop('where')
                    where_clause = query['where']
                    LOGGER.debug(where_clause)
                    self.parse_where_clause(where_clause, ctx)
                # --------- analyze SELECT ---------#
                # we should analyze SELECT clause here, because of GROUP/ORDER BY clauses could use number to represent their keywords
                # e.g., SELECT *, COUNT(age) FROM EMP ORDER/GROUP BY 2
                distinct_clause = 'select_distinct' in query
                # select_clause_str = (query.pop('select') if query.get('select', False) else None) or \
                #                     (query.pop('select_distinct') if query.get('select_distinct', False) else None)
                select_clause_str = (query['select'] if query.get('select', False) else None) or \
                                    (query['select_distinct'] if query.get('select_distinct', False) else None)
                LOGGER.debug(select_clause_str)
                select_clause = self._find_select_expressions(select_clause_str, ctx, auto_alias=True,
                                                              select_block=True)
                # for SELECT/GROUP/HAVING
                # for clause in select_clause:
                #     clause.require_tuples = require_tuples_func(clause)
                ctx.set_select_clause(select_clause)

                # --------- GROUP BY ---------#
                if 'groupby' in query:
                    # in groupby, it might output many tables
                    # groupby_clause = query.pop('groupby')
                    groupby_clause = query['groupby']
                    if self.scope.environment.dialect == DIALECT.ORACLE and isinstance(groupby_clause, dict):
                        if 'rollup' in groupby_clause:
                            groupby_clause = groupby_clause['rollup']
                        else:
                            raise SyntaxError(f"Unknown grouping operations in Oracle: {groupby_clause}.")
                    groupby_clause = self._replace_clause(groupby_clause, ctx, group_by=True,
                                                          outer_attrs=[select_clause])
                    LOGGER.debug(groupby_clause)
                    self.parse_groupby_clause(
                        groupby_clause,
                        select_clause=ctx.select_clause,
                        ctx=ctx,
                        groupby_fuzzy=kwargs.get('groupby_fuzzy', False),
                    )
                # --------- HAVING without GROUP-BY but treat it as where ---------#
                if 'having' in query:
                    # having_clause = query.pop('having') if query.get('having', False) else None
                    having_clause = query['having']
                    # direct compute AGGREGATION in HAVING
                    if ctx.groupby_clause is None:
                        outer_attrs = [select_clause]
                    else:
                        outer_attrs = [ctx.groupby_clause.attributes, ctx.groupby_clause.out_attributes, select_clause]
                    having_clause = self._replace_clause(having_clause, ctx, having=True, outer_attrs=outer_attrs)
                    # `HAVING SALARY = MAX(SALARY)`
                    if having_clause.require_tuples and isinstance(having_clause, FExpression) and any(
                            getattr(opd, 'require_tuples', None) == False
                            for opd in having_clause
                    ):
                        raise CorrelatedQueryError(query['having'])
                    LOGGER.debug(having_clause)
                    if ctx.groupby_clause is None:
                        self.parse_where_clause(having_clause, ctx)
                    else:
                        ctx.prev_database.update_having_clause(having_clause)
                # --------- ORDER BY ---------#
                if 'orderby' in query and not kwargs.get("skip_orderby", False):
                    # skip_orderby will skip orderby that is not outermost
                    # orderby clause can use both attributes from GROUP-BY and SELECT clause
                    # orderby_clause = query.pop('orderby')
                    orderby_clause = query['orderby']
                    if isinstance(ctx.prev_database, FGroupByTable) and orderby_clause == {'value': SQL_NULL}:
                        # XXX GROUP BY XXX ORDER BY NULL, do nothing
                        pass
                    else:
                        if ctx.groupby_clause is None:
                            outer_attrs = [select_clause]
                        else:
                            # GROUP-BY keys -> SELECT -> 1st attribute in FROM
                            outer_attrs = [
                                ctx.groupby_clause.attributes,
                                select_clause,
                                ctx.groupby_clause.out_attributes,
                            ]
                        orderby_clause = self._replace_clause(orderby_clause, ctx, order_by=True,
                                                              outer_attrs=outer_attrs, select_clause=select_clause)
                        LOGGER.debug(orderby_clause)
                        # if (query.get('limit', None) or query.get('offset', None) or query.get('fetch', None)):
                        #     raise NotSupportedError('limit/offset/fetch')
                        # self.parse_orderby_clause(orderby_clause, None, None, None, ctx)
                        # limit_clause = None if query.get('limit', None) is None else query.pop('limit')
                        # offset_clause = None if query.get('offset', None) is None else query.pop('offset')
                        # fetch_clause = None if query.get('fetch', None) is None else query.pop('fetch')
                        limit_clause = None if query.get('limit', None) is None else query['limit']
                        offset_clause = None if query.get('offset', None) is None else query['offset']
                        fetch_clause = None if query.get('fetch', None) is None else query['fetch']
                        self.parse_orderby_clause(orderby_clause, limit_clause, offset_clause, fetch_clause, ctx)
                # end groupby operation
                if ctx.groupby_clause is not None:
                    # stop groupby context
                    ctx.attributes = ctx.groupby_clause.out_attributes
                    ctx.prev_database.set_attributes(ctx.groupby_clause.out_attributes)
                    ctx.groupby_ctx = ctx.groupby_clause.out_attributes = None
                # --------- PROJECTION ---------#
                if (select_clause_str != '*') or distinct_clause:
                    self.parse_select_clause(ctx.pop_select_clause(), ctx, DISTINCT=distinct_clause)
                if isinstance(ctx.prev_database, FStackTable):
                    ctx.prev_database = FUnionAllTable(self.scope, ctx.prev_database.fathers)
                # drop right outer flag
                ctx.right_outer_table = False
                # --------- OFFSET/FETCH ---------#
                # psql
                if 'offset' in query or 'fetch' in query or 'limit' in query:
                    if 'offset' in query:
                        # offset_clause = query.pop('offset')
                        offset_clause = query['offset']
                    else:
                        offset_clause = 0
                    if 'fetch' in query:
                        # fetch_clause = query.pop('fetch')
                        fetch_clause = query['fetch']
                    else:
                        fetch_clause = len(ctx.prev_database)
                    if 'limit' in query:
                        # limit_clause = query.pop('limit')
                        limit_clause = query['limit']
                        if isinstance(limit_clause, list):
                            offset_clause, fetch_clause = limit_clause
                        else:
                            offset_clause, fetch_clause = 0, limit_clause
                    self.parse_slice_clause(offset_clause, fetch_clause, ctx)

                # clear saved alias info in attributes
                if ctx.prev_database is not None:
                    ctx.prev_database.clear_alias_info()
                # if len(query) > 0:
                #     raise NotImplementedError(query)
            elif 'union_all' in query:
                # union_all_clause = query.pop('union_all')
                union_all_clause = query['union_all']
                LOGGER.debug(union_all_clause)
                self.parse_union_clause(union_all_clause, union_all=True, ctx=ctx)
            elif 'union_distinct' in query:
                # union_distinct_clause = query.pop('union_distinct')
                union_distinct_clause = query['union_distinct']
                LOGGER.debug(union_distinct_clause)
                self.parse_union_clause(union_distinct_clause, union_all=True, ctx=ctx)
            elif 'union' in query:
                # union_clause = query.pop('union')
                union_clause = query['union']
                LOGGER.debug(union_clause)
                self.parse_union_clause(union_clause, union_all=False, ctx=ctx)
            elif 'intersect_all' in query:
                # intersect_all_clause = query.pop('intersect_all')
                intersect_all_clause = query['intersect_all']
                LOGGER.debug(intersect_all_clause)
                self.parse_intersect_clause(intersect_all_clause, intersect_all=True, ctx=ctx)
            elif 'intersect' in query:
                # intersect_clause = query.pop('intersect')
                intersect_clause = query['intersect']
                LOGGER.debug(intersect_clause)
                self.parse_intersect_clause(intersect_clause, intersect_all=False, ctx=ctx)
            elif 'except_all' in query:
                # except_clause = query.pop('except_all')
                except_clause = query['except_all']
                LOGGER.debug(except_clause)
                self.parse_except_clause(except_clause, except_all=True, ctx=ctx)
            elif 'except' in query:
                # except_clause = query.pop('except')
                except_clause = query['except']
                LOGGER.debug(except_clause)
                self.parse_except_clause(except_clause, except_all=False, ctx=ctx)
            elif self._is_alias(query):
                self.parse_from_clause(query, ctx)
            elif 'from' in query:
                # from_clause = query.pop('from')
                from_clause = query['from']
                LOGGER.debug(from_clause)
                self.analyze(from_clause, ctx=ctx)
                # --------- ORDER BY ---------#
                if query.get('orderby', False):
                    # orderby_clause = query.pop('orderby')
                    orderby_clause = query['orderby']
                    orderby_clause = self._replace_clause(orderby_clause, ctx, order_by=True)
                    LOGGER.debug(orderby_clause)
                    # limit_clause = None if query.get('limit', None) is None else query.pop('limit')
                    # offset_clause = None if query.get('offset', None) is None else query.pop('offset')
                    # fetch_clause = None if query.get('fetch', None) is None else query.pop('fetch')
                    limit_clause = None if query.get('limit', None) is None else query['limit']
                    offset_clause = None if query.get('offset', None) is None else query['offset']
                    fetch_clause = None if query.get('fetch', None) is None else query['fetch']
                    self.parse_orderby_clause(orderby_clause, limit_clause, offset_clause, fetch_clause, ctx)
            else:
                raise NotImplementedError(query)
            if with_flag:
                for clause in ctx.with_clause:
                    self.scope.base_databases.pop(clause)
                ctx.clear_with()

                pop_key_pairs = []
                for key in self.scope.base_databases.keys():
                    if str.endswith(key, BACKUP_SUFFIX):
                        pop_key_pairs.append([key[: - len(BACKUP_SUFFIX)], key])
                for pop_key, ori_key in pop_key_pairs:
                    self.scope.base_databases[pop_key] = self.scope.base_databases.pop(ori_key)


        elif isinstance(query, str | dict | ValuesTable):
            self.parse_from_clause(query, ctx)
        elif isinstance(query, FBaseTable):
            ctx.prev_database = query
        # if isinstance(query, Dict) and len(query) > 0:
        #     raise AssertionError(f'There exist some clauses that have not been analyzed, please check them. ({query})')
        else:
            raise NotImplementedError(query)
        return ctx
