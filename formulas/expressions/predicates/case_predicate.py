# -*- coding: utf-8 -*-

from errors import NotSupportedError
from formulas import register_formula
from formulas.expressions.operator import FOperator
from formulas.expressions.predicates.base_predicate import FBasePredicate


@register_formula('case_predicate')
class FCasePredicate(FBasePredicate):
    def __init__(self, clauses):
        super(FCasePredicate, self).__init__(
            operator=FOperator('or'),
            operands=clauses,
        )
        # broadcast uninterpreted function
        # only works for the case where returned values are number or uninterpreted function
        from formulas.expressions.digits import FDigits
        candidate_clauses = [
            clause
            for clause in self.then_clauses + [self.else_clause]
            if not isinstance(clause, FDigits)
        ]
        uninterpreted_func = None
        for clause in candidate_clauses:
            if getattr(clause, 'is_uninterpreted_func', False):
                if uninterpreted_func is not None and uninterpreted_func != clause.uninterpreted_func:
                    raise NotSupportedError(f"CASE has different uninterpreted functions")
                uninterpreted_func = clause.uninterpreted_func
        if uninterpreted_func is not None:
            for clause in self.then_clauses + [self.else_clause]:
                clause.uninterpreted_func = None
            self.uninterpreted_func = uninterpreted_func

    @property
    def when_clauses(self):
        return [self[i] for i in range(0, len(self) - 1, 2)]

    @property
    def then_clauses(self):
        return [self[i] for i in range(1, len(self) - 1, 2)]

    @property
    def else_clause(self):
        return self[-1]

    def __str__(self):
        # cases = ', '.join([f'[{when} → {then}]' for when, then in zip(self.when_clauses, self.then_clauses)])
        # return f"CASE {cases} ELSE [{self.else_clause}]"
        out = ''.join([f'__{when}_Implies_{then}__' for when, then in zip(self.when_clauses, self.then_clauses)])
        out += str(self.else_clause)
        return out

    @property
    def CASE_SIZE(self):
        return (len(self) + 1) // 2
