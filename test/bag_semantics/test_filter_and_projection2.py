# -*- coding:utf-8 -*-

# sql1 = "SELECT name FROM (SELECT name, emp_age, id FROM EMP WHERE emp_age > 25) WHERE emp_age < 30"
# sql2 = "SELECT name FROM (SELECT id, name, emp_age FROM EMP WHERE emp_age < 30) WHERE emp_age > 25"

# EMP = [
#     t1 = [id=x1, name=x2, age=x3, dept_id=x4],
#     t2 = [id=x5, name=x6, age=x7, dept_id=x8],
# ]
# t1_prerequisite: Not(DELETED(t1))
# t2_prerequisite: Not(DELETED(t2))

# SELECT name, emp_age, id FROM EMP WHERE emp_age > 25
# t3_prerequisite: And(
#                      Not(DELETED(t1)) ∧ EMP_AGE(t1) > 25 ⇒ Not(DELETED(t3)),
#                      Not(Not(DELETED(t1)) ∧ EMP_AGE(t1) > 25) ⇒ DELETED(t3),
#                  )
# t4_prerequisite: And(
#                      Not(DELETED(t2)) ∧ EMP_AGE(t2) > 25 ⇒ Not(DELETED(t4)),
#                      Not(Not(DELETED(t2)) ∧ EMP_AGE(t2) > 25) ⇒ DELETED(t4),
#                  )

# SELECT name FROM (...) WHERE emp_age < 30
# t5_prerequisite: And(
#                      Not(DELETED(t3)) ∧ EMP_AGE(t3) < 30 ⇒ Not(DELETED(t5)),
#                      Not(Not(DELETED(t3)) ∧ EMP_AGE(t3) < 30) ⇒ DELETED(t5),
#                  )
# t6_prerequisite: And(
#                      Not(DELETED(t4)) ∧ EMP_AGE(t4) < 30 ⇒ Not(DELETED(t6)),
#                      Not(Not(DELETED(t4)) ∧ EMP_AGE(t4) < 30) ⇒ DELETED(t6),
#                  )

# "SELECT id, name, emp_age FROM EMP WHERE emp_age < 30"
# t7_prerequisite: And(
#                      Not(DELETED(t1)) ∧ Not(EMP_AGE(t1) < 30) ⇒ Not(DELETED(t7)),
#                      Not(Not(DELETED(t1)) ∧ Not(EMP_AGE(t1) < 30) ⇒ DELETED(t7),
#                  )
# t8_prerequisite: And(
#                      Not(DELETED(t2)) ∧ Not(EMP_AGE(t2) < 30) ⇒ Not(DELETED(t8)),
#                      Not(Not(DELETED(t2)) ∧ Not(EMP_AGE(t2) < 30) ⇒ DELETED(t8),
#                  )

# "SELECT name FROM (...) WHERE emp_age > 25"
# t9_prerequisite: And(
#                      Not(DELETED(t7)) ∧ Not(EMP_AGE(t7) > 25) ⇒ Not(DELETED(t9)),
#                      Not(Not(DELETED(t7)) ∧ Not(EMP_AGE(t7) > 25) ⇒ DELETED(t9),
#                  )
# t10_prerequisite: And(
#                      Not(DELETED(t8)) ∧ Not(EMP_AGE(t8) > 25) ⇒ Not(DELETED(t10)),
#                      Not(Not(DELETED(t8)) ∧ Not(EMP_AGE(t8) > 25) ⇒ DELETED(t10),
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
t3, t4, t5, t6 = Consts('t3 t4 t5 t6', T)
# final tuples of sql2
t7, t8, t9, t10 = Consts('t7 t8 t9 t10', T)

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
    # SELECT name, emp_age, id FROM EMP WHERE emp_age > 25
    # t1 -> t3
    Implies(
        And(Not(DELETED(t1)), emp_age(t1) > 25),
        And(
            Not(DELETED(t3)),
            emp_name(t3) == emp_name(t1), NULL(t3, attr_emp_name) == NULL(t1, attr_emp_name),
            emp_age(t3) == emp_age(t1), NULL(t3, attr_emp_age) == NULL(t1, attr_emp_age),
            emp_id(t3) == emp_id(t1), NULL(t3, attr_emp_id) == NULL(t1, attr_emp_id),
        ),
    ),
    Implies(Not(And(Not(DELETED(t1)), emp_age(t1) > 25)), DELETED(t3)),
    # t2 -> t4
    Implies(
        And(Not(DELETED(t2)), emp_age(t2) > 25),
        And(
            Not(DELETED(t4)),
            emp_name(t4) == emp_name(t2), NULL(t4, attr_emp_name) == NULL(t2, attr_emp_name),
            emp_age(t4) == emp_age(t2), NULL(t4, attr_emp_age) == NULL(t2, attr_emp_age),
            emp_id(t4) == emp_id(t2), NULL(t4, attr_emp_id) == NULL(t2, attr_emp_id),
        ),
    ),
    Implies(Not(And(Not(DELETED(t2)), emp_age(t2) > 25)), DELETED(t4)),

    # SELECT name FROM (...) WHERE emp_age < 30
    # t3 -> t5
    Implies(
        And(Not(DELETED(t3)), emp_age(t3) < 30),
        And(
            Not(DELETED(t5)),
            emp_name(t5) == emp_name(t3), NULL(t5, attr_emp_name) == NULL(t3, attr_emp_name),
        ),
    ),
    Implies(Not(And(Not(DELETED(t3)), emp_age(t3) < 30)), DELETED(t5)),
    # t4 -> t6
    Implies(
        And(Not(DELETED(t4)), emp_age(t4) < 30),
        And(
            Not(DELETED(t6)),
            emp_name(t6) == emp_name(t4), NULL(t6, attr_emp_name) == NULL(t4, attr_emp_name),
        ),
    ),
    Implies(Not(And(Not(DELETED(t4)), emp_age(t4) < 30)), DELETED(t6)),
)

result2 = And(
    # SELECT id, name, emp_age FROM EMP WHERE emp_age < 30
    # t1 -> t7
    Implies(
        And(Not(DELETED(t1)), emp_age(t1) < 30),
        And(
            Not(DELETED(t7)),
            emp_name(t7) == emp_name(t1), NULL(t7, attr_emp_name) == NULL(t1, attr_emp_name),
            emp_age(t7) == emp_age(t1), NULL(t7, attr_emp_age) == NULL(t1, attr_emp_age),
            emp_id(t7) == emp_age(t1), NULL(t7, attr_emp_id) == NULL(t1, attr_emp_id),
        ),
    ),
    Implies(Not(And(Not(DELETED(t1)), emp_age(t1) < 30)), DELETED(t7)),
    # t2 -> t8
    Implies(
        And(Not(DELETED(t2)), emp_age(t2) < 30),
        And(
            Not(DELETED(t8)),
            emp_name(t8) == emp_name(t2), NULL(t8, attr_emp_name) == NULL(t2, attr_emp_name),
            emp_age(t8) == emp_age(t2), NULL(t8, attr_emp_age) == NULL(t2, attr_emp_age),
            emp_id(t8) == emp_age(t2), NULL(t8, attr_emp_id) == NULL(t2, attr_emp_id),
        ),
    ),
    Implies(Not(And(Not(DELETED(t2)), emp_age(t2) < 30)), DELETED(t8)),

    # SELECT name FROM (...) WHERE emp_age > 25
    # t7 -> t9
    Implies(
        And(Not(DELETED(t7)), emp_age(t7) > 25),
        And(
            Not(DELETED(t9)),
            emp_name(t9) == emp_name(t7), NULL(t9, attr_emp_name) == NULL(t7, attr_emp_name),
        ),
    ),
    Implies(Not(And(Not(DELETED(t7)), emp_age(t7) > 25)), DELETED(t9)),
    # t8 -> t10
    Implies(
        And(Not(DELETED(t8)), emp_age(t8) > 25),
        And(
            Not(DELETED(t10)),
            emp_name(t10) == emp_name(t8), NULL(t10, attr_emp_name) == NULL(t8, attr_emp_name),
        ),
    ),
    Implies(Not(And(Not(DELETED(t8)), emp_age(t8) > 25)), DELETED(t10)),
)

prerequisites = And(DBMS_facts, result1, result2)


def equals(ltuples, rtuples):
    def _tuple_equals(tuple1, tuple2):
        return And(
            And(Not(DELETED(tuple1)), Not(DELETED(tuple2))),
            Or(
                And(NULL(tuple1, attr_emp_name), NULL(tuple2, attr_emp_name)),
                emp_name(tuple1) == emp_name(tuple2),
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


conclusion = equals(ltuples=[t5, t6], rtuples=[t9, t10])

solver.add(Not(
    Implies(prerequisites, conclusion)
))

if solver.check() == sat:
    print(solver.model())

print(solver.check())
