# -*- coding:utf-8 -*-

# sql1 = "SELECT id FROM EMP WHERE emp_age > 25"
# sql2 = "SELECT id FROM EMP WHERE NOT emp_age <= 25"

# EMP = [
#     t1 = [id=x1, name=x2, age=x3, dept_id=x4],
#     t2 = [id=x5, name=x6, age=x7, dept_id=x8],
# ]
# t1_prerequisite: Not(DELETED(t1))
# t2_prerequisite: Not(DELETED(t2))

# SELECT id FROM EMP WHERE emp_age > 25
# t3_prerequisite: And(
#                      Not(DELETED(t1)) ∧ EMP_AGE(t1) > 25 ⇒ Not(DELETED(t3)),
#                      Not(Not(DELETED(t1)) ∧ EMP_AGE(t1) > 25) ⇒ DELETED(t3),
#                  )
# t4_prerequisite: And(
#                      Not(DELETED(t2)) ∧ EMP_AGE(t2) > 25 ⇒ Not(DELETED(t4)),
#                      Not(Not(DELETED(t2)) ∧ EMP_AGE(t2) > 25) ⇒ DELETED(t4),
#                  )

# "SELECT id FROM EMP WHERE NOT emp_age <= 25"
# t5_prerequisite: And(
#                      Not(DELETED(t1)) ∧ Not(EMP_AGE(t1) <= 25) ⇒ Not(DELETED(t5)),
#                      Not(Not(DELETED(t1)) ∧ Not(EMP_AGE(t1) <= 25) ⇒ DELETED(t5),
#                  )
# t6_prerequisite: And(
#                      Not(DELETED(t2)) ∧ Not(EMP_AGE(t2) <= 25) ⇒ Not(DELETED(t6)),
#                      Not(Not(DELETED(t2)) ∧ Not(EMP_AGE(t2) <= 25) ⇒ DELETED(t6),
#                  )

import itertools

from z3 import *

T = DeclareSort('T')
DELETED = Function('DELETED', T, BoolSort())
NULL = Function('NULL', T, StringSort(), BoolSort())

emp_id = Function('EMP.id', T, IntSort())
emp_name = Function('EMP.name', T, IntSort())
emp_age = Function('EMP.emp_age', T, IntSort())
emp_dept_id = Function('EMP.dept_id', T, IntSort())
dept_id = Function('DEPT.id', T, IntSort())
dept_name = Function('DEPT.name', T, IntSort())

attr_emp_id = Const('EMP.id_str', StringSort())
attr_emp_name = Const('EMP.name_str', StringSort())
attr_emp_age = Const('EMP.age_str', StringSort())
attr_emp_dept_id = Const('EMP.dept_id_str', StringSort())
attr_dept_name = Const('DEPT.name_str', StringSort())
attr_dept_id = Const('DEPT.id_str', StringSort())

# base tuples and their values from the DBMS
t1, t2 = Consts('t1 t2', T)
x1, x2, x3, x4 = Ints('x1 x2 x3 x4')
x5, x6, x7, x8 = Ints('x5 x6 x7 x8')
# final tuples of sql1
t3, t4 = Consts('t3 t4', T)
# final tuples of sql2
t5, t6 = Consts('t5, t6', T)

solver = Solver()

DBMS_facts = And(
    Not(DELETED(t1)),
    Not(DELETED(t2)),

    emp_id(t1) == x1, emp_name(t1) == x2, emp_age(t1) == x3, emp_dept_id(t1) == x4,
    Not(NULL(t1, attr_emp_id)), Not(NULL(t1, attr_emp_name)), Not(NULL(t1, attr_emp_age)),
    Not(NULL(t1, attr_emp_dept_id)),

    emp_id(t2) == x5, emp_name(t2) == x6, emp_age(t2) == x7, emp_dept_id(t2) == x8,
    Not(NULL(t2, attr_emp_id)), Not(NULL(t2, attr_emp_name)), Not(NULL(t2, attr_emp_age)),
    Not(NULL(t2, attr_emp_dept_id)),
)

result1 = And(
    # SELECT id FROM EMP WHERE emp_age > 25
    # t1 -> t3
    Implies(
        And(Not(DELETED(t1)), emp_age(t1) > 25),
        And(
            Not(DELETED(t3)),
            emp_id(t3) == emp_id(t1), NULL(t3, attr_emp_id) == NULL(t1, attr_emp_id),
            # add more columns mappings here, if need
        ),
    ),
    Implies(Not(And(Not(DELETED(t1)), emp_age(t1) > 25)), DELETED(t3)),

    # t2 -> t4
    Implies(
        And(Not(DELETED(t2)), emp_age(t2) > 25),
        And(
            Not(DELETED(t4)),
            emp_id(t4) == emp_id(t2), NULL(t4, attr_emp_id) == NULL(t2, attr_emp_id),
            # add more columns mappings here, if need
        ),
    ),
    Implies(Not(And(Not(DELETED(t2)), emp_age(t2) > 25)), DELETED(t4)),
)

result2 = And(
    # SELECT id FROM EMP WHERE NOT emp_age <= 25
    # t1 -> t5
    Implies(
        And(Not(DELETED(t1)), Not(emp_age(t1) <= 25)),
        And(
            Not(DELETED(t5)),
            emp_id(t5) == emp_id(t1), NULL(t5, attr_emp_id) == NULL(t1, attr_emp_id),
            # add more columns mappings here, if need
        ),
    ),
    Implies(Not(And(Not(DELETED(t1)), Not(emp_age(t1) <= 25))), DELETED(t5)),

    # t2 -> t6
    Implies(
        And(Not(DELETED(t2)), Not(emp_age(t2) <= 25)),
        And(
            Not(DELETED(t6)),
            emp_id(t6) == emp_id(t2), NULL(t6, attr_emp_id) == NULL(t2, attr_emp_id),
            # add more columns mappings here, if need
        ),
    ),
    Implies(Not(And(Not(DELETED(t2)), Not(emp_age(t2) <= 25))), DELETED(t6)),
)

prerequisites = And(DBMS_facts, result1, result2)


def equals(ltuples, rtuples):
    def _tuple_equals(tuple1, tuple2):
        return And(
            And(Not(DELETED(tuple1)), Not(DELETED(tuple2))),
            Or(
                And(NULL(tuple1, attr_emp_id), NULL(tuple2, attr_emp_id)),
                emp_id(tuple1) == emp_id(tuple2),
            ),
        )

    formulas = []
    for tuple_sort in itertools.chain(ltuples, rtuples):
        count_in_ltuples = Sum([If(_tuple_equals(tuple_sort, t), 1, 0) for t in ltuples])
        count_in_rtuples = Sum([If(_tuple_equals(tuple_sort, t), 1, 0) for t in rtuples])
        formulas.append(
            Implies(
                Not(DELETED(tuple_sort)),
                count_in_ltuples == count_in_rtuples,
            )
        )
    formulas = And(formulas)
    return formulas


conclusion = equals(ltuples=[t3, t4], rtuples=[t5, t6])

solver.add(Not(
    Implies(prerequisites, conclusion)
))

if solver.check() == sat:
    print(solver.model())

print(solver.check())
