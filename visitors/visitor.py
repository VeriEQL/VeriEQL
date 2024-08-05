# -*- coding:utf-8 -*-

import functools
import itertools
from typing import (
    Dict,
    Sequence,
)

from ordered_set import OrderedSet
from z3 import (
    ArithRef,
    FuncDeclRef,
    ExprRef,
    BoolRef,
    ToReal,
    AstRef,
    Function,
    is_bool,
    is_true,
    is_false,
    is_int,
    eq as Z3_EQ,
)

from constants import (
    Z3_NULL_VALUE,
    NumericType,
    Sum,
    Implies,
    If,
    Not,
    And,
    Or,
    Z3_TRUE,
    Z3_FALSE,
    Z3_1,
    Z3_0,
    IntVal,
    BoolVal,
    RealVal,
)
from errors import NotSupportedError
from formulas.columns import *
from formulas.expressions import *
from formulas.tables import *
from formulas.tuples import *
from utils import (
    encode_same,
    encode_equality,
    encode_inequality,
    encode_is_distinct_from,
    encode_is_not_distinct_from,
    simplify,
    encode_concate_by_and,
    encode_concate_by_or,
    is_uninterpreted_func,
    __pos_hash__,
    CodeSnippet
)
from visitors import visitor
from visitors.dump_tuple import DumpTuple
from visitors.interm_function import IntermFunc

ExcutableType = NumericType | FDigits | bool


class Visitor:

    def __init__(self, scope):
        self.scope = scope
        self._DEL = scope.DELETED_FUNCTION
        self.correlated_table_indices = {}

    @visitor(FExpression)
    def visit(self, formulas: FExpression, **outer_kwargs):

        def _f(*args, **kwargs):
            def _application(formulas):
                operands = []
                params = itertools.repeat(args[0]) if len(args) == 1 else args
                for idx, (operand, param) in enumerate(zip(formulas.operands, params)):
                    if is_uninterpreted_func(operand):
                        raise NotImplementedError(
                            f'Do not support Uninterpreted Function `{operand}` in clause which is not projection.')
                    elif isinstance(operand, FAttribute):
                        # AGE - 1
                        if 'first_non_deleted_tuple_sort' in kwargs:
                            param = kwargs['first_non_deleted_tuple_sort']
                        elif isinstance(param, Sequence):
                            param = param[0]
                        attr_tuple = self.visit(operand, **outer_kwargs)(param, **kwargs)
                        operands.append(FExpressionTuple(attr_tuple.NULL, attr_tuple.VALUE))
                    elif getattr(operand, 'require_tuples', False):
                        operands.append(self.visit(operand, **outer_kwargs)(param, **kwargs))
                    # elif isinstance(operand, FSymbolicFunc):
                    #     operands.append(self.visit(operand))
                    # AGE - (AGE - 1)
                    elif isinstance(operand, FExpression | FExpressionTuple):
                        operands.append(self.visit(operand, **outer_kwargs)(*args, **kwargs))
                    elif isinstance(operand, FDigits | FNull):
                        operands.append(self.visit(operand, **outer_kwargs)(None))
                    elif isinstance(operand, FBaseTable):
                        operands.append(self._table_to_value(operand, **kwargs))
                    else:
                        operands.append(FExpressionTuple(Z3_FALSE, operand))

                match formulas.operator:
                    case '∧' | '∨':  # AND, OR
                        for idx, opd in enumerate(operands):
                            if isinstance(opd.VALUE, ArithRef | NumericType):
                                operands[idx].VALUE = opd.VALUE != Z3_0
                        if formulas.operator == '∧':
                            # NULL and false <=> false
                            # other NULL operations <=> NULL
                            return encode_concate_by_and(
                                [opd.NULL for opd in operands], [opd.VALUE for opd in operands]
                            )
                        else:
                            # NULL or true <=> true
                            # other NULL operations <=> NULL
                            return encode_concate_by_or(
                                [opd.NULL for opd in operands], [opd.VALUE for opd in operands]
                            )
                    case '=' | '!=':  # EQ, NEQ
                        if formulas.operator == '=':
                            encode_func = encode_equality
                        else:
                            encode_func = encode_inequality
                        if all(isinstance(opd.VALUE, ArithRef | NumericType) for opd in operands) \
                                or all(isinstance(opd.VALUE, BoolRef | bool) for opd in operands):
                            # all operands are 1) numeric or 2) boolean
                            value_formula = encode_func(*[opd.NULL for opd in operands],
                                                        *[opd.VALUE for opd in operands])
                            return FExpressionTuple(
                                NULL=simplify([opd.NULL for opd in operands], operator=Or),
                                VALUE=value_formula,
                            )
                        else:
                            # otherwise, mixture of numeric and boolean
                            for idx, opd in enumerate(operands):
                                if isinstance(opd.VALUE, ArithRef | NumericType):
                                    operands[idx].VALUE = opd.VALUE != Z3_0
                            return FExpressionTuple(
                                NULL=simplify([opd.NULL for opd in operands], operator=Or),
                                VALUE=encode_func(*[opd.NULL for opd in operands],
                                                  *[opd.VALUE for opd in operands], ),
                            )
                    case '<' | '<=' | '>' | '>=':
                        # boolean operation: opd1 op opd2
                        assert len(operands) == 2, NotImplementedError(formulas.operator, operands)
                        opd1, opd2 = operands
                        if isinstance(opd1, FExpressionTuple) and isinstance(opd2, FExpressionTuple):
                            NULL = Or(opd1.NULL, opd2.NULL)
                            VALUE = formulas.operator(opd1.VALUE, opd2.VALUE)
                        elif isinstance(opd1, FExpressionTuple) and not isinstance(opd2, FExpressionTuple):
                            NULL = opd1.NULL
                            VALUE = And(Not(opd1.NULL), formulas.operator(opd1.VALUE, opd2))
                        elif not isinstance(opd1, FExpressionTuple) and isinstance(opd2, FExpressionTuple):
                            NULL = opd2.NULL
                            VALUE = And(Not(opd2.NULL), formulas.operator(opd1, opd2.VALUE))
                        else:
                            NULL = Z3_FALSE
                            VALUE = formulas.operator(opd1, opd2)
                        return FExpressionTuple(NULL=NULL, VALUE=VALUE)
                    case '+' | '-' | '*' | '/':
                        # numeric operation: (op, opd1, opd2, ...), if one of opds is NULL, then expr is NULL
                        values = [opd.VALUE for opd in operands]
                        if formulas.operator == '/':
                            NULL = simplify([opd.NULL for opd in operands] + [operands[-1].VALUE == Z3_0], operator=Or)
                            for idx, v in enumerate(values):
                                if isinstance(v, AstRef) and v.is_int():
                                    values[idx] = ToReal(v)
                        else:
                            NULL = simplify([opd.NULL for opd in operands], operator=Or)
                        if formulas.operator == '-' and len(values) == 1:
                            # - XX
                            return FExpressionTuple(NULL, -values[0])
                        else:
                            return FExpressionTuple(NULL, functools.reduce(formulas.operator, values))
                    case 'not':
                        if isinstance(operands[0].VALUE, ArithRef | NumericType):
                            # not 1
                            # because of False => 0, True => 1
                            operands[0].VALUE = operands[0].VALUE == Z3_0
                        else:
                            # not age
                            operands[0].VALUE = formulas.operator(operands[0].VALUE)
                        return operands[0]
                    case 'ne!' | 'eq!':
                        if formulas.operator == 'ne!':
                            encode_func = encode_is_not_distinct_from
                        else:
                            encode_func = encode_is_distinct_from
                        if all(isinstance(opd.VALUE, ArithRef | NumericType) for opd in operands) \
                                or all(isinstance(opd.VALUE, BoolRef | bool) for opd in operands):
                            # all operands are 1) numeric or 2) boolean
                            value_formula = encode_func(*[opd.NULL for opd in operands],
                                                        *[opd.VALUE for opd in operands])
                            return FExpressionTuple(NULL=Z3_FALSE, VALUE=value_formula)
                        else:
                            # otherwise, mixture of numeric and boolean
                            for idx, opd in enumerate(operands):
                                if isinstance(opd.VALUE, ArithRef | NumericType):
                                    operands[idx].VALUE = opd.VALUE != Z3_0
                            value_formula = encode_func(*[opd.NULL for opd in operands],
                                                        *[opd.VALUE for opd in operands])
                            return FExpressionTuple(NULL=Z3_FALSE, VALUE=value_formula)
                    case _:
                        # ignore NULL
                        if len(operands) == 1:  # not
                            if formulas.operator == 'not' and isinstance(operands[0], ArithRef | NumericType):
                                # because of False => 0, True => 1
                                return operands[0] == Z3_0
                            else:
                                return formulas.operator(*operands)
                        else:
                            return functools.reduce(formulas.operator, operands)

            return _application(formulas)

        return _f

    def _table_to_value(self, formulas: FBaseTable, **kwargs):
        # we think this table only contains one attribute and one non-deletd tuple:
        if len(formulas.attributes) != 1:
            raise NotImplementedError
        attribute = self.visit(formulas.attributes[0])
        self.visit(formulas)  # to generate table formulas
        tuple_sorts = [tuple.SORT for tuple in formulas]
        constraint = CodeSnippet(
            code=Sum(*[If(self._DEL(t), Z3_0, Z3_1) for t in tuple_sorts]) == Z3_1,
            docstring=f"Constraint of converting a table to variable {formulas.name}.",
            docstring_first=True,
        )
        self.scope.register_formulas(formulas=constraint)
        value_tuple = attribute(tuple_sorts[-1])
        NULL, VALUE = value_tuple.NULL, value_tuple.VALUE
        for idx, curr_tuple in enumerate(tuple_sorts[:-1][::-1]):
            value_tuple = attribute(curr_tuple)
            NULL = If(self._DEL(curr_tuple), NULL, value_tuple.NULL)
            VALUE = If(self._DEL(curr_tuple), VALUE, value_tuple.VALUE)
        return FExpressionTuple(NULL, VALUE)

    ############################ aggregation ############################

    @visitor(FAggCount)
    def visit(self, formula: FAggCount, **kwargs):
        return formula.__expr__

    @visitor(FAggSum)
    def visit(self, formula: FAggSum, **kwargs):
        return formula.__expr__

    @visitor(FAggAvg)
    def visit(self, formula: FAggAvg, **kwargs):
        return formula.__expr__

    @visitor(FAggMax)
    def visit(self, formula: FAggMax, **kwargs):
        return formula.__expr__

    @visitor(FAggMin)
    def visit(self, formula: FAggMin, **kwargs):
        return formula.__expr__

    @visitor(FStddevPop)
    def visit(self, formula: FStddevPop, **kwargs):
        return formula.__expr__

    ############################ table ############################

    @visitor(FBaseTable)
    def visit(self, formulas: FBaseTable, **kwargs) -> Dict:
        table = {tuple.name: self.visit(tuple) for tuple in formulas}
        return table

    @visitor(FAliasTable)
    def visit(self, formulas: FAliasTable, **kwargs) -> Dict:
        prev_table = self.visit(formulas.fathers[0])
        if formulas.alias_attributes:
            curr_table = {}
            for idx, curr_tuple in enumerate(formulas):
                if self.scope.is_register_dump_tuple(curr_tuple.name):
                    curr_tuple = self.scope.get_dump_tuple(curr_tuple.name)
                else:
                    curr_tuple_sort = curr_tuple.SORT
                    prev_tuple = prev_table[curr_tuple.fathers[0]]
                    prev_tuple_sort = prev_tuple.SORT

                    mapping_formulas = []
                    for prev_attr, curr_attr in zip(*curr_tuple.condition):
                        prev_attr, curr_attr = prev_attr(prev_tuple_sort), curr_attr(curr_tuple_sort)
                        mapping_formulas.append(curr_attr == prev_attr)

                    code = And(
                        Implies(
                            Not(self._DEL(prev_tuple_sort)),
                            And(
                                Not(self._DEL(curr_tuple_sort)),
                                *mapping_formulas,
                            )
                        ),
                        Implies(
                            self._DEL(prev_tuple_sort),
                            self._DEL(curr_tuple_sort),
                        ),
                    )
                    implication = CodeSnippet(
                        code=code,
                        docstring=str(curr_tuple),
                        docstring_first=True,
                    )
                    self.scope.register_formulas(formulas=implication)
                    curr_tuple = DumpTuple(
                        name=curr_tuple.name, sort=curr_tuple_sort, attributes=curr_tuple.condition[-1],
                        parent_sorts=prev_tuple,
                    )
                    self.scope.register_dump_tuple(curr_tuple.name, curr_tuple)
                curr_table[curr_tuple.name] = curr_tuple
        else:
            curr_table = prev_table
        return curr_table

    def _product(self, formulas: TableType, use_condition=False, is_using=False, **kwargs) -> Dict:
        if len(formulas.fathers[0]) == 0:
            return formulas.fathers[0]
        if len(formulas.fathers[1]) == 0:
            return formulas.fathers[1]
        left_prev_table, right_prev_table = self.visit(formulas.fathers)
        curr_table = {}
        for idx, curr_tuple in enumerate(formulas):
            if self.scope.is_register_dump_tuple(curr_tuple.name):
                curr_tuple = self.scope.get_dump_tuple(curr_tuple.name)
            else:
                ltuple, rtuple = left_prev_table[curr_tuple.fathers[0]], right_prev_table[curr_tuple.fathers[1]]
                left_prev_tuple_sort, right_prev_tuple_sort = ltuple.SORT, rtuple.SORT
                curr_tuple_sort = curr_tuple.SORT
                curr_attributes = curr_tuple.attributes

                mapping_formulas = [
                    *[
                        curr_attributes[curr_attributes.index(attr)](curr_tuple_sort) == attr(left_prev_tuple_sort)
                        for attr in ltuple.attributes if attr in curr_attributes
                    ],
                    *[
                        curr_attributes[curr_attributes.index(attr)](curr_tuple_sort) == attr(right_prev_tuple_sort)
                        for attr in rtuple.attributes if attr in curr_attributes
                    ],
                ]
                if is_using and formulas._hidden_attributes is not None:
                    mapping_formulas.extend([
                        attr(curr_tuple_sort) == attr(right_prev_tuple_sort)
                        for attr in formulas._hidden_attributes
                    ])

                if use_condition:
                    condition = self.visit(curr_tuple.condition)(left_prev_tuple_sort, right_prev_tuple_sort)
                    if isinstance(condition, FExpressionTuple):
                        condition_premise = And(Not(condition.NULL), condition.VALUE)
                    else:
                        condition_premise = condition
                    premise = And(
                        Not(self._DEL(left_prev_tuple_sort)),
                        Not(self._DEL(right_prev_tuple_sort)),
                        condition_premise,
                    )
                    code = And(
                        Implies(
                            premise,
                            And(
                                Not(self._DEL(curr_tuple_sort)),
                                *mapping_formulas,
                            )
                        ),
                        Implies(
                            Not(premise),
                            self._DEL(curr_tuple_sort),
                        ),
                    )
                    if self.scope._script_writer is None:
                        _code_string = None
                    else:
                        _code_string = ',\n'.join([str(f) for f in mapping_formulas])
                        _code_string = f"""
And(
    Implies(
        {premise},
        And(
            Not({self._DEL(curr_tuple_sort)}),
            {_code_string},
        )
    ),
    Implies(
        Not({premise}),
        {self._DEL(curr_tuple_sort)},
    ),
)
"""
                else:
                    premise = And(
                        Not(self._DEL(left_prev_tuple_sort)),
                        Not(self._DEL(right_prev_tuple_sort)),
                    )
                    code = And(
                        Implies(
                            premise,
                            And(
                                Not(self._DEL(curr_tuple_sort)),
                                *mapping_formulas,
                            )
                        ),
                        Implies(
                            Not(premise),
                            self._DEL(curr_tuple_sort),
                        ),
                    )
                    if self.scope._script_writer is None:
                        _code_string = None
                    else:
                        _code_string = ',\n'.join([str(f) for f in mapping_formulas])
                        _code_string = f"""
And(
    Implies(
        {premise},
        And(
            Not({self._DEL(curr_tuple_sort)}),
            {_code_string},
        )
    ),
    Implies(
        Not({premise}),
        {self._DEL(curr_tuple_sort)},
    ),
)
"""

                implication = CodeSnippet(
                    code=code,
                    docstring=str(curr_tuple),
                    docstring_first=True,
                    code_string=_code_string,
                )
                self.scope.register_formulas(formulas=implication)
                curr_tuple = DumpTuple(
                    name=curr_tuple.name, sort=curr_tuple_sort, attributes=curr_attributes,
                    parent_sorts=[ltuple.name, rtuple.name],
                )
                self.scope.register_dump_tuple(curr_tuple.name, curr_tuple)
            curr_table[curr_tuple.name] = curr_tuple
        return curr_table

    @visitor(FProductTable)
    def visit(self, formulas: FProductTable, **kwargs) -> Dict:
        return self._product(formulas)

    @visitor(FCrossJoinTable)
    def visit(self, formulas: FCrossJoinTable, **kwargs) -> Dict:
        return self._product(formulas, use_condition=formulas[0].condition is not None, is_using=formulas.is_using)

    @visitor(FInnerJoinTable)
    def visit(self, formulas: FInnerJoinTable, **kwargs) -> Dict:
        return self._product(formulas, use_condition=formulas[0].condition is not None, is_using=formulas.is_using)

    @visitor(FNaturalJoinTable)
    def visit(self, formulas: FNaturalJoinTable, **kwargs) -> Dict:
        return self._product(formulas, use_condition=True, is_using=formulas.is_using)

    def _outer_join(self, formulas, using_condition=False, **kwargs):
        # EMPTY table join
        if len(formulas.fathers[0]) == 0:
            return formulas.fathers[0]
        if len(formulas.fathers[1]) == 0:
            return formulas.fathers[1]
        left_prev_table, right_prev_table = self.visit(formulas.fathers)
        if formulas.left_null_tuple is not None:
            left_null_tuple = self.visit(formulas.left_null_tuple)
            left_prev_table[left_null_tuple.name] = left_null_tuple
        if formulas.right_null_tuple is not None:
            right_null_tuple = self.visit(formulas.right_null_tuple)
            right_prev_table[right_null_tuple.name] = right_null_tuple

        curr_table = {}
        for idx, curr_tuple in enumerate(formulas):
            if self.scope.is_register_dump_tuple(curr_tuple.name):
                curr_tuple = self.scope.get_dump_tuple(curr_tuple.name)
            else:
                ltuple, rtuple = left_prev_table[curr_tuple.fathers[0]], right_prev_table[curr_tuple.fathers[1]]
                left_prev_tuple_sort, right_prev_tuple_sort = ltuple.SORT, rtuple.SORT
                curr_tuple_sort = curr_tuple.SORT

                curr_attributes = formulas.attributes
                # assert len(curr_attributes) == len(ltuple.attributes) + len(rtuple.attributes)

                mapping_formulas = [
                    *[
                        curr_attributes[curr_attributes.index(attr)](curr_tuple_sort) == attr(left_prev_tuple_sort)
                        for attr in ltuple.attributes if attr in curr_attributes
                    ],
                    *[
                        curr_attributes[curr_attributes.index(attr)](curr_tuple_sort) == attr(right_prev_tuple_sort)
                        for attr in rtuple.attributes if attr in curr_attributes
                    ],
                ]
                if formulas.is_using and formulas._hidden_attributes is not None:
                    if isinstance(formulas, FRightOuterJoinTable):
                        mapping_formulas.extend([
                            attr(curr_tuple_sort) == attr(left_prev_tuple_sort)
                            for attr in formulas._hidden_attributes
                        ])
                    else:
                        mapping_formulas.extend([
                            attr(curr_tuple_sort) == attr(right_prev_tuple_sort)
                            for attr in formulas._hidden_attributes
                        ])

                # this tuple is not composed of any NULL tuple
                premise = [
                    Not(self._DEL(left_prev_tuple_sort)),
                    Not(self._DEL(right_prev_tuple_sort)),
                ]
                if using_condition:
                    condition = self.visit(curr_tuple.condition)(left_prev_tuple_sort, right_prev_tuple_sort)
                    if is_bool(condition.NULL):
                        if is_true(condition.NULL):
                            condition = Z3_FALSE
                        # elif is_false(condition.NULL):
                        else:
                            condition = condition.VALUE
                    else:
                        condition = If(condition.NULL, Z3_FALSE, condition.VALUE)
                    premise.append(condition)
                    premise = And(*premise)
                    not_premise = Or(self._DEL(left_prev_tuple_sort), self._DEL(right_prev_tuple_sort),
                                     Not(condition))
                else:
                    premise = And(*premise)
                    not_premise = Or(self._DEL(left_prev_tuple_sort), self._DEL(right_prev_tuple_sort))

                code = And(*[
                    Implies(premise, And(Not(self._DEL(curr_tuple_sort)), *mapping_formulas)),
                    Implies(not_premise, self._DEL(curr_tuple_sort)),
                ])

                implication = CodeSnippet(code=code, docstring=str(curr_tuple), docstring_first=True)
                self.scope.register_formulas(formulas=implication)
                curr_tuple = DumpTuple(
                    name=curr_tuple.name, sort=curr_tuple_sort,
                    attributes=curr_attributes[::-1] if isinstance(formulas, FRightOuterJoinTable) else curr_attributes,
                    parent_sorts=[ltuple.name, rtuple.name],
                )
                self.scope.register_dump_tuple(curr_tuple.name, curr_tuple)
            curr_table[curr_tuple.name] = curr_tuple
        return curr_table

    @visitor(FLeftOuterJoinTable)
    def visit(self, formulas: FLeftOuterJoinTable, **kwargs) -> Dict:
        return self._outer_join(formulas, using_condition=formulas[0].condition is not None)

    @visitor(FRightOuterJoinTable)
    def visit(self, formulas: FRightOuterJoinTable, **kwargs) -> Dict:
        return self._outer_join(formulas, using_condition=formulas[0].condition is not None)

    @visitor(FFullOuterJoinTable)
    def visit(self, formulas: FFullOuterJoinTable, **kwargs) -> Dict:
        return self._outer_join(formulas, using_condition=formulas[0].condition is not None)

    @visitor(FFilterTable)
    def visit(self, formulas: FFilterTable, **kwargs) -> Dict:
        prev_table = self.visit(formulas.fathers[0], **kwargs)

        # TODO: handle correlated subquery
        if formulas.is_correlated_subquery:
            prev_outer_attrs = kwargs.get('outer_attrs', {})
            formulas = self.detach_tuples(formulas)

        curr_table = {}
        for prev_tuple, curr_tuple in zip(prev_table.values(), formulas):
            if self.scope.is_register_dump_tuple(curr_tuple.name):
                curr_tuple = self.scope.get_dump_tuple(curr_tuple.name)
            else:
                premise = [Not(self._DEL(prev_tuple.SORT))]
                if isinstance(formulas.fathers[0], FOuterJoinBaseTable) and curr_tuple.condition is None:
                    premise.append(simplify([self._DEL(t) for t in curr_tuple._mutex], operator=And))
                else:
                    # update outer_attrs for WHERE clause which might be nested in a correlated subquery
                    if formulas.is_correlated_subquery:
                        outer_attrs = {k: v for k, v in prev_outer_attrs.items()}
                        for attr in formulas.attributes:
                            outer_attrs[str(attr)] = self.visit(attr)(prev_tuple.SORT)
                        kwargs['outer_attrs'] = outer_attrs

                    filer_cond = self.visit(curr_tuple.condition, **kwargs)(prev_tuple.SORT)
                    if is_int(filer_cond.VALUE):
                        filer_cond.VALUE = BoolVal(not Z3_EQ(filer_cond.VALUE, Z3_0))
                    if is_true(filer_cond.NULL):
                        premise.append(Z3_FALSE)
                    elif is_false(filer_cond.NULL):
                        premise.append(filer_cond.VALUE)
                    else:
                        premise.append(If(filer_cond.NULL, Z3_FALSE, filer_cond.VALUE))

                if self.scope._script_writer is None:
                    _code_string = None
                else:
                    _code_string = ',\n'.join([str(f) for f in premise])
                    _code_string = f'''
And(
    Implies(
        And(*{premise}),
        And(Not({self._DEL(curr_tuple.SORT)}), {curr_tuple.SORT == prev_tuple.SORT}),
    ),
    Implies(Not(And(*{premise})), {self._DEL(curr_tuple.SORT)}),
)
'''

                premise = simplify(premise, operator=And)
                implication = CodeSnippet(
                    code=And(
                        Implies(
                            premise,
                            And(Not(self._DEL(curr_tuple.SORT)), curr_tuple.SORT == prev_tuple.SORT),
                        ),
                        Implies(Not(premise), self._DEL(curr_tuple.SORT)),
                    ),
                    docstring=str(curr_tuple),
                    docstring_first=True,
                    code_string=_code_string,
                )
                self.scope.register_formulas(formulas=implication)
                curr_tuple = DumpTuple(
                    name=curr_tuple.name, sort=curr_tuple.SORT, attributes=prev_tuple.attributes,
                    parent_sorts=prev_tuple.SORT,
                )
                self.scope.register_dump_tuple(curr_tuple.name, curr_tuple)
            curr_table[curr_tuple.name] = curr_tuple
        return curr_table

    @visitor(FProjectionPityTuple)
    def visit(self, curr_tuple: FProjectionPityTuple, **kwargs):
        prev_tuples = kwargs.pop('prev_tuples')
        prev_sorts = [tuple.SORT for tuple in prev_tuples]
        curr_sort = curr_tuple.SORT
        mapping_formulas = []
        for attr in curr_tuple.attributes:
            if is_uninterpreted_func(attr):
                if getattr(attr, 'require_tuples', False):
                    if getattr(attr.EXPR, 'require_tuples', False):
                        formulas = attr.many_to_one_mapping(prev_sorts, curr_sort, **kwargs)
                    else:
                        formulas = self.visit(attr)(curr_sort) == self.visit(attr.EXPR)(prev_sorts, **kwargs)
                else:
                    # pure attribute/expression
                    if isinstance(attr, FAttribute) and isinstance(attr.EXPR, FDigits):
                        inner_expr_tuple = self.visit(attr)(curr_sort, **kwargs)
                        inner_expr_value = inner_expr_tuple.__expr__(curr_sort).VALUE
                        formulas = inner_expr_tuple.VALUE == inner_expr_value
                    else:
                        inner_expr_tuple = self.visit(attr)(curr_sort)
                        formulas = And(inner_expr_tuple.NULL, inner_expr_tuple.VALUE == Z3_NULL_VALUE)
            elif isinstance(attr, FAttribute):
                if getattr(attr, 'require_tuples', False):
                    # contrain agg
                    if getattr(attr.EXPR, 'require_tuples', False):
                        formulas = attr.many_to_one_mapping(prev_sorts, curr_sort, **kwargs)
                    else:
                        formulas = \
                            self.visit(attr)(curr_sort) == self.visit(attr.EXPR)(prev_sorts, **kwargs)
                else:
                    # pure attribute/expression
                    if isinstance(attr, FAttribute) and isinstance(attr.EXPR, FDigits):
                        attr_tuple = self.visit(attr)(curr_sort)
                        attr_value = attr.__expr__(curr_sort).VALUE
                        formulas = attr_tuple.VALUE == attr_value
                    else:
                        attr_tuple = self.visit(attr)(curr_sort)
                        formulas = And(attr_tuple.NULL, attr_tuple.VALUE == Z3_NULL_VALUE)
            else:
                # 'SELECT id, COUNT(*), SUM(EMPNO) FROM EMP WHERE FALSE'
                # raise SyntaxError("An empty table project a vanilla attribute.")
                raise NotImplementedError
            mapping_formulas.append(formulas)

        premise = simplify([self._DEL(tuple) for tuple in prev_sorts], operator=And)
        code = And(
            Implies(premise, And(
                Not(self._DEL(curr_sort)),
                *mapping_formulas,
            )),
            Implies(Not(premise), self._DEL(curr_sort)),
        )
        if self.scope._script_writer is None:
            _code_string = None
        else:
            _code_string = ',\n'.join([str(f) for f in mapping_formulas])
            _code_string = f"""
And(
Implies({premise}, And(
    Not({self._DEL(curr_sort)}),
    {_code_string},
)),
Implies(Not({premise}), {self._DEL(curr_sort)}),
)
"""
        formulas = CodeSnippet(code=code, docstring=str(curr_tuple), docstring_first=True, code_string=_code_string)
        self.scope.register_formulas(formulas)
        curr_tuple = DumpTuple(
            name=curr_tuple.name, sort=curr_sort, attributes=curr_tuple.attributes,
            parent_sorts=prev_tuples,
        )
        self.scope.register_dump_tuple(curr_tuple.name, curr_tuple)
        return curr_tuple

    def _is_lower_bound_attribute(self, attribute, **kwargs):
        return isinstance(attribute, FAggMax) and \
            getattr(attribute.EXPR, 'LOWER_BOUND_INT_SORT', None) is not None

    def _is_upper_bound_attribute(self, attribute, **kwargs):
        return isinstance(attribute, FAggMin) and \
            getattr(attribute.EXPR, 'UPPER_BOUND_INT_SORT', None) is not None

    @visitor(FProjectionTable)
    def visit(self, formulas: FProjectionTable, **kwargs) -> Dict:
        prev_table = self.visit(formulas.fathers[0])
        if formulas.is_correlated_subquery:
            formulas = self.detach_tuples(formulas)
        elif not formulas.is_correlated_subquery and formulas.fathers[0].is_correlated_subquery:
            # attach correlated subquery's tuples to projection
            prev_table = self.attach_tuples(prev_table)
        curr_table = {}

        def _mapping_func(curr_tuple_sort, curr_attributes):
            mapping_formulas, deleted_mapping_formulas = [], []

            def _f(attr, require_tuples_func_flag=False, **kwargs):
                if (attr.EXPR is None) or isinstance(attr.EXPR, FDigits):
                    if not require_tuples_func_flag and len(prev_tuple_sorts) > 1:
                        # one-to-one mapping with 1st non-deleted tuple constraint
                        first_non_deleted_tuple_sort, find_constraint = \
                            self._find_1st_non_deleted_tuple_sort(prev_tuple_sorts)
                        if find_constraint is not None:
                            mapping_formulas.append(find_constraint)
                        # formula = attr.one_to_one_mapping(first_non_deleted_tuple_sort, curr_tuple_sort)
                        formula = attr(curr_tuple_sort) == attr(first_non_deleted_tuple_sort)
                    else:
                        # one-to-one mapping
                        # formula = attr.one_to_one_mapping(prev_tuple_sorts[0], curr_tuple_sort)
                        formula = attr(curr_tuple_sort) == attr(prev_tuple_sorts[0])
                elif (attr in prev_attributes):
                    # avoid alias attribute problem
                    """
                    'SELECT COUNT(*) FROM (SELECT  COUNT(*), EMP0.EMPNO, DEPT0.DEPTNO AS DEPTNO0 FROM EMP AS EMP0 INNER JOIN DEPT AS DEPT0 ON EMP0.DEPTNO = DEPT0.DEPTNO GROUP BY EMP0.EMPNO, DEPT0.DEPTNO) AS t2 GROUP BY t2.EMPNO',
                    'SELECT COUNT(*) FROM EMP AS EMP INNER JOIN DEPT AS DEPT ON EMP.DEPTNO = DEPT.DEPTNO GROUP BY EMP.EMPNO',
                    """
                    src_attr = prev_attributes[prev_attributes.index(attr)]
                    # src_attr = find_from_attributes(attr, prev_attributes)
                    if not require_tuples_func_flag and len(prev_tuple_sorts) > 1:
                        # one-to-one mapping with 1st non-deleted tuple constraint
                        first_non_deleted_tuple_sort, find_constraint = \
                            self._find_1st_non_deleted_tuple_sort(prev_tuple_sorts)
                        if find_constraint is not None:
                            mapping_formulas.append(find_constraint)
                        formula = attr(curr_tuple_sort) == src_attr(first_non_deleted_tuple_sort)
                    else:
                        # one-to-one mapping
                        formula = attr(curr_tuple_sort) == src_attr(prev_tuple_sorts[0])
                elif isinstance(attr.EXPR, FCasePredicate):
                    # cannot be directly assigned and also need to be analyze
                    if require_tuples_func_flag:
                        first_non_deleted_tuple_sort, find_constraint = \
                            self._find_1st_non_deleted_tuple_sort(prev_tuple_sorts)
                        if find_constraint is not None:
                            mapping_formulas.append(find_constraint)
                        formula = attr.many_to_one_mapping(prev_tuple_sorts, curr_tuple_sort,
                                                           first_non_deleted_tuple_sort=first_non_deleted_tuple_sort)
                    else:
                        formula = attr.many_to_one_mapping(prev_tuple_sorts[0], curr_tuple_sort)
                else:
                    if not require_tuples_func_flag and len(prev_tuple_sorts) > 1:
                        # name, name+2
                        first_non_deleted_tuple_sort, find_constraint = \
                            self._find_1st_non_deleted_tuple_sort(prev_tuple_sorts)
                        if find_constraint is not None:
                            mapping_formulas.append(find_constraint)
                        formula = attr.many_to_one_mapping([first_non_deleted_tuple_sort], curr_tuple_sort)
                    elif not require_tuples_func_flag and len(prev_tuple_sorts) == 1:
                        prev_attr_tuple = attr.EXPR_CALL(prev_tuple_sorts[0])
                        curr_attr_tuple = self.visit(attr)(curr_tuple_sort)
                        formula = curr_attr_tuple == prev_attr_tuple
                    elif require_tuples_func_flag and len(prev_tuple_sorts) > 1:
                        # count(*)
                        first_non_deleted_tuple_sort, find_constraint = \
                            self._find_1st_non_deleted_tuple_sort(prev_tuple_sorts)
                        if find_constraint is not None:
                            mapping_formulas.append(find_constraint)
                        formula = attr.many_to_one_mapping(prev_tuple_sorts, curr_tuple_sort,
                                                           first_non_deleted_tuple_sort=first_non_deleted_tuple_sort)
                    else:
                        # COUNT(AGE-1) AS attr
                        formula = attr.many_to_one_mapping(prev_tuple_sorts, curr_tuple_sort)
                mapping_formulas.append(formula)

            has_no_agg_attribute = not any(getattr(attr, 'require_tuples', False) for attr in curr_attributes)
            for attr in curr_attributes:
                if is_uninterpreted_func(attr):
                    if isinstance(attr, ArithRef):
                        # CAST(TIME '12:34:56' AS TIMESTAMP(0))
                        continue
                    else:
                        _f(attr, getattr(attr, 'require_tuples', False))

                elif isinstance(attr, FAttribute):
                    if attr in prev_attributes and has_no_agg_attribute:
                        src_attr = prev_attributes[prev_attributes.index(attr)]
                        mapping_formulas.append(
                            self.visit(attr)(curr_tuple_sort) == self.visit(src_attr)(prev_tuple_sorts)
                        )
                    elif isinstance(attr.EXPR, ExcutableType):
                        attr_tuple = self.visit(attr)(curr_tuple_sort)
                        mapping_formulas.extend([
                            Not(attr_tuple.NULL),
                            attr_tuple.VALUE == attr.EXPR,
                        ])
                    elif isinstance(attr.EXPR, FNull):
                        mapping_formulas.append(attr.NULL(curr_tuple_sort))
                    else:
                        _f(attr, getattr(attr, 'require_tuples', False))

            return mapping_formulas

        if formulas.pity_flag:
            tuples = formulas[:-1]
        else:
            tuples = formulas
        for curr_tuple in tuples:
            if self.scope.is_register_dump_tuple(curr_tuple.name):
                curr_tuple = self.scope.get_dump_tuple(curr_tuple.name)
            else:
                prev_tuples = [prev_table[idx] for idx in curr_tuple.fathers]
                prev_tuple_sorts = [t.SORT for t in prev_tuples]
                prev_attributes = prev_tuples[0].attributes

                curr_tuple_sort = curr_tuple.SORT
                curr_attributes = curr_tuple.attributes

                mapping_formulas = _mapping_func(curr_tuple_sort, curr_attributes)

                if len(prev_tuple_sorts) == 1:
                    # vanilla 1-to-1 mapping
                    premise = self._DEL(prev_tuple_sorts[0])
                    code = And(*[
                        Implies(
                            Not(premise),
                            And(Not(self._DEL(curr_tuple_sort)), *mapping_formulas),
                        ),
                        Implies(premise, self._DEL(curr_tuple_sort)),
                    ])
                    if self.scope._script_writer is None:
                        _code_string = None
                    else:
                        _code_string = ',\n'.join([str(f) for f in mapping_formulas])
                        _code_string = f"""
And(*[
    Implies(
        Not({premise}),
        And(
Not({self._DEL(curr_tuple_sort)}),
{_code_string},
        ),
    ),
    Implies({premise}, {self._DEL(curr_tuple_sort)}),
])
"""
                else:
                    # if there exists at least one non-deleted tuple, we can project it
                    # works for groupby
                    # premise = Or(*[Not(self._DEL(t)) for t in prev_tuple_sorts])
                    premise = simplify([self._DEL(t) for t in prev_tuple_sorts], operator=Or, add_not=True)
                    code = And(*[
                        Implies(
                            premise,
                            And(Not(self._DEL(curr_tuple_sort)), *mapping_formulas),
                        ),
                        Implies(Not(premise), self._DEL(curr_tuple_sort)),
                    ])
                    if self.scope._script_writer is None:
                        _code_string = None
                    else:
                        _code_string = ',\n'.join([str(f) for f in mapping_formulas])
                        _code_string = f"""
And(*[
    Implies(
        {premise},
        And(
Not({self._DEL(curr_tuple_sort)}),
{_code_string},
        ),
    ),
    Implies(Not({premise}), {self._DEL(curr_tuple_sort)}),
])
"""
                implication = CodeSnippet(code=code, docstring=str(curr_tuple), docstring_first=True,
                                          code_string=_code_string)
                self.scope.register_formulas(formulas=implication)
                curr_tuple = DumpTuple(
                    name=curr_tuple.name, sort=curr_tuple_sort, attributes=curr_attributes,
                    parent_sorts=prev_tuples,
                )
                self.scope.register_dump_tuple(curr_tuple.name, curr_tuple)
            curr_table[curr_tuple.name] = curr_tuple

        if formulas.pity_flag:
            pity_tuple = formulas[-1]
            pity_tuple = self.visit(pity_tuple, prev_tuples=pity_tuple.tuples, pity_flag=formulas.pity_flag)
            curr_table[pity_tuple.name] = pity_tuple

        return curr_table

    @visitor(FFakeProjectionTable)
    def visit(self, formulas: FFakeProjectionTable, **kwargs) -> Dict:
        prev_table = self.visit(formulas.fathers[0], **kwargs)
        if formulas.is_correlated_subquery:
            formulas = self.detach_tuples(formulas)
        curr_table = {}
        for curr_tuple, prev_tuple in zip(formulas, prev_table.values()):
            curr_tuple = DumpTuple(
                name=curr_tuple.name, sort=prev_tuple.SORT, attributes=curr_tuple.attributes,
                parent_sorts=prev_tuple.kwargs.get('parent_sorts', None),
            )
            self.scope.register_dump_tuple(curr_tuple.name, curr_tuple)
            curr_table[curr_tuple.name] = curr_tuple
        return curr_table

    def _remove_duplicate_tuples(self, formulas: FDistinctTable | FUnionTable, **kwargs):
        def _duplicate_constraint(prev_tuple_sibling, prev_tuple_sort, curr_attributes: Sequence,
                                  prev_attributes: Sequence):
            formulas = []
            for curr_attr, prev_attr in zip(curr_attributes, prev_attributes):
                attr_tuple = self.visit(curr_attr)(prev_tuple_sort)
                attr_sibling_tuple = self.visit(prev_attr)(prev_tuple_sibling)
                formulas.append(
                    encode_same(
                        attr_tuple.NULL, attr_sibling_tuple.NULL,
                        attr_tuple.VALUE, attr_sibling_tuple.VALUE
                    ),
                )
            formulas = simplify(formulas, operator=And)
            formulas = Not(formulas)
            return formulas

        prev_table = self.visit(formulas.fathers[0])
        # # what if 1st tuple is deleted
        # first_non_deleted_tuple_sort, find_constraint = \
        #     self._find_1st_non_deleted_tuple_sort([t.SORT for t in formulas.fathers[0]])
        # self.scope.register_formulas(
        #     formulas=CodeSnippet(code=find_constraint, docstring=f'DISTINCT constraints for {formulas.name}',
        #                          docstring_first=True)
        # )
        curr_table = {}
        for idx, curr_tuple in enumerate(formulas):
            if self.scope.is_register_dump_tuple(curr_tuple.name):
                curr_tuple = self.scope.get_dump_tuple(curr_tuple.name)
            else:
                curr_tuple_sort = curr_tuple.SORT
                # assert len(curr_tuple.fathers) == 1, AssertionError(str(formulas))

                prev_tuple = prev_table[curr_tuple.fathers[0]]
                prev_tuple_sort = prev_tuple.SORT
                curr_attributes = curr_tuple.attributes

                premise = [Not(self._DEL(prev_tuple_sort))]
                if self.scope._script_writer is None:
                    _premise_string = None
                else:
                    _premise_string = [str(premise[-1])]

                # current tuple is not the 1st non-deleted tuple, they must be distinct
                # premise.append(
                #     Implies(
                #         # Not(self._DEL(tuple_sort.SORT)),
                #         And(curr_tuple_sort != first_non_deleted_tuple_sort, Not(self._DEL(curr_tuple_sort))),
                #         _duplicate_constraint(curr_tuple_sort, first_non_deleted_tuple_sort,
                #                               curr_attributes, prev_tuple.attributes),
                #     )
                # )
                prev_tuple_siblings = [tuple for tuple in list(prev_table.values())[:idx]]
                for tuple_sort in prev_tuple_siblings:
                    # current tuple is distinct from previous tuples
                    premise.append(
                        Implies(
                            Not(self._DEL(tuple_sort.SORT)),
                            # And(tuple_sort.SORT != first_non_deleted_tuple_sort, Not(self._DEL(tuple_sort.SORT))),
                            _duplicate_constraint(tuple_sort.SORT, prev_tuple_sort,
                                                  tuple_sort.attributes, prev_tuple.attributes),
                        )
                    )
                    if self.scope._script_writer is not None:
                        _premise_string.append(str(premise[-1]))
                premise = simplify(premise, operator=And)
                mapping_formulas = []
                for curr_attr, prev_attr in zip(curr_attributes, prev_tuple.attributes):
                    mapping_formulas.append(
                        self.visit(curr_attr)(curr_tuple_sort) == self.visit(prev_attr)(prev_tuple_sort)
                    )

                code = And(
                    Implies(
                        premise,
                        And(
                            Not(self._DEL(curr_tuple_sort)),
                            *mapping_formulas,
                        ),
                    ),
                    Implies(Not(premise), self._DEL(curr_tuple_sort)),
                )
                if self.scope._script_writer is None:
                    _code_string = None
                else:
                    _premise_string = ',\n'.join(f for f in _premise_string)
                    _premise_string = f"And(\n{_premise_string}\n)"
                    _code_string = ',\n'.join([str(f) for f in mapping_formulas])
                    _code_string = f"""
And(
    Implies(
        {_premise_string},
        And(
            Not({self._DEL(curr_tuple_sort)}),
            {_code_string},
        ),
    ),
    Implies(Not({_premise_string}), {self._DEL(curr_tuple_sort)}),
)
"""
                implication = CodeSnippet(code=code, docstring=str(curr_tuple), docstring_first=True,
                                          code_string=_code_string)
                self.scope.register_formulas(formulas=implication)
                curr_tuple = DumpTuple(
                    name=curr_tuple.name, sort=curr_tuple_sort, attributes=curr_attributes,
                    parent_sorts=[prev_tuple],
                )
                self.scope.register_dump_tuple(curr_tuple.name, curr_tuple)
            curr_table[curr_tuple.name] = curr_tuple
        return curr_table

    @visitor(FDistinctTable)
    def visit(self, formulas: FDistinctTable, **kwargs) -> Dict:
        curr_table = self._remove_duplicate_tuples(formulas)
        return curr_table

    ############################ find first non-deleted tuples ############################

    def _find_1st_non_deleted_tuple_sort(self, tuple_sorts, **kwargs):
        # find 1st non-deleted constraint: 1st reduced tuple must be non-deleted
        if len(tuple_sorts) == 1:
            return tuple_sorts[0], None

        constraints = []
        copied_prev_tuple_sorts = [
            self.scope._declare_tuple_sort(f'_find_1st_non_deleted_{self.scope._get_new_tuple_name()}')
            for _ in range(len(tuple_sorts))
        ]
        constraints.extend([
            copied_prev_tuple_sort == prev_tuple_sort
            for prev_tuple_sort, copied_prev_tuple_sort in zip(tuple_sorts, copied_prev_tuple_sorts)
        ])
        DEL_FUNC = kwargs['group_func'] if 'group_func' in kwargs else self._DEL

        for i in range(1, len(copied_prev_tuple_sorts)):
            x = copied_prev_tuple_sorts[0]
            y = copied_prev_tuple_sorts[i]
            _x = self.scope._declare_tuple_sort(f'_find_1st_non_deleted_{self.scope._get_new_tuple_name()}')
            if 'group_func' in kwargs:
                premise = And(DEL_FUNC(x), Not(DEL_FUNC(y)), kwargs['group_func'](y))
            else:
                premise = And(DEL_FUNC(x), Not(DEL_FUNC(y)))
            constraints.append(If(premise, _x == y, _x == x))

            copied_prev_tuple_sorts[0] = _x
        return copied_prev_tuple_sorts[0], And(*constraints)

    ############################ find last non-deleted tuples ############################

    def _find_last_non_deleted_tuple_sort(self, tuple_sorts, **kwargs):
        # find 1st non-deleted constraint: 1st reduced tuple must be non-deleted
        if len(tuple_sorts) == 1:
            return tuple_sorts[-1], None

        constraints = []
        copied_prev_tuple_sorts = [
            self.scope._declare_tuple_sort(f'_find_last_non_deleted_{self.scope._get_new_tuple_name()}')
            for _ in range(len(tuple_sorts))
        ]
        constraints.extend([
            copied_prev_tuple_sort == prev_tuple_sort
            for prev_tuple_sort, copied_prev_tuple_sort in zip(tuple_sorts, copied_prev_tuple_sorts)
        ])

        for i in range(1, len(copied_prev_tuple_sorts)):
            x = copied_prev_tuple_sorts[0]
            y = copied_prev_tuple_sorts[i]
            _x = self.scope._declare_tuple_sort(f'_find_last_non_deleted_{self.scope._get_new_tuple_name()}')
            if 'group_func' in kwargs:
                premise = And(Not(self._DEL(y)), kwargs['group_func'](y))
            else:
                premise = Not(self._DEL(y))
            constraints.append(If(premise, _x == y, _x == x))
            copied_prev_tuple_sorts[0] = _x
        return copied_prev_tuple_sorts[0], And(*constraints)

    ############################ table ############################

    @visitor(FGroupByTable)
    def visit(self, formulas: FGroupByTable, **kwargs) -> Dict:
        prev_table = self.visit(formulas.fathers[0])
        return prev_table

    @visitor(FGroupByMapTable)
    def visit(self, formulas: FGroupByMapTable, **kwargs) -> Dict:
        prev_table = self.visit(formulas.fathers[0])
        if not formulas.is_correlated_subquery and formulas.fathers[0].is_correlated_subquery:
            # attach correlated subquery's tuples to projection
            prev_table = self.attach_tuples(prev_table)

        """
        Example:
            (t10, t11, t12) -> t16
            (     t13, t14) -> t17
            (          t15) -> t18
        """

        # constraint for groupby
        # let i = [1, ..., n], i <= j, j = [i, ..., n]
        # group(i, t_j)  <=> ¬ Del(t_j) ∧ group(i, t_i) ∧ E(t_j) = E(t_i)
        # sum group(?, t_j) = Del(t_j)
        constraint = []
        i = 0
        prev_tuples = list(prev_table.values())
        t_0 = prev_tuples[i].SORT
        constraint.append(
            formulas.group_function(t_0, IntVal(str(i))) == If(self._DEL(t_0), Z3_0, Z3_1)
        )
        values = [
            [self.visit(key)(t.SORT) for key in keys]
            for t, keys in zip(prev_tuples, formulas.keys)
        ]
        for j, curr_tuple in enumerate(prev_tuples[1:], start=1):
            constraint.append(
                Sum(*[formulas.group_function(curr_tuple.SORT, IntVal(str(group_idx))) for group_idx in
                      range(j + 1)]) == \
                If(self._DEL(curr_tuple.SORT), Z3_0, Z3_1)
            )

            curr_values = values[j]
            for group_idx in range(j):
                group_values = values[group_idx]
                z3_group_index = IntVal(str(group_idx))
                value_equality = simplify(
                    [encode_same(curr_v.NULL, group_v.NULL, curr_v.VALUE, group_v.VALUE) \
                     for curr_v, group_v in zip(curr_values, group_values)],
                    operator=And,
                )
                constraint.append(
                    formulas.group_function(curr_tuple.SORT, z3_group_index) == And(
                        Not(self._DEL(curr_tuple.SORT)),
                        formulas.group_function(prev_tuples[group_idx].SORT, z3_group_index),
                        value_equality,
                    )
                )

        curr_table = {}
        for idx, curr_tuple in enumerate(formulas):
            if self.scope.is_register_dump_tuple(curr_tuple.name):
                curr_tuple = self.scope.get_dump_tuple(curr_tuple.name)
            else:
                curr_tuple_sort = curr_tuple.SORT
                prev_tuples = [prev_table[idx] for idx in curr_tuple.fathers]  # many-to-one mapping, e.g., COUNT(...)
                prev_tuple_sorts = [t.SORT for t in prev_tuples]
                group_function = lambda x, **kwargs: formulas.group_function(x, IntVal(str(idx)))

                first_non_deleted_tuple_sort = None
                last_non_deleted_tuple_sort = None

                premise = Or(*[group_function(t) for t in prev_tuple_sorts])  # group by
                if formulas.having_clause is not None:
                    if first_non_deleted_tuple_sort is None:
                        if len(prev_tuple_sorts) == 1:
                            first_non_deleted_tuple_sort = prev_tuple_sorts[0]
                        else:
                            first_non_deleted_tuple_sort, find_constraint = \
                                self._find_1st_non_deleted_tuple_sort(prev_tuple_sorts)
                            if find_constraint is not None:
                                constraint.append(find_constraint)

                    # if having has MIN/MAX, we should add BOUND constraints
                    if getattr(formulas.having_clause, 'require_tuples', False):
                        # if AGG in HAVING
                        deleted_func = lambda x, **kwargs: Not(group_function(x))
                        having_premise = self.visit(formulas.having_clause)(
                            prev_tuple_sorts,
                            first_non_deleted_tuple_sort=first_non_deleted_tuple_sort,
                            deleted_func=deleted_func,
                        )
                    else:
                        having_premise = self.visit(formulas.having_clause)(first_non_deleted_tuple_sort)

                    premise = And(
                        premise,
                        Not(having_premise.NULL),  # having is not NULL
                        having_premise.VALUE,  # having condition holds
                    )

                if self.scope._script_writer is None:
                    _code_string = None
                else:
                    _code_string = ''

                mapping = []
                for attr in formulas.out_attributes:
                    if attr in curr_tuple.out_attributes:
                        if first_non_deleted_tuple_sort is None:
                            if len(prev_tuple_sorts) == 1:
                                first_non_deleted_tuple_sort = prev_tuple_sorts[0]
                            else:
                                first_non_deleted_tuple_sort, find_constraint = \
                                    self._find_1st_non_deleted_tuple_sort(prev_tuple_sorts)
                                if find_constraint is not None:
                                    constraint.append(find_constraint)
                        # indeed we need to assign 1st previous tuple attributes to the current tuple
                        src_attr = curr_tuple.out_attributes[curr_tuple.out_attributes.index(attr)]
                        # avoid alias attribute problem
                        src_attr_tuple = src_attr(first_non_deleted_tuple_sort)
                        dst_attr_tuple = attr(curr_tuple_sort)
                        mapping.append(dst_attr_tuple == src_attr_tuple)
                        if self.scope._script_writer is not None:
                            _code_string += f"And({dst_attr_tuple.NULL == src_attr_tuple.NULL},\n{dst_attr_tuple.VALUE == src_attr_tuple.VALUE}),\n"
                    elif isinstance(attr, FLastValuePredicate) or isinstance(attr.EXPR, FLastValuePredicate):
                        if last_non_deleted_tuple_sort is None:
                            if len(prev_tuple_sorts) == 1:
                                last_non_deleted_tuple_sort = prev_tuple_sorts[0]
                            else:
                                last_non_deleted_tuple_sort, find_constraint = \
                                    self._find_last_non_deleted_tuple_sort(prev_tuple_sorts, group_func=group_function)
                                constraint.append(find_constraint)
                        attr_tuple = self.visit(attr)(curr_tuple_sort)
                        attr_generated_tuple = attr.__expr__(last_non_deleted_tuple_sort)
                        mapping.append(attr_tuple == attr_generated_tuple)
                        if self.scope._script_writer is not None:
                            _code_string += f"And({attr_tuple.NULL == attr_generated_tuple.NULL},\n{attr_tuple.VALUE == attr_generated_tuple.VALUE}),\n"
                    else:
                        if len(prev_tuple_sorts) == 1:
                            first_non_deleted_tuple_sort = prev_tuple_sorts[0]
                        else:
                            first_non_deleted_tuple_sort, find_constraint = \
                                self._find_1st_non_deleted_tuple_sort(prev_tuple_sorts)
                            if find_constraint is not None:
                                constraint.append(find_constraint)
                        attr_tuple = self.visit(attr)(curr_tuple_sort)
                        attr_generated_tuple = attr.__expr__(prev_tuple_sorts, group_func=group_function,
                                                             first_non_deleted_tuple_sort=first_non_deleted_tuple_sort)
                        mapping.append(attr_tuple == attr_generated_tuple)
                        if self.scope._script_writer is not None:
                            _code_string += f"And({attr_tuple.NULL == attr_generated_tuple.NULL},\n{attr_tuple.VALUE == attr_generated_tuple.VALUE}),\n"

                code = And(
                    Implies(
                        premise,
                        And(
                            Not(self._DEL(curr_tuple_sort)),
                            And(*mapping),
                        ),
                    ),
                    Implies(
                        Not(premise),
                        self._DEL(curr_tuple_sort),
                    ),
                )
                if self.scope._script_writer is None:
                    _code_string = None
                else:
                    # _code_string = ',\n'.join([str(f) for f in mapping])
                    _code_string = f"""
And(
    Implies(
        {premise},
        And(
            Not({self._DEL(curr_tuple_sort)}),
            And(
{_code_string}
            ),
        ),
    ),
    Implies(
        Not({premise}),
        {self._DEL(curr_tuple_sort)},
    ),
)
"""
                implication = CodeSnippet(code=code, docstring=str(curr_tuple), docstring_first=True,
                                          code_string=_code_string)
                self.scope.register_formulas(formulas=implication)
                curr_tuple = DumpTuple(
                    name=curr_tuple.name, sort=curr_tuple_sort,
                    attributes=formulas.out_attributes,
                    parent_sorts=[t.SORT for t in prev_tuples],
                )
                self.scope.register_dump_tuple(curr_tuple.name, curr_tuple)
            curr_table[curr_tuple.name] = curr_tuple
        # register constraint of GroupReduce table
        if len(constraint) > 0:
            if self.scope._script_writer is None:
                _code_string = None
            else:
                _code_string = ',\n'.join([str(f) for f in constraint])
                _code_string = f"""
    And(
    {_code_string}
    )
    """
            self.scope.register_formulas(
                formulas=CodeSnippet(code=And(*constraint), docstring=f'{formulas.name} GroupBy constraint',
                                     docstring_first=True, code_string=_code_string)
            )
        return curr_table

    def _move_del_tuples_to_tail(self, sorted_tuples):
        # only work for List Semantics eval
        constraint = []
        for idx in range(len(sorted_tuples)):
            new_tuple = self.scope._declare_tuple_sort(f'_orderby_{self.scope._get_new_tuple_name()}')
            constraint.append(new_tuple == sorted_tuples[idx])
            sorted_tuples[idx] = new_tuple

        for j in range(len(sorted_tuples)):
            for idx in range(len(sorted_tuples) - j - 1):
                x, y = sorted_tuples[idx], sorted_tuples[idx + 1]
                _x = self.scope._declare_tuple_sort(f'_orderby_{self.scope._get_new_tuple_name()}')
                _y = self.scope._declare_tuple_sort(f'_orderby_{self.scope._get_new_tuple_name()}')

                constraint.append(
                    If(
                        And(self._DEL(x), Not(self._DEL(y))),
                        And(_x == y, _y == x),
                        And(_x == x, _y == y),
                    )
                )

                sorted_tuples[idx] = _x
                sorted_tuples[idx + 1] = _y

        if self.scope._script_writer is None:
            _code_string = None
        else:
            _code_string = ',\n'.join([str(c) for c in constraint])
            _code_string = f"And(\n{_code_string}\n)"

        # register constraint of OrderBy table
        constraint = CodeSnippet(code=And(*constraint), docstring=f"Move {sorted_tuples}'s deleted tuples to the tail",
                                 docstring_first=True, code_string=_code_string)
        return sorted_tuples, constraint

    @visitor(FOrderByTable)
    def visit(self, formulas: FOrderByTable, **kwargs) -> Dict:
        prev_table = self.visit(formulas.fathers[0])
        if not formulas.is_correlated_subquery and formulas.fathers[0].is_correlated_subquery:
            # attach correlated subquery's tuples to projection
            prev_table = self.attach_tuples(prev_table)
        constraint = []  # generate constraint over those Map tuples

        # 1) move DELETED tuples to the table end
        sorted_tuples = [t.SORT for t in prev_table.values()]
        for idx in range(len(sorted_tuples)):
            new_tuple = self.scope._declare_tuple_sort(f'_orderby_{self.scope._get_new_tuple_name()}')
            constraint.append(new_tuple == sorted_tuples[idx])
            sorted_tuples[idx] = new_tuple

        for j in range(len(formulas)):
            for idx in range(len(formulas) - j - 1):
                x, y = sorted_tuples[idx], sorted_tuples[idx + 1]
                _x = self.scope._declare_tuple_sort(f'_orderby_{self.scope._get_new_tuple_name()}')
                _y = self.scope._declare_tuple_sort(f'_orderby_{self.scope._get_new_tuple_name()}')

                constraint.append(
                    If(
                        And(self._DEL(x), Not(self._DEL(y))),
                        And(_x == y, _y == x),
                        And(_x == x, _y == y),
                    )
                )

                sorted_tuples[idx] = _x
                sorted_tuples[idx + 1] = _y

        # 2) swap by keys and their ascending rules
        order_keys = formulas.keys

        def _swap(x, y):
            # In MySQL: NULL is smaller than every non-NULL variables
            # keep the same order:
            #   1) the last tuple is deleted (since we will move deleted tuple to the end first),
            #   2) previous <= next,
            #   3) NULL /\ Not(NULL)
            swap_cond = []
            should_equality_next_col = []
            for attribute, ascending in zip(order_keys, formulas.ascending_flags):
                attr_x = self.visit(attribute)(x)
                attr_y = self.visit(attribute)(y)
                if ascending:
                    formula = And(
                        Not(self._DEL(x)), Not(self._DEL(y)),
                        Or(
                            # attr_y.NULL,
                            And(Not(attr_x.NULL), attr_y.NULL),  # NULL, NULL
                            And(Not(attr_x.NULL), Not(attr_y.NULL), attr_x.VALUE > attr_y.VALUE),
                        )
                    )
                else:
                    formula = And(
                        Not(self._DEL(x)), Not(self._DEL(y)),
                        Or(
                            # attr_x.NULL,
                            And(attr_x.NULL, Not(attr_y.NULL)),  # NULL, NULL
                            And(Not(attr_x.NULL), Not(attr_y.NULL), attr_x.VALUE < attr_y.VALUE),
                        )
                    )
                if len(should_equality_next_col) > 0:
                    formula = And(*should_equality_next_col, formula)
                swap_cond.append(formula)
                should_equality_next_col.append(
                    encode_same(attr_x.NULL, attr_y.NULL, attr_x.VALUE, attr_y.VALUE)
                )
            swap_cond = simplify(swap_cond, operator=Or)
            return swap_cond

        for j in range(len(sorted_tuples)):
            for idx in range(len(sorted_tuples) - j - 1):
                x, y = sorted_tuples[idx], sorted_tuples[idx + 1]
                _x = self.scope._declare_tuple_sort(f'_orderby_{self.scope._get_new_tuple_name()}')
                _y = self.scope._declare_tuple_sort(f'_orderby_{self.scope._get_new_tuple_name()}')

                constraint.append(
                    # swapping is stricter than not swapping
                    If(
                        _swap(x, y),
                        And(_x == y, _y == x),
                        And(_x == x, _y == y),  # keep the same order
                    )
                )

                sorted_tuples[idx] = _x
                sorted_tuples[idx + 1] = _y

        if self.scope._script_writer is None:
            _code_string = None
        else:
            _code_string = ',\n'.join([str(c) for c in constraint])
            _code_string = f"And(\n{_code_string}\n)"
        # register constraint of OrderBy table
        self.scope.register_formulas(
            formulas=CodeSnippet(code=And(*constraint), docstring=f'{formulas.name} OrderBy constraint',
                                 docstring_first=True, code_string=_code_string)
        )

        curr_table = {}
        # final_tuple_sorts = []
        for idx, curr_tuple in enumerate(formulas):
            if self.scope.is_register_dump_tuple(curr_tuple.name):
                curr_tuple = self.scope.get_dump_tuple(curr_tuple.name)
            else:
                curr_tuple_sort = self.scope._get_tuple_sort(curr_tuple.name)
                implication = CodeSnippet(code=curr_tuple_sort == sorted_tuples[idx],
                                          docstring=str(curr_tuple), docstring_first=True)
                self.scope.register_formulas(formulas=implication)
                curr_tuple = DumpTuple(
                    name=curr_tuple.name, sort=curr_tuple_sort,
                    attributes=prev_table[curr_tuple.fathers[0]].attributes,
                    parent_sorts=[prev_table[curr_tuple.fathers[0]]],
                )
                self.scope.register_dump_tuple(curr_tuple.name, curr_tuple)
                # final_tuple_sorts.append(curr_tuple_sort)
            curr_table[curr_tuple.name] = curr_tuple
        # save orderby constraint, and use they in final formulas
        self.scope.orderby_constraints = {
            'keys': formulas.keys,
            'tuples': [tuple.SORT for tuple in curr_table.values()],
        }
        return curr_table

    @visitor(FLimitTable)
    def visit(self, formulas: FLimitTable, **kwargs) -> Dict:
        prev_table = self.visit(formulas.fathers[0])
        if formulas.drop_deleted_tuples:
            constraint = []
            # 1) move DELETED tuples to the table end
            sorted_tuples = [t.SORT for t in prev_table.values()]
            for idx in range(len(sorted_tuples)):
                new_tuple = self.scope._declare_tuple_sort(f'_limit_{self.scope._get_new_tuple_name()}')
                constraint.append(new_tuple == sorted_tuples[idx])
                sorted_tuples[idx] = new_tuple

            for j in range(len(prev_table)):
                for idx in range(len(prev_table) - j - 1):
                    x, y = sorted_tuples[idx], sorted_tuples[idx + 1]
                    _x = self.scope._declare_tuple_sort(f'_limit_{self.scope._get_new_tuple_name()}')
                    _y = self.scope._declare_tuple_sort(f'_limit_{self.scope._get_new_tuple_name()}')

                    constraint.append(
                        If(
                            And(self._DEL(x), Not(self._DEL(y))),
                            And(_x == y, _y == x),
                            And(_x == x, _y == y),
                        )
                    )

                    sorted_tuples[idx] = _x
                    sorted_tuples[idx + 1] = _y
            # register constraint of dropping the deleted tuples to the end of the table
            if self.scope._script_writer is None:
                _code_string = None
            else:
                _code_string = ',\n'.join([str(c) for c in constraint])
                _code_string = f"And(\n{_code_string}\n)"
            self.scope.register_formulas(
                formulas=CodeSnippet(
                    code=And(*constraint),
                    docstring=f'{formulas.name} LIMIT constraint of dropping the deleted tuples to the end of the table',
                    docstring_first=True, code_string=_code_string,
                )
            )

            curr_table = {}
            for idx, prev_index in enumerate(range(formulas.limit_a, formulas.limit_b)):
                curr_tuple = formulas[idx]
                if self.scope.is_register_dump_tuple(curr_tuple.name):
                    curr_tuple = self.scope.get_dump_tuple(curr_tuple.name)
                else:
                    curr_tuple_sort = curr_tuple.SORT
                    implication = CodeSnippet(
                        code=curr_tuple_sort == sorted_tuples[prev_index],
                        docstring=str(curr_tuple), docstring_first=True,
                    )
                    self.scope.register_formulas(formulas=implication)
                    curr_tuple = DumpTuple(
                        name=curr_tuple.name, sort=curr_tuple_sort,
                        attributes=prev_table[curr_tuple.fathers[0]].attributes,
                        parent_sorts=[prev_table[curr_tuple.fathers[0]]],
                    )
                    self.scope.register_dump_tuple(curr_tuple.name, curr_tuple)

                curr_table[curr_tuple.name] = curr_tuple
            return curr_table
        else:
            pop_keys = [pop_key for idx, pop_key in enumerate(prev_table)
                        if not (formulas.limit_a <= idx < formulas.limit_b)]
            # print(formulas.limit_a, formulas.limit_b)
            for key in pop_keys:
                prev_table.pop(key)
            return prev_table

    ############################ UNION/INTERSECT/EXCEPT ############################
    @visitor(FUnionAllTable)
    def visit(self, formulas: FUnionAllTable, **kwargs) -> Dict:
        prev_tables = self.visit(formulas.fathers)
        _1st_prev_table = prev_tables[0]
        for prev_table in prev_tables[1:]:
            _1st_prev_table.update(prev_table)
        curr_table = _1st_prev_table
        return curr_table

    @visitor(FUnionTable)
    def visit(self, formulas: FUnionTable, **kwargs) -> Dict:
        curr_table = self._remove_duplicate_tuples(formulas)
        return curr_table

    @visitor(FIntersectAllTable)
    def visit(self, formulas: FIntersectAllTable, **kwargs) -> Dict:
        prev_table, prev_except_table = self.visit(formulas.fathers)
        prev_tuple_sorts = [t.SORT for t in prev_table.values()]
        prev_intersect_tuple_sorts = [t.SORT for t in prev_except_table.values()]
        prev_intersect_attributes = formulas.fathers[1].attributes

        curr_table = {}
        for idx, curr_tuple in enumerate(formulas):
            if self.scope.is_register_dump_tuple(curr_tuple.name):
                curr_tuple = self.scope.get_dump_tuple(curr_tuple.name)
            else:
                curr_tuple_sort = curr_tuple.SORT
                prev_tuple_sort = prev_table[curr_tuple.fathers[0]].SORT
                prev_attributes = curr_attributes = curr_tuple.attributes

                # equals to at least one tuple
                premise = []
                for prev_intersect_tuple in prev_intersect_tuple_sorts:
                    tmp = []
                    for attr, except_attr in zip(prev_attributes, prev_intersect_attributes):
                        attr, except_attr = attr(prev_tuple_sort), except_attr(prev_intersect_tuple)
                        tmp.append(encode_same(attr.NULL, except_attr.NULL, attr.VALUE, except_attr.VALUE))
                    tmp = simplify(tmp, operator=And)
                    premise.append(And(Not(self._DEL(prev_intersect_tuple)), tmp))
                premise = And(Not(self._DEL(prev_tuple_sort)), Or(*premise))

                mapping_formulas = [attr(curr_tuple_sort) == attr(prev_tuple_sort) for attr in curr_attributes]

                code = And(*[
                    Implies(
                        premise,
                        And(Not(self._DEL(curr_tuple_sort)), *mapping_formulas),
                    ),
                    Implies(Not(premise), self._DEL(curr_tuple_sort)),
                ])
                implication = CodeSnippet(
                    code=code,
                    docstring=f"{curr_tuple.name} := Intersect([{prev_tuple_sort}] ∩ {prev_intersect_tuple_sorts})",
                    docstring_first=True,
                )
                self.scope.register_formulas(formulas=implication)
                curr_tuple = DumpTuple(
                    name=curr_tuple.name, sort=curr_tuple_sort, attributes=curr_attributes,
                    parent_sorts=[prev_tuple_sort],
                )
                self.scope.register_dump_tuple(curr_tuple.name, curr_tuple)
            curr_table[curr_tuple.name] = curr_tuple
        implication = CodeSnippet(
            code=Implies(
                Or(
                    And(*[self._DEL(tuple_sort) for tuple_sort in prev_tuple_sorts]),
                    And(*[self._DEL(tuple_sort) for tuple_sort in prev_intersect_tuple_sorts]),
                ),
                And(*[self._DEL(tuple.SORT) for tuple in curr_table.values()])
            ),
            docstring=f"Intersection constraint of empty sets",
            docstring_first=True,
        )
        self.scope.register_formulas(formulas=implication)
        return curr_table

    @visitor(FIntersectTable)
    def visit(self, formulas: FIntersectTable, **kwargs) -> Dict:
        curr_table = self._remove_duplicate_tuples(formulas)
        return curr_table

    @visitor(FExceptAllTable)
    def visit(self, formulas: FExceptAllTable, **kwargs) -> Dict:
        prev_table, prev_except_table = self.visit(formulas.fathers)
        # prev_tuple_sorts = [t.SORT for t in prev_table.values()]
        prev_except_tuple_sorts = [t.SORT for t in prev_except_table.values()]
        # prev_except_attributes = formulas.fathers[1].attributes

        # build the `paired` matrix
        # Eq(t_i, t_j, A) <=> \not DEL(t_i) /\ \not DEL(t_i) /\ \foreach a \in A. t_i.a = t_j.a
        # paired(i,j) = Eq(t_i, t_j, A), i=j=1
        #             = Eq(t_i, t_j, A) /\ /\_{k=1}^{j-1} \not paired(1,k), i=1, j!=1
        #             = Eq(t_i, t_j, A) /\ /\_{k=1}^{i-1} \not paired(k,1), i!=1, j=1
        #             = Eq(t_i, t_j, A) /\ /\_{k=1}^{i-1} \not paired(k,j) /\ /\_{k=1}^{j-1} \not paired(i,k), otherwise

        func_name = formulas.name + '_paired'
        paired_func = Function(func_name, self.scope.TupleSort, self.scope.TupleSort, self.scope.BooleanSort)
        self.scope.register_function(__pos_hash__(func_name), paired_func)
        if self.scope._script_writer is not None:
            self.scope._script_writer.function_declaration.append(
                CodeSnippet(
                    code=f"{func_name} = Function('{func_name}', __TupleSort, __TupleSort, __Boolean)",
                    docstring=f"define `{func_name}` function  for {formulas.name}'s EXCEPT ALL",
                )
            )

        def _tuple_eq(t_i, t_j):
            attr_eq_formula = []
            for attr_i, attr_j in zip(t_i.attributes, t_j.attributes):
                attr_i, attr_j = attr_i(t_i.SORT), attr_j(t_j.SORT)
                attr_eq_formula.append(encode_same(attr_i.NULL, attr_j.NULL, attr_i.VALUE, attr_j.VALUE))
            return And(Not(self._DEL(t_i.SORT)), Not(self._DEL(t_j.SORT)), And(*attr_eq_formula))

        paired_formulas = []
        prev_tuples = list(prev_table.values())
        prev_except_tuples = list(prev_except_table.values())
        for i, t_i in enumerate(prev_tuples):
            for j, t_j in enumerate(prev_except_tuples):
                if i == j == 0:
                    paired_f = paired_func(t_i.SORT, t_j.SORT) == _tuple_eq(t_i, t_j)
                elif i == 0 and j != 0:
                    paired_f = paired_func(t_i.SORT, t_j.SORT) == And(_tuple_eq(t_i, t_j), Not(Or(
                        *[paired_func(t_i.SORT, t_k.SORT) for t_k in prev_except_tuples[:j]])))
                elif i != 0 and j == 0:
                    paired_f = paired_func(t_i.SORT, t_j.SORT) == And(_tuple_eq(t_i, t_j), Not(Or(
                        *[paired_func(t_k.SORT, t_j.SORT) for t_k in prev_tuples[:i]])))
                else:
                    paired_f = paired_func(t_i.SORT, t_j.SORT) == And(
                        _tuple_eq(t_i, t_j), \
                        Not(Or(*[paired_func(t_k.SORT, t_j.SORT) for t_k in prev_tuples[:i]] + [
                            paired_func(t_i.SORT, t_k.SORT) for t_k in prev_except_tuples[:j]]))
                    )
                paired_formulas.append(paired_f)
        self.scope.register_formulas(
            CodeSnippet(code=And(*paired_formulas), docstring=f"EXCEPT ALL for {formulas.name}", docstring_first=True)
        )

        curr_table = {}
        for idx, curr_tuple in enumerate(formulas):
            if self.scope.is_register_dump_tuple(curr_tuple.name):
                curr_tuple = self.scope.get_dump_tuple(curr_tuple.name)
            else:
                curr_tuple_sort = curr_tuple.SORT
                prev_tuple_sort = prev_table[curr_tuple.fathers[0]].SORT
                curr_attributes = curr_tuple.attributes

                premise = And(
                    Not(self._DEL(prev_tuple_sort)),  # not deleted
                    # is not paired with any tuple in the rhs table
                    And(*[Not(paired_func(prev_tuple_sort, t_j)) for t_j in prev_except_tuple_sorts])
                )
                mapping_formulas = [attr(curr_tuple_sort) == attr(prev_tuple_sort) for attr in curr_attributes]

                code = And(*[
                    Implies(
                        premise,
                        And(Not(self._DEL(curr_tuple_sort)), *mapping_formulas),
                    ),
                    Implies(Not(premise), self._DEL(curr_tuple_sort)),
                ])
                implication = CodeSnippet(code=code, docstring=str(curr_tuple), docstring_first=True)
                self.scope.register_formulas(formulas=implication)
                curr_tuple = DumpTuple(
                    name=curr_tuple.name, sort=curr_tuple_sort, attributes=curr_attributes,
                    parent_sorts=[prev_tuple_sort],
                )
                self.scope.register_dump_tuple(curr_tuple.name, curr_tuple)
            curr_table[curr_tuple.name] = curr_tuple
        return curr_table

    @visitor(FExceptTable)
    def visit(self, formulas: FExceptTable, **kwargs) -> Dict:
        curr_table = self._remove_duplicate_tuples(formulas)
        return curr_table

    ############################ predicate ############################

    @visitor(FuncDeclRef)
    def visit(self, z3function: FuncDeclRef, **kwargs):
        return z3function

    @visitor(IntermFunc)
    def visit(self, formulas: IntermFunc, **kwargs):
        return formulas

    @visitor(FNotInPredicate)
    def visit(self, formulas: FNotInPredicate, **kwargs):
        # I. `(a, b) NOT IN ((A1, B1), (A2, B2))`
        # [(0,1) (0,0) (1, NULL)] NOT IN [(0,1) (0,0)] => [False, False, True]
        # [(0,1) (0,0) (NULL, NULL)] NOT IN [(0,1) (0,0)] => [False, False, NULL]
        # [(0,C) (0,C)] NOT IN [(0,B) (0,A) (1,NULL)] => [True, True]
        # NULL NOT IN (0) => [NULL]
        # 1) if (a, b) = (A1, B1) \/ (a, b) = (A2, B2), and
        #       then
        #               i) (a, b) contains NULL, return (NULL)
        #               ii) else (NOT NULL, False)
        # 2) if Not((a, b) = (A1, B1) \/ (a, b) = (A2, B2)),
        #       then
        #               i) if (a, b) = (NULL, NULL) \/ (A1, B1) = (NULL, NULL) \/ (A2, B2) = (NULL, NULL), return (NULL)
        #               ii) else (NOT NULL, True)
        # II. `(a, b) NOT IN ()` is always True

        def _f(args, **kwargs):
            src_attributes = formulas[0]
            src_attr_tuples = []
            for src_attr in src_attributes:
                if is_uninterpreted_func(src_attr):
                    raise NotSupportedError(f"FNotInPredicate does not support Uninterpreted Functions.")
                else:
                    if isinstance(src_attr, FAttribute) and src_attr.EXPR is not None:
                        src_attr_tuple = src_attr.__expr__(args, **kwargs)
                    else:
                        src_attr_tuple = self.visit(src_attr)(args, **kwargs)
                src_attr_tuples.append(src_attr_tuple)

            # register outer attributes for correlated subquery

            prev_table = self.visit(formulas.operands[1])
            all_del_formula = And(*[self._DEL(prev_tuple.SORT) for prev_tuple in prev_table.values()])
            null_exist_formula = Or(*[src_attr_tuple.NULL for src_attr_tuple in src_attr_tuples])
            # null_exist_formula = And(*[src_attr_tuple.NULL for src_attr_tuple in src_attr_tuples])
            in_formula = []
            null_list = [simplify([src_attr_tuple.NULL for src_attr_tuple in src_attr_tuples], operator=And)]
            for prev_tuple in prev_table.values():
                tmp = []
                pair_are_null = []
                for src_attr_tuple, dst_attr in zip(src_attr_tuples, prev_tuple.attributes):
                    dst_attr_tuple = self.visit(dst_attr)(prev_tuple.SORT)
                    tmp.append(
                        simplify([
                            Not(self._DEL(prev_tuple.SORT)),
                            encode_same(src_attr_tuple.NULL, dst_attr_tuple.NULL, src_attr_tuple.VALUE,
                                        dst_attr_tuple.VALUE)
                        ], operator=And)
                    )
                    pair_are_null.append(And(Not(self._DEL(prev_tuple.SORT)), dst_attr_tuple.NULL))
                null_list.append(simplify(pair_are_null, operator=And))
                # null_list.append(And(Not(self._DEL(prev_tuple.SORT)), dst_attr_tuple.NULL))
                in_formula.append(simplify(tmp, operator=And))
            in_formula = Or(*in_formula)
            return FExpressionTuple(
                # is NULL?
                And(
                    Not(all_del_formula),
                    If(in_formula, null_exist_formula, Or(*null_list))
                    # Or(
                    #     And(in_formula, null_exist_formula),
                    #     And(Not(in_formula), Or(*null_list)),
                    # )
                ),
                # VALUE?
                Or(
                    all_del_formula,
                    # And(Not(in_formula), Not(null_exist_formula)),
                    Not(in_formula),
                ),
            )

        return _f

    @visitor(FInPredicate)
    def visit(self, formulas: FInPredicate, **outer_kwargs):
        # I. `(a, b) IN ((A1, B1), (A2, B2))`
        # [(0,1) (0,0) (1, NULL)] IN [(0,1) (0,0)] => [True, True, False]
        # [(0,1) (0,0) (NULL, NULL)] IN [(0,1) (0,0)] => [True, True, NULL]
        # [1, NULL] IN [(1, 0)] => [NULL]
        # [(1, NULL)] IN [(NULL, 0), (1, NULL)] => [NULL, NULL]
        # [(1, 2)] IN [(NULL, 0), (1, NULL)] => [False, False]
        # 1) if a \/ b is NULL, then NULL
        # 2) if (a, b) = (A1, B1) \/ (a, b) = (A2, B2), and
        #       then
        #               i) (a, b) contains NULL, return (NULL)
        #               ii) else (NOT NULL, True)
        # 3) if Not((a, b) = (A1, B1) \/ (a, b) = (A2, B2)),
        #       then
        #               i) if (A1, B1, A2, B2) or (a, b) contain NULL, return (NULL)
        #               ii) else (NOT NULL, False)
        # II. `(a, b) IN ()` is always False

        def _f(args, **kwargs):
            src_attributes = formulas[0]
            src_attr_tuples = []
            for src_attr in src_attributes:
                if is_uninterpreted_func(src_attr):
                    raise NotSupportedError(f"FInPredicate does not support Uninterpreted Functions.")
                else:
                    if isinstance(src_attr, FAttribute) and src_attr.EXPR is not None:
                        src_attr_tuple = src_attr.__expr__(args, **kwargs)
                    else:
                        src_attr_tuple = self.visit(src_attr)(args, **kwargs)
                src_attr_tuples.append(src_attr_tuple)

            prev_table = self.visit(formulas.operands[1], **outer_kwargs)
            all_del_formula = And(*[self._DEL(prev_tuple.SORT) for prev_tuple in prev_table.values()])
            null_exist_formula = Or(*[src_attr_tuple.NULL for src_attr_tuple in src_attr_tuples])
            in_formula = []
            null_list = []
            for prev_tuple in prev_table.values():
                tmp = []
                # pair_are_null = []
                for src_attr_tuple, dst_attr in zip(src_attr_tuples, prev_tuple.attributes):
                    dst_attr_tuple = self.visit(dst_attr)(prev_tuple.SORT)
                    tmp.append(
                        simplify([
                            Not(self._DEL(prev_tuple.SORT)),
                            encode_same(src_attr_tuple.NULL, dst_attr_tuple.NULL, src_attr_tuple.VALUE,
                                        dst_attr_tuple.VALUE)
                        ], operator=And)
                    )
                    null_list.append(And(Not(self._DEL(prev_tuple.SORT)), dst_attr_tuple.NULL))
                in_formula.append(simplify(tmp, operator=And))
            in_formula = Or(*in_formula)
            return FExpressionTuple(
                # is NULL?
                And(
                    Not(all_del_formula),
                    Or(
                        null_exist_formula,
                        And(Not(in_formula), Or(*null_list)),
                    )
                ),
                # VALUE?
                And(
                    Not(all_del_formula),
                    And(in_formula, Not(null_exist_formula)),
                ),
            )

        return _f

    @visitor(FExistsPredicate)
    def visit(self, formulas: FExistsPredicate, **outer_kwargs):

        def _f(*args, **kwargs):
            outer_attrs = outer_kwargs.get('outer_attrs', {})
            t_sort = args[0]
            for attr in self.scope.dump_tuples[str(t_sort)].attributes:
                outer_attrs[str(attr)] = self.visit(attr, **outer_kwargs)(t_sort)
            outer_kwargs['outer_attrs'] = outer_attrs
            out = []
            prev_table = self.visit(formulas[0], **outer_kwargs)
            # print(prev_table)
            for prev_tuple in prev_table.values():
                out.append(Not(self._DEL(prev_tuple.SORT)))
            return FExpressionTuple(
                NULL=Z3_FALSE,
                VALUE=Or(*out) if len(out) > 1 else out[0],
            )

        return _f

    @visitor(FNullIfPredicate)
    def visit(self, formulas: FNullIfPredicate, **kwargs):

        def _f(*args, **kwargs):
            lhs_attr, rhs_attr = formulas.operands
            lhs_attr = self.visit(lhs_attr)(*args, **kwargs)
            rhs_attr = self.visit(rhs_attr)(*args, **kwargs)
            return FExpressionTuple(
                NULL=Or(lhs_attr.NULL, lhs_attr.VALUE == rhs_attr.VALUE),
                VALUE=lhs_attr.VALUE,
            )

        return _f

    @visitor(FCoalescePredicate)
    def visit(self, formulas: FCoalescePredicate, **kwargs):
        # expressions = [self.visit(operand) for operand in formulas.operands]
        expressions = formulas.operands

        def _directly_app(x):
            return (isinstance(x, list) and len(x) > 1) or isinstance(x, ExprRef)

        def _f(exprs, args, **kwargs):
            constraints = []

            def __f(expr, args, **kwargs):
                if isinstance(expr, FAttribute):
                    if _directly_app(args):
                        if isinstance(args, list):
                            if len(args) == 1:
                                args = args[0]
                            else:
                                if 'first_non_deleted_tuple_sort' in kwargs:
                                    args = kwargs['first_non_deleted_tuple_sort']
                                else:
                                    args, find_constraint = self._find_1st_non_deleted_tuple_sort(args)
                                    if find_constraint is not None:
                                        constraints.append(find_constraint)
                        expr = self.visit(expr)(args, **kwargs)
                    else:
                        expr = self.visit(expr)(*args, **kwargs)
                    return FExpressionTuple(expr.NULL, expr.VALUE)
                elif isinstance(expr, FExpression | FExpressionTuple) or is_uninterpreted_func(expr):
                    expr = self.visit(expr)(args, **kwargs) if _directly_app(args) \
                        else self.visit(expr)(*args, **kwargs)
                    return expr
                elif getattr(expr, 'require_tuples', False):
                    return self.visit(expr)(args, **kwargs)
                elif isinstance(expr, FDigits):
                    return self.visit(expr)(args, **kwargs)
                elif isinstance(expr, ArithRef):
                    return FExpressionTuple(Z3_FALSE, expr)
                else:
                    raise NotImplementedError(expressions)

            expr_res = []
            for expr in exprs:
                expr_res.append(__f(expr, args, **kwargs))
                if isinstance(expr, FDigits | ArithRef):
                    break

            NULL = expr_res[-1].NULL
            for expr in expr_res[:-1][::-1]:
                NULL = If(expr.NULL, NULL, Z3_FALSE)
            VALUE = expr_res[-1].VALUE
            for expr in expr_res[:-1][::-1]:
                if type(VALUE) != type(expr.VALUE):
                    if isinstance(VALUE, BoolRef):
                        VALUE = If(formulas, Z3_1, Z3_0)
                    if isinstance(expr.VALUE, BoolRef):
                        else_clause = If(expr.VALUE, Z3_1, Z3_0)
                    else:
                        else_clause = expr.VALUE
                    VALUE = If(expr.NULL, VALUE, else_clause)
                else:
                    VALUE = If(expr.NULL, VALUE, expr.VALUE)

            if len(constraints) > 0:
                self.scope.register_formulas(
                    formulas=CodeSnippet(code=And(*constraints), docstring=f'{formulas} COALESCE constraint',
                                         docstring_first=True)
                )
            return FExpressionTuple(NULL, VALUE)

        return IntermFunc(
            z3_function=lambda args, **kwargs: _f(expressions, args, **kwargs),
            description=f'COALESCE({formulas.operands})'
        )

    @visitor(FRound)
    def visit(self, formulas: FRound, **kwargs):
        return formulas

    @visitor(FIfPredicate)
    def visit(self, formulas: FIfPredicate, **kwargs):
        cond = self.visit(formulas[0])
        then_clause = self.visit(formulas[1])
        else_clause = self.visit(formulas[2])
        return IntermFunc(
            z3_function=lambda x, **kwargs: If(cond(x), then_clause(x), else_clause(x)),
            description=f'If ({formulas[0]}) then {formulas[1]} else {formulas[2]}',
        )

    @visitor(FNull)
    def visit(self, formula: FNull, **kwargs):
        # SELECT NULL
        return lambda x, **kwargs: FExpressionTuple(Z3_TRUE, Z3_NULL_VALUE)

    @visitor(FIsNullPredicate)
    def visit(self, condition: FIsNullPredicate, **kwargs):
        def _f(x, **kwargs):
            if getattr(condition[0], 'require_tuples', False):
                attr_tuple = self.visit(condition.value)(x, **kwargs)
                return FExpressionTuple(Z3_FALSE, attr_tuple.NULL)
            else:
                if 'group_func' in kwargs:
                    # WITH A AS (SELECT PLAYER_ID, MIN(EVENT_DATE) AS INSTALL_DT FROM ACTIVITY GROUP BY PLAYER_ID) , B AS (SELECT T.EVENT_DATE, IFNULL(COUNT(T.PLAYER_ID),0) AS CT FROM A LEFT JOIN ACTIVITY T ON T.PLAYER_ID = A.PLAYER_ID WHERE T.EVENT_DATE = A.INSTALL_DT+1 GROUP BY T.EVENT_DATE) SELECT INSTALL_DT, COUNT(*) AS INSTALLS, ROUND(IFNULL(B.CT,0)/COUNT(*),2) AS DAY1_RETENTION FROM A LEFT JOIN B ON A.INSTALL_DT = B.EVENT_DATE-1 GROUP BY INSTALL_DT
                    if 'first_non_deleted_tuple_sort' in kwargs:
                        first_tuple = kwargs['first_non_deleted_tuple_sort']
                    else:
                        first_tuple, _find_constraints = self._find_1st_non_deleted_tuple_sort(x, del_func=kwargs[
                            'group_func'])
                        if _find_constraints is not None:
                            self.scope.register_formulas(formulas=CodeSnippet(code=_find_constraints,
                                                                              docstring=f'constraint for {condition}'))
                    return FExpressionTuple(
                        Z3_FALSE,
                        And(kwargs['group_func'](first_tuple), self.visit(condition.value)(first_tuple, **kwargs).NULL),
                    )
                else:
                    attr_tuple = self.visit(condition.value)(x[0] if isinstance(x, Sequence) else x, **kwargs)
                    return FExpressionTuple(Z3_FALSE, attr_tuple.NULL)

        return _f

    @visitor(FIsNotNullPredicate)
    def visit(self, condition: FIsNotNullPredicate, **kwargs):

        def _f(x, **kwargs):
            if getattr(condition[0], 'require_tuples', False):
                attr_tuple = self.visit(condition.value)(x, **kwargs)
                return FExpressionTuple(Z3_FALSE, Not(attr_tuple.NULL))
            else:
                if 'group_func' in kwargs:
                    if 'first_non_deleted_tuple_sort' in kwargs:
                        first_tuple = kwargs['first_non_deleted_tuple_sort']
                    else:
                        first_tuple, _find_constraints = self._find_1st_non_deleted_tuple_sort(x, del_func=kwargs[
                            'group_func'])
                        if _find_constraints is not None:
                            self.scope.register_formulas(formulas=CodeSnippet(code=_find_constraints,
                                                                              docstring=f'constraint for {condition}'))
                    return FExpressionTuple(
                        Z3_FALSE,
                        And(kwargs['group_func'](first_tuple),
                            Not(self.visit(condition.value)(first_tuple, **kwargs).NULL)),
                    )
                else:
                    attr_tuple = self.visit(condition.value)(x[0] if isinstance(x, Sequence) else x, **kwargs)
                    return FExpressionTuple(Z3_FALSE, Not(attr_tuple.NULL))

        return _f

    @visitor(FIsTruePredicate)
    def visit(self, condition: FIsTruePredicate, **kwargs):

        def _f(*args, **kwargs):
            if isinstance(condition.value, FBaseTable):
                if len(condition.value.attributes) != 1:
                    raise NotImplementedError("Query in `Query is True` must have one attribute")
                attr = condition.value.attributes[0]
                self.scope.register_formulas(
                    formulas=CodeSnippet(code=Sum(*[self._DEL(t.SORT) for t in condition.value]) <= Z3_1,
                                         docstring=f'{self.__class__.__name__} constraint',
                                         docstring_first=True)
                )
                self.visit(condition.value)  # visit the nested table
                vars = []
                for t in condition.value:
                    attr_tuple = self.visit(attr)(t.SORT)
                    vars.append(And(Not(self._DEL(t.SORT)), Not(attr_tuple.NULL), attr_tuple.VALUE != Z3_0))
                return FExpressionTuple(Z3_FALSE, Or(*vars))
            else:
                attr_tuple = self.visit(condition.value)(*args, **kwargs)
                # only return true/false
                if isinstance(attr_tuple.VALUE, ArithRef | ExcutableType):
                    attr_tuple.VALUE = attr_tuple.VALUE != Z3_0
                return FExpressionTuple(Z3_FALSE, And(Not(attr_tuple.NULL), attr_tuple.VALUE))

        return _f

    @visitor(FIsFalsePredicate)
    def visit(self, condition: FIsFalsePredicate, **kwargs):

        def _f(*args, **kwargs):
            if isinstance(condition.value, FBaseTable):
                if len(condition.value.attributes) != 1:
                    raise NotImplementedError("Query in `Query is False` must have one attribute")
                attr = condition.value.attributes[0]
                self.scope.register_formulas(
                    formulas=CodeSnippet(code=Sum(*[self._DEL(t.SORT) for t in condition.value]) <= Z3_1,
                                         docstring=f'{self.__class__.__name__} constraint',
                                         docstring_first=True)
                )
                self.visit(condition.value)  # visit the nested table
                vars = []
                for t in condition.value:
                    attr_tuple = self.visit(attr)(t.SORT)
                    vars.append(And(Not(self._DEL(t.SORT)), Not(attr_tuple.NULL), attr_tuple.VALUE != Z3_0))
                return FExpressionTuple(Z3_FALSE, Not(Or(*vars)))
            else:
                attr_tuple = self.visit(condition.value)(*args, **kwargs)
                # only return true/false
                if isinstance(attr_tuple.VALUE, ExcutableType):
                    attr_tuple.VALUE = attr_tuple.VALUE == Z3_0
                return FExpressionTuple(Z3_FALSE, And(Not(attr_tuple.NULL), Not(attr_tuple.VALUE)))

        return _f

    @visitor(FIsNotTruePredicate)
    def visit(self, condition: FIsNotTruePredicate, **kwargs):

        def _f(*args, **kwargs):
            attr_tuple = self.visit(condition.value)(*args, **kwargs)
            # only return true/false
            if isinstance(attr_tuple.VALUE, ExcutableType):
                attr_tuple.VALUE = attr_tuple.VALUE == Z3_0
            return FExpressionTuple(Z3_FALSE, Or(attr_tuple.NULL, Not(attr_tuple.VALUE)))

        return _f

    @visitor(FIsNotFalsePredicate)
    def visit(self, condition: FIsNotFalsePredicate, **kwargs):

        def _f(*args, **kwargs):
            attr_tuple = self.visit(condition.value)(*args, **kwargs)
            # only return true/false
            if isinstance(attr_tuple.VALUE, ExcutableType):
                attr_tuple.VALUE = attr_tuple.VALUE != Z3_0
            return FExpressionTuple(Z3_FALSE, Or(attr_tuple.NULL, attr_tuple.VALUE))

        return _f

    ############################ data structure ############################

    @visitor(list)
    def visit(self, formula: list, **kwargs):
        return [self.visit(f) for f in formula]

    @visitor(OrderedSet)
    def visit(self, formula: OrderedSet, **kwargs):
        return OrderedSet([self.visit(f) for f in formula])

    ############################ type ############################

    @visitor(NumericType)
    def visit(self, formula: NumericType, **kwargs):
        return formula

    @visitor(FDigits)
    def visit(self, formula: FDigits, **kwargs):
        if isinstance(formula.value, bool):
            value = Z3_TRUE if formula.value else Z3_FALSE
            return lambda *args, **kwargs: FExpressionTuple(Z3_FALSE, value)
        else:
            _const_ = IntVal(str(formula.value)) if isinstance(formula.value, int) \
                else RealVal(str(formula.value))
            return lambda *args, **kwargs: FExpressionTuple(Z3_FALSE, _const_)

    @visitor(bool)
    def visit(self, formula: bool, **kwargs):
        return lambda *args, **kwargs: FExpressionTuple(Z3_FALSE, BoolVal(formula))

    @visitor(BoolRef)
    def visit(self, formula: BoolRef, **kwargs):
        return lambda *args, **kwargs: FExpressionTuple(Z3_FALSE, formula)

    @visitor(ArithRef)
    def visit(self, formula: ArithRef, **kwargs):
        return lambda *args, **kwargs: FExpressionTuple(Z3_FALSE, formula)

    @functools.lru_cache()
    @visitor(FAttribute)
    def visit(self, formulas: FAttribute, **outer_kwargs):
        def _f(args, **kwargs):
            if 'first_non_deleted_tuple_sort' in kwargs:
                args = kwargs['first_non_deleted_tuple_sort']
            if isinstance(args, tuple | list):
                args = args[0]
            if str(formulas) in outer_kwargs.get('outer_attrs', {}):
                return outer_kwargs['outer_attrs'][str(formulas)]
            else:
                NULL = formulas.NULL(args)
                if kwargs.get('pity_flag', False):
                    NULL = Or(NULL, self._DEL(args))
                return FExpressionTuple(
                    NULL=NULL,
                    VALUE=formulas.VALUE(args),
                )

        return _f

    @visitor(FSymbol)
    def visit(self, formula: FSymbol, **kwargs):
        return FExpressionTuple(Z3_FALSE, lambda *args, **kwargs: self.scope._get_variable(formula))

    @visitor(FField)
    def visit(self, formula: FField, **kwargs):
        attribute = self.visit(formula.attribute)
        value = self.visit(formula.value)
        ifunction = IntermFunc(
            z3_function=lambda x, **kwargs: formula.operator(attribute(x), value),
            description=f'{attribute} {formula.operator} {formula.value}',
        )
        return ifunction

    @visitor(FNullTuple)
    def visit(self, formulas: FNullTuple, **kwargs):
        dum_tuple = DumpTuple(
            name=formulas.name, sort=formulas.SORT,
            attributes=formulas.attributes,
            parent_sorts=None,
        )
        self.scope.register_dump_tuple(dum_tuple.name, dum_tuple)

        code = And(*[
            Not(self._DEL(dum_tuple.SORT)),
            *[
                attr.NULL(dum_tuple.SORT)
                for attr in dum_tuple.attributes
            ]
        ])
        implication = CodeSnippet(code=code, docstring=str(dum_tuple), docstring_first=True)
        self.scope.register_formulas(formulas=implication)
        return dum_tuple

    @visitor(FBaseTuple)
    def visit(self, formulas: FBaseTuple, **kwargs):
        dum_tuple = DumpTuple(name=formulas.name, sort=formulas.SORT, attributes=formulas.attributes)
        self.scope.register_dump_tuple(dum_tuple.name, dum_tuple)
        return dum_tuple

    @visitor(FValueTable)
    def visit(self, formulas: FValueTable, **kwargs):
        # prev_table = self.visit(formulas.fathers[0])
        # assert len(formulas) == 1 and len(formulas.attributes) == 1, AssertionError(str(formulas))
        return formulas.attributes[0](formulas[0].SORT)

    @visitor(FAbsPredicate)
    def visit(self, formulas: FAbsPredicate, **kwargs):
        def _f(*args, **kwargs):
            expr = self.visit(formulas[0])(*args, **kwargs)
            if isinstance(expr.VALUE, BoolRef):
                expr.VALUE = If(expr.VALUE, Z3_1, Z3_0)
            return FExpressionTuple(
                expr.NULL,
                If(expr.VALUE < Z3_0, -expr.VALUE, expr.VALUE)
            )

        return _f

    @visitor(FPowerPredicate)
    def visit(self, formulas: FPowerPredicate, **kwargs):
        def _f(*args, **kwargs):
            base = self.visit(formulas[0])(*args, **kwargs)
            exponent = self.visit(formulas[1])(*args, **kwargs)
            return FExpressionTuple(
                Or(base.NULL, exponent.NULL),
                base.VALUE ** exponent.VALUE,
            )

        return _f

    @visitor(FModPredicate)
    def visit(self, formulas: FModPredicate, **kwargs):
        def _f(*args, **kwargs):
            expr0 = self.visit(formulas[0])(*args, **kwargs)
            expr1 = self.visit(formulas[1])(*args, **kwargs)
            return FExpressionTuple(
                Or(expr0.NULL, expr1.NULL),
                expr0.VALUE % expr1.VALUE,
            )

        return _f

    @visitor(FExpressionTuple)
    def visit(self, formulas: FExpressionTuple, **kwargs):
        def _f(*args, **kwargs):
            return formulas

        return _f

    @visitor(FLastValuePredicate)
    def visit(self, formulas: FLastValuePredicate, **kwargs):
        def _f(*args, **kwargs):
            expr = self.visit(formulas[0])(*args, **kwargs)
            return expr

        return _f

    @visitor(FIsNullOrHoldPredicate)
    def visit(self, formulas: FIsNullOrHoldPredicate, **kwargs):
        def _f(*args, **kwargs):
            expr = self.visit(formulas[0])(*args, **kwargs)
            if not isinstance(expr.VALUE, BoolRef | bool):
                expr.VALUE = expr.VALUE != Z3_0
            return FExpressionTuple(Z3_FALSE, Or(expr.NULL, expr.VALUE))

        return _f

    @visitor(FCasePredicate)
    def visit(self, formulas: FCasePredicate, **kwargs):
        def _f(*args, **kwargs):

            if getattr(formulas.else_clause, 'require_tuples', False):
                else_clause = self.visit(formulas.else_clause)(*args, **kwargs)
            else:
                if isinstance(args[0], list | tuple) and len(args[0]) > 1 and \
                        kwargs.get('first_non_deleted_tuple_sort', None) is None:
                    # SELECT (CASE) + GROUP BY
                    else_clause = self.visit(formulas.else_clause)(args[0][0])
                else:
                    else_clause = self.visit(formulas.else_clause)(*args, **kwargs)
            for if_clause, then_clause in zip(formulas.when_clauses[::-1], formulas.then_clauses[::-1]):
                if getattr(then_clause, 'require_tuples', False):
                    then_clause = self.visit(then_clause)(*args, **kwargs)
                else:
                    if isinstance(args[0], list | tuple) and len(args[0]) > 1:
                        # SELECT (CASE) + GROUP BY
                        then_clause = self.visit(then_clause)(args[0][0], **kwargs)
                    else:
                        then_clause = self.visit(then_clause)(*args, **kwargs)
                if_clause = self.visit(if_clause)(*args, **kwargs)
                if isinstance(if_clause.VALUE, NumericType):
                    if_clause.VALUE = if_clause.VALUE != Z3_0
                if isinstance(if_clause.VALUE, ArithRef | int | float):
                    bool_premise = And(Not(if_clause.NULL), if_clause.VALUE != Z3_0)
                else:
                    bool_premise = And(Not(if_clause.NULL), if_clause.VALUE)

                if then_clause.NULL == else_clause.NULL:
                    else_clause_null = then_clause.NULL
                else:
                    else_clause_null = If(
                        bool_premise,  # Not NULL or cond
                        then_clause.NULL,
                        else_clause.NULL,
                    )

                # to align the type in then and else (bool -> int by default)
                if isinstance(then_clause.VALUE, bool | BoolRef) and \
                        isinstance(else_clause.VALUE, int | ArithRef):
                    then_clause.VALUE = If(then_clause.VALUE, Z3_1, Z3_0)
                elif isinstance(then_clause.VALUE, int | ArithRef) and \
                        isinstance(else_clause.VALUE, bool | BoolRef):
                    else_clause.VALUE = If(else_clause.VALUE, Z3_1, Z3_0)

                if then_clause.VALUE == else_clause.VALUE:
                    else_clause_value = then_clause.VALUE
                else:
                    else_clause_value = If(
                        bool_premise,  # Not NULL or cond
                        then_clause.VALUE,
                        else_clause.VALUE,
                    )

                else_clause = FExpressionTuple(NULL=else_clause_null, VALUE=else_clause_value)
            return else_clause

        return _f

    @visitor(FEmptyTable)
    def visit(self, formulas: FEmptyTable, **kwargs):
        curr_table = {}
        for curr_tuple in formulas:
            curr_tuple = DumpTuple(
                name=curr_tuple.name, sort=curr_tuple.SORT,
                attributes=curr_tuple.attributes, parent_sorts=[],
            )
            self.scope.register_dump_tuple(curr_tuple.name, curr_tuple)
            curr_table[curr_tuple.name] = curr_tuple
        return curr_table

    @visitor(FSymbolicFunc)
    def visit(self, formulas: FSymbolicFunc, **kwargs):
        parameters = []
        sorts = []
        for table in formulas:
            if isinstance(table, FBaseTable):
                for tuple in table:
                    parameters.append(self.scope.DELETED_FUNCTION(tuple.SORT))
                    sorts.append(self.scope.BooleanSort)
                    for attr in tuple.attributes:
                        attr_tuple = self.scope.visitor.visit(attr)(tuple.SORT)
                        parameters.extend([attr_tuple.NULL, attr_tuple.VALUE])
                        sorts.extend([self.scope.BooleanSort, self.scope.VarSort])
            else:
                raise NotImplementedError(formulas)

        function = self.scope._get_function(formulas.operator)
        if function is None:
            function = Function(formulas.operator, *sorts, self.scope.BooleanSort)
            self.scope.register_function(__pos_hash__(formulas.operator), function)

        def _f(*args, **kwargs):
            return FExpressionTuple(
                NULL=Z3_FALSE,
                VALUE=function(*parameters),
            )

        return _f

    def detach_tuples(self, formulas):
        # only works for correlated subquery
        # e.g., WHERE s.CUSTOMERKEY IN (SELECT CustomerKey FROM CUSTOMER WHERE (CustomerKey != s.CUSTOMERKEY))
        # need to rename tuples of the table `SELECT CustomerKey FROM CUSTOMER WHERE (CustomerKey != s.CUSTOMERKEY)`
        old_name = formulas.name.rsplit('_', 1)[0]
        formulas = formulas.detach(self.scope, self.correlated_table_indices.get(old_name, 0))
        self.correlated_table_indices[old_name] = self.correlated_table_indices.get(old_name, 0) + 1
        return formulas

    def attach_tuples(self, detached_table):
        # attach tuples of correlated subquery into outer query
        # attached_table = {}
        # for key, value in detached_table.items():
        #     name = key.rsplit('_')[0]
        #     value.name = name
        #     attached_table[name] = value
        attached_table = {key.rsplit('_')[0]: value for key, value in detached_table.items()}
        return attached_table
