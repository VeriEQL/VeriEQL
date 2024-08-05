# -*- coding: utf-8 -*-

# sql1 = "SELECT EMP.name, DEPT.name FROM (SELECT EMP.id, EMP.name, EMP.age, DEPT.name FROM EMP, DEPT WHERE EMP.dept_id = DEPT.id) WHERE EMP.age > 25"
# sql2 = "SELECT EMP.name, DEPT.name FROM EMP, DEPT WHERE EMP.dept_id = DEPT.id AND EMP.age > 25"

# EMP = [
#     t1 = [id=x1, name=x2, age=x3, dept_id=x4],
#     t2 = [id=x5, name=x6, age=x7, dept_id=x8],
# ]
# t1_prerequisite: Not(DELETED(t1))
# t2_prerequisite: Not(DELETED(t2))
# DEPT = [
#     t3 = [id=v1, name=v3],
#     t4 = [id=v3, name=v4],
# ]
# t3_prerequisite: Not(DELETED(t3))
# t4_prerequisite: Not(DELETED(t4))

# SELECT EMP.id, EMP.name, EMP.age, DEPT.name FROM EMP, DEPT WHERE EMP.dept_id = DEPT.id
# t5_prerequisite: And(
#                      Not(DELETED(t1)) ∧ Not(DELETED(t3)) ∧ EMP_DEPT_ID(t1) = DEPT_ID(t3) ⇒ Not(DELETED(t5)),
#                      Not(Not(DELETED(t1)) ∧ Not(DELETED(t3)) ∧ EMP_DEPT_ID(t1) = DEPT_ID(t3)) ⇒ DELETED(t5),
#                  )
# t6_prerequisite: And(
#                      Not(DELETED(t1)) ∧ Not(DELETED(t4)) ∧ EMP_DEPT_ID(t1) = DEPT_ID(t4) ⇒ Not(DELETED(t6)),
#                      Not(Not(DELETED(t1)) ∧ Not(DELETED(t4)) ∧ EMP_DEPT_ID(t1) = DEPT_ID(t4)) ⇒ DELETED(t6),
#                  )
# t7_prerequisite: And(
#                      Not(DELETED(t2)) ∧ Not(DELETED(t3)) ∧ EMP_DEPT_ID(t2) = DEPT_ID(t3) ⇒ Not(DELETED(t7)),
#                      Not(Not(DELETED(t2)) ∧ Not(DELETED(t3)) ∧ EMP_DEPT_ID(t2) = DEPT_ID(t3)) ⇒ DELETED(t7),
#                  )
# t8_prerequisite: And(
#                      Not(DELETED(t2)) ∧ Not(DELETED(t4)) ∧ EMP_DEPT_ID(t2) = DEPT_ID(t4) ⇒ Not(DELETED(t8)),
#                      Not(Not(DELETED(t2)) ∧ Not(DELETED(t4)) ∧ EMP_DEPT_ID(t2) = DEPT_ID(t4)) ⇒ DELETED(t8),
#                  )

# SELECT EMP.name, DEPT.name FROM (...) WHERE EMP.age > 25
# t9_prerequisite: And(
#                      Not(DELETED(t5)) ∧ EMP_AGE(t5) >25 ⇒ Not(DELETED(t9)),
#                      Not(Not(DELETED(t5)) ∧ EMP_AGE(t5) >25) ⇒ DELETED(t9),
#                  )
# t10_prerequisite: And(
#                      Not(DELETED(t6)) ∧ EMP_AGE(t6) >25 ⇒ Not(DELETED(t10)),
#                      Not(Not(DELETED(t6)) ∧ EMP_AGE(t6) >25) ⇒ DELETED(t10),
#                  )
# t11_prerequisite: And(
#                      Not(DELETED(t7)) ∧ EMP_AGE(t7) >25 ⇒ Not(DELETED(t11)),
#                      Not(Not(DELETED(t7)) ∧ EMP_AGE(t7) >25) ⇒ DELETED(t11),
#                  )
# t12_prerequisite: And(
#                      Not(DELETED(t8)) ∧ EMP_AGE(t8) >25 ⇒ Not(DELETED(t12)),
#                      Not(Not(DELETED(t8)) ∧ EMP_AGE(t8) >25) ⇒ DELETED(t12),
#                  )

# SELECT EMP.name, DEPT.name FROM EMP, DEPT WHERE EMP.dept_id = DEPT.id AND EMP.age > 25
# t13_prerequisite: And(
#                      Not(DELETED(t1)) ∧ Not(DELETED(t3)) ∧ EMP_DEPT_ID(t1) = DEPT_ID(t3) ∧ EMP_AGE(t1) >25 ⇒ Not(DELETED(t13)),
#                      Not(Not(DELETED(t1)) ∧ Not(DELETED(t3)) ∧ EMP_DEPT_ID(t1) = DEPT_ID(t3) ∧ EMP_AGE(t1) >25) ⇒ DELETED(t13),
#                  )
# t14_prerequisite: And(
#                      Not(DELETED(t1)) ∧ Not(DELETED(t4)) ∧ EMP_DEPT_ID(t1) = DEPT_ID(t4) ∧ EMP_AGE(t1) >25 ⇒ Not(DELETED(t14)),
#                      Not(Not(DELETED(t1)) ∧ Not(DELETED(t4)) ∧ EMP_DEPT_ID(t1) = DEPT_ID(t4) ∧ EMP_AGE(t1) >25) ⇒ DELETED(t14),
#                  )
# t15_prerequisite: And(
#                      Not(DELETED(t2)) ∧ Not(DELETED(t3)) ∧ EMP_DEPT_ID(t2) = DEPT_ID(t3) ∧ EMP_AGE(t2) >25 ⇒ Not(DELETED(t15)),
#                      Not(Not(DELETED(t2)) ∧ Not(DELETED(t3)) ∧ EMP_DEPT_ID(t2) = DEPT_ID(t3) ∧ EMP_AGE(t2) >25) ⇒ DELETED(t15),
#                  )
# t16_prerequisite: And(
#                      Not(DELETED(t2)) ∧ Not(DELETED(t4)) ∧ EMP_DEPT_ID(t2) = DEPT_ID(t4) ∧ EMP_AGE(t2) >25 ⇒ Not(DELETED(t16)),
#                      Not(Not(DELETED(t2)) ∧ Not(DELETED(t4)) ∧ EMP_DEPT_ID(t2) = DEPT_ID(t4) ∧ EMP_AGE(t2) >25) ⇒ DELETED(t16),
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
t1, t2, t3, t4 = Consts('t1 t2 t3 t4', T)
x1, x2, x3, x4 = Ints('x1 x2 x3 x4')
x5, x6, x7, x8 = Ints('x5 x6 x7 x8')
v1, v2, v3, v4 = Ints('v1 v2 v3 v4')
# final tuples of sql1
t5, t6, t7, t8, t9, t10, t11, t12 = Consts('t5 t6 t7 t8 t9 t10 t11 t12', T)
# final tuples of sql2
t13, t14, t15, t16 = Consts('t13 t14 t15 t16', T)

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

    Not(DELETED(t3)),
    Not(DELETED(t4)),

    dept_id(t3) == v1, dept_name(t3) == v2,
    Not(NULL(t3, attr_dept_id)), Not(NULL(t3, attr_dept_name)),

    dept_id(t4) == v3, dept_name(t4) == v4,
    Not(NULL(t4, attr_dept_id)), Not(NULL(t4, attr_dept_name)),
)

result1 = And(
    # SELECT EMP.id, EMP.name, EMP.age, DEPT.name FROM EMP, DEPT WHERE EMP.dept_id = DEPT.id
    # (t1, t2) X (t3, t4) -> (t5=(t1 X t3), t6=(t1 X t4), t7=(t2 X t3), t8=(t2 X t4))
    # t5=(t1 X t3)
    Implies(
        And(Not(DELETED(t1)), Not(DELETED(t3)), emp_dept_id(t1) == dept_id(t3)),
        And(
            Not(DELETED(t5)),
            emp_id(t5) == emp_id(t1), NULL(t5, attr_emp_id) == NULL(t1, attr_emp_id),
            emp_name(t5) == emp_name(t1), NULL(t5, attr_emp_name) == NULL(t1, attr_emp_name),
            emp_age(t5) == emp_age(t1), NULL(t5, attr_emp_age) == NULL(t1, attr_emp_age),
            dept_name(t5) == dept_name(t3), NULL(t5, attr_dept_name) == NULL(t3, attr_dept_name),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t1)), Not(DELETED(t3)), emp_dept_id(t1) == dept_id(t3))),
        DELETED(t5),
    ),
    # t6=(t1 X t4)
    Implies(
        And(Not(DELETED(t1)), Not(DELETED(t4)), emp_dept_id(t1) == dept_id(t4)),
        And(
            Not(DELETED(t6)),
            emp_id(t6) == emp_id(t1), NULL(t6, attr_emp_id) == NULL(t1, attr_emp_id),
            emp_name(t6) == emp_name(t1), NULL(t6, attr_emp_name) == NULL(t1, attr_emp_name),
            emp_age(t6) == emp_age(t1), NULL(t6, attr_emp_age) == NULL(t1, attr_emp_age),
            dept_name(t6) == dept_name(t4), NULL(t6, attr_dept_name) == NULL(t4, attr_dept_name),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t1)), Not(DELETED(t4)), emp_dept_id(t1) == dept_id(t4))),
        DELETED(t6),
    ),
    # t7=(t2 X t3)
    Implies(
        And(Not(DELETED(t2)), Not(DELETED(t3)), emp_dept_id(t2) == dept_id(t3)),
        And(
            Not(DELETED(t7)),
            emp_id(t7) == emp_id(t2), NULL(t7, attr_emp_id) == NULL(t2, attr_emp_id),
            emp_name(t7) == emp_name(t2), NULL(t7, attr_emp_name) == NULL(t2, attr_emp_name),
            emp_age(t7) == emp_age(t2), NULL(t7, attr_emp_age) == NULL(t2, attr_emp_age),
            dept_name(t7) == dept_name(t3), NULL(t7, attr_dept_name) == NULL(t3, attr_dept_name),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t2)), Not(DELETED(t3)), emp_dept_id(t2) == dept_id(t3))),
        DELETED(t7),
    ),
    # t8=(t2 X t4)
    Implies(
        And(Not(DELETED(t2)), Not(DELETED(t4)), emp_dept_id(t2) == dept_id(t4)),
        And(
            Not(DELETED(t8)),
            emp_id(t8) == emp_id(t2), NULL(t8, attr_emp_id) == NULL(t2, attr_emp_id),
            emp_name(t8) == emp_name(t2), NULL(t8, attr_emp_name) == NULL(t2, attr_emp_name),
            emp_age(t8) == emp_age(t2), NULL(t8, attr_emp_age) == NULL(t2, attr_emp_age),
            dept_name(t8) == dept_name(t4), NULL(t8, attr_dept_name) == NULL(t4, attr_dept_name),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t2)), Not(DELETED(t4)), emp_dept_id(t2) == dept_id(t4))),
        DELETED(t8),
    ),

    # SELECT EMP.name, DEPT.name FROM (...) WHERE EMP.age > 25
    # t5 -> t9
    Implies(
        And(Not(DELETED(t5)), emp_age(t5) > 25),
        And(
            Not(DELETED(t9)),
            emp_name(t9) == emp_name(t5), NULL(t9, attr_emp_name) == NULL(t5, attr_emp_name),
            dept_name(t9) == dept_name(t5), NULL(t9, attr_dept_name) == NULL(t5, attr_dept_name),
        )
    ),
    Implies(
        Not(And(Not(DELETED(t5)), emp_age(t5) > 25)),
        DELETED(t9),
    ),
    # t6 -> t10
    Implies(
        And(Not(DELETED(t6)), emp_age(t6) > 25),
        And(
            Not(DELETED(t10)),
            emp_name(t10) == emp_name(t6), NULL(t10, attr_emp_name) == NULL(t6, attr_emp_name),
            dept_name(t10) == dept_name(t6), NULL(t10, attr_dept_name) == NULL(t6, attr_dept_name),
        )
    ),
    Implies(
        Not(And(Not(DELETED(t6)), emp_age(t6) > 25)),
        DELETED(t10),
    ),
    # t7 -> t11
    Implies(
        And(Not(DELETED(t7)), emp_age(t7) > 25),
        And(
            Not(DELETED(t11)),
            emp_name(t11) == emp_name(t7), NULL(t11, attr_emp_name) == NULL(t7, attr_emp_name),
            dept_name(t11) == dept_name(t7), NULL(t11, attr_dept_name) == NULL(t7, attr_dept_name),
        )
    ),
    Implies(
        Not(And(Not(DELETED(t7)), emp_age(t7) > 25)),
        DELETED(t11),
    ),
    # t8 -> t12
    Implies(
        And(Not(DELETED(t8)), emp_age(t8) > 25),
        And(
            Not(DELETED(t12)),
            emp_name(t12) == emp_name(t8), NULL(t12, attr_emp_name) == NULL(t8, attr_emp_name),
            dept_name(t12) == dept_name(t8), NULL(t12, attr_dept_name) == NULL(t8, attr_dept_name),
        )
    ),
    Implies(
        Not(And(Not(DELETED(t8)), emp_age(t8) > 25)),
        DELETED(t12),
    ),
)

result2 = And(
    # SELECT EMP.name, DEPT.name FROM EMP, DEPT WHERE EMP.dept_id = DEPT.id AND EMP.age > 25
    # (t1, t2) X (t3, t4) -> (t13=(t1 X t3), t14=(t1 X t4), t15=(t2 X t3), t16=(t2 X t4))
    # t13=(t1 X t3)
    Implies(
        And(Not(DELETED(t1)), Not(DELETED(t3)), emp_dept_id(t1) == dept_id(t3), emp_age(t1) > 25),
        And(
            Not(DELETED(t13)),
            emp_name(t13) == emp_name(t1), NULL(t13, attr_emp_name) == NULL(t1, attr_emp_name),
            dept_name(t13) == dept_name(t3), NULL(t13, attr_dept_name) == NULL(t3, attr_dept_name),
        )
    ),
    Implies(
        Not(And(Not(DELETED(t1)), Not(DELETED(t3)), emp_dept_id(t1) == dept_id(t3), emp_age(t1) > 25)),
        DELETED(t13),
    ),
    # t14=(t1 X t4)
    Implies(
        And(Not(DELETED(t1)), Not(DELETED(t4)), emp_dept_id(t1) == dept_id(t4), emp_age(t1) > 25),
        And(
            Not(DELETED(t14)),
            emp_name(t14) == emp_name(t1), NULL(t14, attr_emp_name) == NULL(t1, attr_emp_name),
            dept_name(t14) == dept_name(t4), NULL(t14, attr_dept_name) == NULL(t4, attr_dept_name),
        )
    ),
    Implies(
        Not(And(Not(DELETED(t1)), Not(DELETED(t4)), emp_dept_id(t1) == dept_id(t4), emp_age(t1) > 25)),
        DELETED(t14),
    ),
    # t15=(t2 X t3)
    Implies(
        And(Not(DELETED(t2)), Not(DELETED(t3)), emp_dept_id(t2) == dept_id(t3), emp_age(t2) > 25),
        And(
            Not(DELETED(t15)),
            emp_name(t15) == emp_name(t2), NULL(t15, attr_emp_name) == NULL(t2, attr_emp_name),
            dept_name(t15) == dept_name(t3), NULL(t15, attr_dept_name) == NULL(t3, attr_dept_name),
        )
    ),
    Implies(
        Not(And(Not(DELETED(t2)), Not(DELETED(t3)), emp_dept_id(t2) == dept_id(t3), emp_age(t2) > 25)),
        DELETED(t15),
    ),
    # t16=(t2 X t4)
    Implies(
        And(Not(DELETED(t2)), Not(DELETED(t4)), emp_dept_id(t2) == dept_id(t4), emp_age(t2) > 25),
        And(
            Not(DELETED(t16)),
            emp_name(t16) == emp_name(t2), NULL(t16, attr_emp_name) == NULL(t2, attr_emp_name),
            dept_name(t16) == dept_name(t4), NULL(t16, attr_dept_name) == NULL(t4, attr_dept_name),
        )
    ),
    Implies(
        Not(And(Not(DELETED(t2)), Not(DELETED(t4)), emp_dept_id(t2) == dept_id(t4), emp_age(t2) > 25)),
        DELETED(t16),
    ),
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


conclusion = equals(ltuples=[t9, t10, t11, t12], rtuples=[t13, t14, t15, t16])

solver.add(Not(
    Implies(prerequisites, conclusion)
))

if solver.check() == sat:
    print(solver.model())

print(solver.check())
