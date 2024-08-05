# -*- coding: utf-8 -*-

import abc

from z3 import (
    ArithRef,
)

from constants import (
    And,
    Implies,
    If,
    Sum,
    Z3_1,
    Z3_0,
)
from errors import NotEquivalenceError
from formulas.columns import *
from formulas.expressions import *
from utils import CodeSnippet
from writers.code_writer import CodeWriter

ExcutableType = FDigits | int | float | ArithRef


class Verifier:
    def __init__(self, environment):
        self._env = environment
        self._DEL = self._env.DELETED_FUNCTION
        self.reset()

    def _table_size(self, table):
        return Sum(*[If(self._DEL(tuple.SORT), Z3_0, Z3_1) for tuple in table.values()])

    @abc.abstractmethod
    def tuple_equivalence(self, *args, **kwargs):
        """
        define the equivalence of 2 tuples
        """
        pass

    @abc.abstractmethod
    def table_equivalence(self, *args, **kwargs):
        """
        define the equivalence of 2 tables
        """
        pass

    def cmp_funcs(self, left_attributes, right_attributes):
        cmp_funcs = []
        for lattr, rattr in zip(left_attributes, right_attributes):
            if getattr(lattr, 'is_uninterpreted_func', False) ^ getattr(rattr, 'is_uninterpreted_func', False):
                raise NotEquivalenceError
            if getattr(lattr, 'is_uninterpreted_func', False) and getattr(rattr, 'is_uninterpreted_func', False) and \
                    lattr.uninterpreted_func != rattr.uninterpreted_func:
                # compare uninterpreted function here
                raise NotEquivalenceError
            if isinstance(lattr, FAttribute) and isinstance(rattr, FAttribute):
                cmp_funcs.append(True)  # use encode_same
            elif isinstance(lattr, ExcutableType) and isinstance(rattr, ExcutableType):
                cmp_funcs.append(False)  # not use encode_same
            else:
                # print("One query contains an uninterpreted function, but the other one does not.")
                raise NotEquivalenceError
        return cmp_funcs

    def tuple_values(self, tuples, attributes, cmp_funcs):
        tuple_values = []
        for idx, tuple in enumerate(tuples):
            tmp = [self._env.DELETED_FUNCTION(tuple.SORT)]
            for lattr, cmp_func in zip(attributes, cmp_funcs):
                if cmp_func:
                    tmp.append([lattr.NULL(tuple.SORT), lattr.VALUE(tuple.SORT)])
                else:
                    tmp.append(lattr)
            tuple_values.append(tmp)
        return tuple_values

    def run(self, ltable, rtable, lformulas, rformulas, left_attributes, right_attributes, **kwargs):
        lresult = [code_snippet.code for code_snippet in lformulas]
        rresult = [code_snippet.code for code_snippet in rformulas]
        premise = []
        premise.extend(self._env.DBMS_facts)
        if len(lresult) > 0:
            premise.extend(lresult)
        if len(rresult) > 0:
            premise.extend(rresult)
        if kwargs['bound_constraints'] is not None and len(kwargs['bound_constraints']) > 0:
            # premise.append(And(*list(kwargs['bound_constraints'])))
            premise.extend(kwargs['bound_constraints'])
        premise = And(*premise)

        if kwargs['orderby_constraints'][0] is not None and \
                kwargs['orderby_constraints'][1] is not None:
            # only two outermost queries have orderby claues
            from .list_semantics_verifier import ListSemanticsVerifier
            semantics_verifier = ListSemanticsVerifier(self._env)
            semantics_verifier.additional_conclusion = self.additional_conclusion
        else:
            from .bag_semantics_verifier import BagSemanticsVerifier
            semantics_verifier = BagSemanticsVerifier(self._env)

        conclusion = semantics_verifier.table_equivalence(ltable, rtable, left_attributes, right_attributes, **kwargs)
        if self._env._script_writer is not None:
            self._env._script_writer.DBMS_facts = CodeWriter(
                code=self._env.DBMS_facts,
                docstring=f'Database tuples',
            )
            if kwargs['bound_constraints'] is not None and len(kwargs['bound_constraints']) > 0:
                self._env._script_writer.bound_constraints = kwargs['bound_constraints']
            if len(lformulas) == 0:
                lformulas = True
            else:
                lformulas = ',\n\n'.join([str(code_snippet) for code_snippet in lformulas])
            lresult = CodeSnippet(code=lformulas, docstring='1st SQL query formulas', docstring_first=True)
            if len(rformulas) == 0:
                rformulas = True
            else:
                rformulas = ',\n\n'.join([str(code_snippet) for code_snippet in rformulas])
            rresult = CodeSnippet(code=rformulas, docstring='2nd SQL query formulas', docstring_first=True)
            self._env._script_writer.premise.code = [lresult, rresult]
            self._env._script_writer.final_tables = [
                CodeSnippet(code=', '.join([str(tuple.SORT) for tuple in ltable.values()])),
                CodeSnippet(code=', '.join([str(tuple.SORT) for tuple in rtable.values()])),
            ]
            self._env._script_writer.equal_func = semantics_verifier.z3(left_attributes, right_attributes, **kwargs)
        return Implies(premise, conclusion)

    @abc.abstractmethod
    def z3(self, *args, **kwargs):
        """
        convert formulas into a z3 script
        """
        pass

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

    def reset(self):
        """
        ORDER BY constraint for debug
        """
        self.additional_conclusion = []
