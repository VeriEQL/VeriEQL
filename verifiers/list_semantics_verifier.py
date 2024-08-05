# -*- coding: utf-8 -*-

from constants import (
    And,
    Or,
    Not,
    Implies,
)
from formulas.columns import FAttribute
from utils import (
    encode_same,
    CodeSnippet,
)
from verifiers.verifier import (
    Verifier,
)


class ListSemanticsVerifier(Verifier):

    def __init__(self, environment):
        super(ListSemanticsVerifier, self).__init__(environment)
        self._DEL = self._env.DELETED_FUNCTION

    def z3(self, left_attributes, right_attributes, **kwargs):
        DELETED_func_str = str(self._env.DELETED_FUNCTION)

        def _tuple_equals(left_attributes, right_attributes):
            equalities = []
            for lattr, rattr in zip(left_attributes, right_attributes):
                if isinstance(lattr, FAttribute):
                    formula = [f"{lattr.VALUE}({self._env.Tuple1})",
                               f"{rattr.VALUE}({self._env.Tuple2})"]
                else:
                    formula = [f"{str(lattr.VALUE).replace('?', self._env.Tuple1)}",
                               "{str(rattr.VALUE).replace('?', self._env.Tuple2)}"]
                formula = f"""
If({str(lattr.NULL).replace('?', self._env.Tuple1)}, 0, {formula[0]}) == \\
If({str(rattr.NULL).replace('?', self._env.Tuple2)}, 0, {formula[1]}),
""".strip()
                # equalities.append(CodeSnippet(code=formula, docstring=f'{lattr} == {rattr}', docstring_first=True))
                equalities.append(formula)
            equalities = "\n".join(equalities)
            return f"""
And(
    And({DELETED_func_str}({self._env.Tuple1}) == {DELETED_func_str}({self._env.Tuple2})),
    Implies(
        And(
            Not({DELETED_func_str}({self._env.Tuple1})),
            Not({DELETED_func_str}({self._env.Tuple2})),
        ),
        And(
        {equalities}
        ),
    ),   
)
""".strip()

        if len(self.additional_conclusion) > 0:
            additional_conclusions = '\n\n'.join(str(conclusion) for conclusion in self.additional_conclusion)
            additional_conclusions = f'    formulas.append(\n{additional_conclusions}\n)'
        else:
            additional_conclusions = ''
        code = f"""
def equals(ltuples, rtuples):
    _func = lambda {self._env.Tuple1}, {self._env.Tuple2}: {_tuple_equals(left_attributes, right_attributes)}

    formulas = []
    for ltuple, rtuple in zip(ltuples, rtuples):
        formulas.append(_func(ltuple, rtuple))
        
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

        for lhs_value, rhs_value in zip(lhs_tuple_values, rhs_tuple_values):
            equalities = []
            for lhs_attr, rhs_attr in zip(lhs_value[1:], rhs_value[1:]):
                if isinstance(lhs_attr, list):
                    equalities.append(encode_same(lhs_attr[0], rhs_attr[0], lhs_attr[1], rhs_attr[1]))
                else:
                    equalities.append(lhs_attr == rhs_attr)
            formulas.append(
                Or(
                    And(lhs_value[0], rhs_value[0]),  # both deleted
                    Implies(
                        And(Not(lhs_value[0]), Not(rhs_value[0])),
                        And(*equalities),
                    )
                )
            )

        formulas = And(*formulas)
        return formulas
