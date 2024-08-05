# -*- coding: utf-8 -*-

from z3 import (
    ArithRef,
)

from constants import (
    NumericType,
    Or,
    And,
    Not,
    Implies,
    If,
    Sum,
    Z3_1,
    Z3_0,
)
from formulas.columns import *
from formulas.expressions import *
from utils import (
    encode_same,
    CodeSnippet,
)
from verifiers.verifier import (
    Verifier,
)


class BagSemanticsVerifier(Verifier):
    def __init__(self, environment):
        super(BagSemanticsVerifier, self).__init__(environment)

    def z3(self, left_attributes, right_attributes, **kwargs):
        DELETED_func_str = str(self._env.DELETED_FUNCTION)

        def _attr2str(attribute, tuple_sort):
            if isinstance(attribute, FAttribute):
                if isinstance(attribute.EXPR, FDigits):
                    return f"{attribute.EXPR.value}"
                elif isinstance(attribute.EXPR, NumericType | ArithRef):
                    return f"{attribute.EXPR}"
                else:
                    return f"{attribute.VALUE}({tuple_sort})"
            else:
                return f"{str(attribute.VALUE).replace('?', tuple_sort)}"

        def _tuple_equals(left_attributes, right_attributes):
            equalities = []
            for attr_pair in zip(left_attributes, right_attributes):
                attr_nulls, attr_values = [], []
                for attr, tuple_sort in zip(attr_pair, [self._env.Tuple1, self._env.Tuple2]):
                    attr_nulls.append(f"{str(attr.NULL).replace('?', tuple_sort)}")
                    attr_values.append(_attr2str(attr, tuple_sort))
                formula = f"""
Or(And({attr_nulls[0]}, {attr_nulls[1]}), And(Not({attr_nulls[0]}), Not({attr_nulls[1]}), {attr_values[0]} == {attr_values[1]})),
""".strip()
                equalities.append(formula)
            equalities = "\n".join(equalities)
            return f"""
Or(
    And({DELETED_func_str}({self._env.Tuple1}), {DELETED_func_str}({self._env.Tuple2})),
    And(
        Not({DELETED_func_str}({self._env.Tuple1})),
        Not({DELETED_func_str}({self._env.Tuple2})),
        {equalities}
    )
)
""".strip()

        if len(self.additional_conclusion) > 0:
            additional_conclusions = '\n\n'.join(str(conclusion) for conclusion in self.additional_conclusion)
            additional_conclusions = f'    formulas.append(\n{additional_conclusions}\n)'
        else:
            additional_conclusions = ''
        code = f"""
def equals(ltuples, rtuples):
    left_left_function = lambda {self._env.Tuple1}, {self._env.Tuple2}: {_tuple_equals(left_attributes, left_attributes)}
    left_right_function = lambda {self._env.Tuple1}, {self._env.Tuple2}: {_tuple_equals(left_attributes, right_attributes)}
    right_left_function = lambda {self._env.Tuple1}, {self._env.Tuple2}: {_tuple_equals(right_attributes, left_attributes)}
    right_right_function = lambda {self._env.Tuple1}, {self._env.Tuple2}: {_tuple_equals(right_attributes, right_attributes)}

    formulas = [
        Sum([If({DELETED_func_str}(tuple_sort), 0, 1) for tuple_sort in ltuples]) == \
        Sum([If({DELETED_func_str}(tuple_sort), 0, 1) for tuple_sort in rtuples])
    ]
    for tuple_sort in ltuples:
        count_in_ltuples = Sum([If(left_left_function(tuple_sort, t), 1, 0) for t in ltuples])
        count_in_rtuples = Sum([If(left_right_function(tuple_sort, t), 1, 0) for t in rtuples])
        formulas.append(
            Implies(
                Not({DELETED_func_str}(tuple_sort)),
                count_in_ltuples == count_in_rtuples,
            )
        )
    for tuple_sort in rtuples:
        count_in_ltuples = Sum([If(right_left_function(tuple_sort, t), 1, 0) for t in ltuples])
        count_in_rtuples = Sum([If(right_right_function(tuple_sort, t), 1, 0) for t in rtuples])
        formulas.append(
            Implies(
                Not({DELETED_func_str}(tuple_sort)),
                count_in_ltuples == count_in_rtuples,
            )
        )
{additional_conclusions}
    formulas = And(formulas)
    return formulas
    """.strip()
        return CodeSnippet(code)

    def table_equivalence(self, ltable, rtable, left_attributes, right_attributes, **kwargs):
        # |lhs_table| = |rhs_table|, to accelerate
        formulas = [
            self._table_size(ltable) == self._table_size(rtable)
        ]

        cmp_funcs = self.cmp_funcs(left_attributes, right_attributes)
        lhs_tuple_values = self.tuple_values(ltable.values(), left_attributes, cmp_funcs)
        rhs_tuple_values = self.tuple_values(rtable.values(), right_attributes, cmp_funcs)
        tuple_values = lhs_tuple_values + rhs_tuple_values
        cmp_formulas = {}
        for i, lhs_value in enumerate(tuple_values):
            for j, rhs_value in enumerate(tuple_values[i:], start=i):
                if i == j:
                    cmp_formulas[(i, j)] = Z3_1
                else:
                    equalities = []
                    for lhs_attr, rhs_attr in zip(lhs_value[1:], rhs_value[1:]):
                        if isinstance(lhs_attr, list):
                            equalities.append(encode_same(lhs_attr[0], rhs_attr[0], lhs_attr[1], rhs_attr[1]))
                        else:
                            equalities.append(lhs_attr == rhs_attr)
                    cmp_formulas[(i, j)] = cmp_formulas[(j, i)] = If(
                        Or(
                            And(lhs_value[0], rhs_value[0]),
                            And(Not(lhs_value[0]), Not(rhs_value[0]), *equalities),
                        ), Z3_1, Z3_0
                    )

        lhs_table_num, rhs_table_num = len(ltable), len(rtable)
        for idx, tuple in enumerate(ltable.values()):
            count_in_ltuples = Sum(*[cmp_formulas[idx, j] for j in range(lhs_table_num)])
            count_in_rtuples = Sum(*[cmp_formulas[idx, j] for j in range(lhs_table_num, lhs_table_num + rhs_table_num)])
            formulas.append(
                Implies(
                    Not(self._env.DELETED_FUNCTION(tuple.SORT)),
                    count_in_ltuples == count_in_rtuples,
                )
            )
        for idx, tuple in enumerate(rtable.values(), start=lhs_table_num):
            count_in_ltuples = Sum(*[cmp_formulas[idx, j] for j in range(lhs_table_num)])
            count_in_rtuples = Sum(*[cmp_formulas[idx, j] for j in range(lhs_table_num, lhs_table_num + rhs_table_num)])
            formulas.append(
                Implies(
                    Not(self._env.DELETED_FUNCTION(tuple.SORT)),
                    count_in_ltuples == count_in_rtuples,
                )
            )

        formulas = And(*formulas)
        return formulas
