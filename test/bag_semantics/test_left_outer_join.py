# -*- coding: utf-8 -*-

# sql1 = "SELECT EMP.ID FROM EMP LEFT OUTER JOIN DEPT ON EMP.dept_id = DEPT.id WHERE EMP.age > 25"
# sql2 = "SELECT EMP.ID FROM DEPT RIGHT OUTER JOIN EMP ON EMP.dept_id = DEPT.id WHERE EMP.age > 25"

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

# EMP LEFT OUTER JOIN DEPT ON EMP.dept_id = DEPT.id
# DELETED_prerequisite = []
# t5_prerequisite: And(
#                      Not(DELETED(t1)) ∧ Not(DELETED(t3)) ∧ EMP_DEPT_ID(t1) = DEPT_ID(t3) ⇒ Not(DELETED(t5)),
#                      Not(Not(DELETED(t1)) ∧ Not(DELETED(t3)) ∧ EMP_DEPT_ID(t1) = DEPT_ID(t3)) ⇒ DELETED(t5),
#                  )
# DELETED_prerequisite = DELETED_tuples ∧ DELETED(t5)
# t6_prerequisite: And(
#                      Not(DELETED(t1)) ∧ Not(DELETED(t4)) ∧ EMP_DEPT_ID(t1) = DEPT_ID(t4) ⇒ Not(DELETED(t6)),
#                      Not(Not(DELETED(t1)) ∧ Not(DELETED(t4)) ∧ EMP_DEPT_ID(t1) = DEPT_ID(t4)) ⇒ DELETED(t6),
#                  )
# DELETED_prerequisite = DELETED_tuples ∧ DELETED(t6)
# t7 = (t1, NULL)
# t7_fact: And(
#              EMP_ID(t7) = EMP_ID(t1) ∧ NULL(t7, EMP_ID) = NULL(t1, EMP_ID), ...
#              NULL(t7, DEPT_ID), ...
#          )
# t7_prerequisite: And(
#                      DELETED_prerequisite ⇒ Not(DELETED(t7)),
#                      Not(DELETED_prerequisite) ⇒ DELETED(t7),
#                      t7_fact,
#                  )

# DEPT RIGHT OUTER JOIN EMP ON EMP.dept_id = DEPT.id


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
t5, t6, t7, t8, t9, t10, t11, t12, t13, t14, t15, t16 = Consts('t5 t6 t7 t8 t9 t10 t11 t12 t13 t14 t15 t16', T)
# final tuples of sql2
t17, t18, t19, t20, t21, t22, t23, t24, t25, t26, t27, t28 = Consts('t17 t18 t19 t20 t21 t22 t23 t24 t25 t26 t27 t28',
                                                                    T)

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
    # EMP LEFT OUTER JOIN DEPT ON EMP.dept_id = DEPT.id
    # (t1, t2) X (t3, t4) -> (t5=(t1 X t3), t6=(t1 X t4), t7=(t1 X NULL), t8=(t2 X t3), t9=(t2 X t4), t10=(t2 X NULL))
    # t5 = (t1, t3)
    Implies(
        And(Not(DELETED(t1)), Not(DELETED(t3)), emp_dept_id(t1) == dept_id(t3)),
        And(
            Not(DELETED(t5)),

            emp_id(t5) == emp_id(t1), NULL(t5, attr_emp_id) == NULL(t1, attr_emp_id),
            emp_name(t5) == emp_name(t1), NULL(t5, attr_emp_name) == NULL(t1, attr_emp_name),
            emp_age(t5) == emp_age(t1), NULL(t5, attr_emp_age) == NULL(t1, attr_emp_age),
            emp_dept_id(t5) == emp_dept_id(t1), NULL(t5, attr_emp_dept_id) == NULL(t1, attr_emp_dept_id),

            dept_id(t5) == dept_id(t3), NULL(t5, attr_dept_id) == NULL(t3, attr_dept_id),
            dept_name(t5) == dept_name(t3), NULL(t5, attr_dept_name) == NULL(t3, attr_dept_name),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t1)), Not(DELETED(t3)), emp_dept_id(t1) == dept_id(t3))),
        DELETED(t5),
    ),
    # t6 = (t1, t4)
    Implies(
        And(Not(DELETED(t1)), Not(DELETED(t4)), emp_dept_id(t1) == dept_id(t4)),
        And(
            Not(DELETED(t6)),

            emp_id(t6) == emp_id(t1), NULL(t6, attr_emp_id) == NULL(t1, attr_emp_id),
            emp_name(t6) == emp_name(t1), NULL(t6, attr_emp_name) == NULL(t1, attr_emp_name),
            emp_age(t6) == emp_age(t1), NULL(t6, attr_emp_age) == NULL(t1, attr_emp_age),
            emp_dept_id(t6) == emp_dept_id(t1), NULL(t6, attr_emp_dept_id) == NULL(t1, attr_emp_dept_id),

            dept_id(t6) == dept_id(t4), NULL(t6, attr_dept_id) == NULL(t4, attr_dept_id),
            dept_name(t6) == dept_name(t4), NULL(t6, attr_dept_name) == NULL(t4, attr_dept_name),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t1)), Not(DELETED(t4)), emp_dept_id(t1) == dept_id(t4))),
        DELETED(t6),
    ),
    # t7 = (t1, NULL)
    Implies(
        And(DELETED(t5), DELETED(t6)),
        And(
            Not(DELETED(t7)),

            emp_id(t7) == emp_id(t1), NULL(t7, attr_emp_id) == NULL(t1, attr_emp_id),
            emp_name(t7) == emp_name(t1), NULL(t7, attr_emp_name) == NULL(t1, attr_emp_name),
            emp_age(t7) == emp_age(t1), NULL(t7, attr_emp_age) == NULL(t1, attr_emp_age),
            emp_dept_id(t7) == emp_dept_id(t1), NULL(t7, attr_emp_dept_id) == NULL(t1, attr_emp_dept_id),

            NULL(t7, attr_dept_id),
            NULL(t7, attr_dept_name),
        ),
    ),
    Implies(
        Not(And(DELETED(t5), DELETED(t6))),
        DELETED(t7),
    ),
    # t8 = (t2, t3)
    Implies(
        And(Not(DELETED(t2)), Not(DELETED(t3)), emp_dept_id(t2) == dept_id(t3)),
        And(
            Not(DELETED(t8)),

            emp_id(t8) == emp_id(t2), NULL(t8, attr_emp_id) == NULL(t2, attr_emp_id),
            emp_name(t8) == emp_name(t2), NULL(t8, attr_emp_name) == NULL(t2, attr_emp_name),
            emp_age(t8) == emp_age(t2), NULL(t8, attr_emp_age) == NULL(t2, attr_emp_age),
            emp_dept_id(t8) == emp_dept_id(t2), NULL(t8, attr_emp_dept_id) == NULL(t2, attr_emp_dept_id),

            dept_id(t8) == dept_id(t3), NULL(t8, attr_dept_id) == NULL(t3, attr_dept_id),
            dept_name(t8) == dept_name(t3), NULL(t8, attr_dept_name) == NULL(t3, attr_dept_name),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t2)), Not(DELETED(t3)), emp_dept_id(t2) == dept_id(t3))),
        DELETED(t8),
    ),
    # t9 = (t2, t4)
    Implies(
        And(Not(DELETED(t2)), Not(DELETED(t4)), emp_dept_id(t2) == dept_id(t4)),
        And(
            Not(DELETED(t9)),

            emp_id(t9) == emp_id(t2), NULL(t9, attr_emp_id) == NULL(t2, attr_emp_id),
            emp_name(t9) == emp_name(t2), NULL(t9, attr_emp_name) == NULL(t2, attr_emp_name),
            emp_age(t9) == emp_age(t2), NULL(t9, attr_emp_age) == NULL(t2, attr_emp_age),
            emp_dept_id(t9) == emp_dept_id(t2), NULL(t9, attr_emp_dept_id) == NULL(t2, attr_emp_dept_id),

            dept_id(t9) == dept_id(t4), NULL(t9, attr_dept_id) == NULL(t4, attr_dept_id),
            dept_name(t9) == dept_name(t4), NULL(t9, attr_dept_name) == NULL(t4, attr_dept_name),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t2)), Not(DELETED(t4)), emp_dept_id(t2) == dept_id(t4))),
        DELETED(t9),
    ),
    # t10 = (t2, NULL)
    Implies(
        And(DELETED(t8), DELETED(t9)),
        And(
            Not(DELETED(t10)),

            emp_id(t10) == emp_id(t2), NULL(t10, attr_emp_id) == NULL(t2, attr_emp_id),
            emp_name(t10) == emp_name(t2), NULL(t10, attr_emp_name) == NULL(t2, attr_emp_name),
            emp_age(t10) == emp_age(t2), NULL(t10, attr_emp_age) == NULL(t2, attr_emp_age),
            emp_dept_id(t10) == emp_dept_id(t2), NULL(t10, attr_emp_dept_id) == NULL(t2, attr_emp_dept_id),

            NULL(t10, attr_dept_id),
            NULL(t10, attr_dept_name),
        ),
    ),
    Implies(
        Not(And(DELETED(t8), DELETED(t9))),
        DELETED(t10),
    ),

    # SELECT EMP.ID FROM (...) WHERE EMP.age > 25
    # t5 -> t11
    Implies(
        And(Not(DELETED(t5)), emp_age(t5) > 25),
        And(
            Not(DELETED(t11)),
            emp_id(t11) == emp_id(t5), NULL(t11, attr_emp_id) == NULL(t5, attr_emp_id),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t5)), emp_age(t5) > 25)),
        DELETED(t11),
    ),
    # t6 -> t12
    Implies(
        And(Not(DELETED(t6)), emp_age(t6) > 25),
        And(
            Not(DELETED(t12)),
            emp_id(t12) == emp_id(t6), NULL(t12, attr_emp_id) == NULL(t6, attr_emp_id),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t6)), emp_age(t6) > 25)),
        DELETED(t12),
    ),
    # t7 -> t13
    Implies(
        And(Not(DELETED(t7)), emp_age(t7) > 25),
        And(
            Not(DELETED(t13)),
            emp_id(t13) == emp_id(t7), NULL(t13, attr_emp_id) == NULL(t7, attr_emp_id),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t7)), emp_age(t7) > 25)),
        DELETED(t13),
    ),
    # t8 -> t14
    Implies(
        And(Not(DELETED(t8)), emp_age(t8) > 25),
        And(
            Not(DELETED(t14)),
            emp_id(t14) == emp_id(t8), NULL(t14, attr_emp_id) == NULL(t8, attr_emp_id),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t8)), emp_age(t8) > 25)),
        DELETED(t14),
    ),
    # t9 -> t15
    Implies(
        And(Not(DELETED(t9)), emp_age(t9) > 25),
        And(
            Not(DELETED(t15)),
            emp_id(t15) == emp_id(t9), NULL(t15, attr_emp_id) == NULL(t9, attr_emp_id),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t9)), emp_age(t9) > 25)),
        DELETED(t15),
    ),
    # t10 -> t16
    Implies(
        And(Not(DELETED(t10)), emp_age(t10) > 25),
        And(
            Not(DELETED(t16)),
            emp_id(t16) == emp_id(t10), NULL(t16, attr_emp_id) == NULL(t10, attr_emp_id),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t10)), emp_age(t10) > 25)),
        DELETED(t16),
    ),
)

result2 = And(
    # DEPT RIGHT OUTER JOIN EMP ON EMP.dept_id = DEPT.id
    # (t1, t2) X (t3, t4) -> (t17=(t3 X t1), t18=(t4 X t1), t19=(NULL X t1), t20=(t3 X t2), t21=(t4 X t2), t22=(NULL X t2))
    # t17 = (t3, t1)
    Implies(
        And(Not(DELETED(t3)), Not(DELETED(t1)), emp_dept_id(t1) == dept_id(t3)),
        And(
            Not(DELETED(t17)),

            dept_id(t17) == dept_id(t3), NULL(t17, attr_dept_id) == NULL(t3, attr_dept_id),
            dept_name(t17) == dept_name(t3), NULL(t17, attr_dept_name) == NULL(t3, attr_dept_name),

            emp_id(t17) == emp_id(t1), NULL(t17, attr_emp_id) == NULL(t1, attr_emp_id),
            emp_name(t17) == emp_name(t1), NULL(t17, attr_emp_name) == NULL(t1, attr_emp_name),
            emp_age(t17) == emp_age(t1), NULL(t17, attr_emp_age) == NULL(t1, attr_emp_age),
            emp_dept_id(t17) == emp_dept_id(t1), NULL(t17, attr_emp_dept_id) == NULL(t1, attr_emp_dept_id),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t3)), Not(DELETED(t1)), emp_dept_id(t1) == dept_id(t3))),
        DELETED(t17),
    ),
    # t18 = (t4, t1)
    Implies(
        And(Not(DELETED(t4)), Not(DELETED(t1)), emp_dept_id(t1) == dept_id(t4)),
        And(
            Not(DELETED(t18)),

            dept_id(t18) == dept_id(t4), NULL(t18, attr_dept_id) == NULL(t4, attr_dept_id),
            dept_name(t18) == dept_name(t4), NULL(t18, attr_dept_name) == NULL(t4, attr_dept_name),

            emp_id(t18) == emp_id(t1), NULL(t18, attr_emp_id) == NULL(t1, attr_emp_id),
            emp_name(t18) == emp_name(t1), NULL(t18, attr_emp_name) == NULL(t1, attr_emp_name),
            emp_age(t18) == emp_age(t1), NULL(t18, attr_emp_age) == NULL(t1, attr_emp_age),
            emp_dept_id(t18) == emp_dept_id(t1), NULL(t18, attr_emp_dept_id) == NULL(t1, attr_emp_dept_id),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t4)), Not(DELETED(t1)), emp_dept_id(t1) == dept_id(t4))),
        DELETED(t18),
    ),
    # t19 = (NULL, t1)
    Implies(
        And(DELETED(t17), DELETED(t18)),
        And(
            Not(DELETED(t19)),

            emp_id(t19) == emp_id(t1), NULL(t19, attr_emp_id) == NULL(t1, attr_emp_id),
            emp_name(t19) == emp_name(t1), NULL(t19, attr_emp_name) == NULL(t1, attr_emp_name),
            emp_age(t19) == emp_age(t1), NULL(t19, attr_emp_age) == NULL(t1, attr_emp_age),
            emp_dept_id(t19) == emp_dept_id(t1), NULL(t19, attr_emp_dept_id) == NULL(t1, attr_emp_dept_id),

            NULL(t19, attr_dept_id),
            NULL(t19, attr_dept_name),
        ),
    ),
    Implies(
        Not(And(DELETED(t17), DELETED(t18))),
        DELETED(t19),
    ),
    # t20 = (t3, t2)
    Implies(
        And(Not(DELETED(t3)), Not(DELETED(t2)), emp_dept_id(t2) == dept_id(t3)),
        And(
            Not(DELETED(t20)),

            dept_id(t20) == dept_id(t3), NULL(t20, attr_dept_id) == NULL(t3, attr_dept_id),
            dept_name(t20) == dept_name(t3), NULL(t20, attr_dept_name) == NULL(t3, attr_dept_name),

            emp_id(t20) == emp_id(t2), NULL(t20, attr_emp_id) == NULL(t2, attr_emp_id),
            emp_name(t20) == emp_name(t2), NULL(t20, attr_emp_name) == NULL(t2, attr_emp_name),
            emp_age(t20) == emp_age(t2), NULL(t20, attr_emp_age) == NULL(t2, attr_emp_age),
            emp_dept_id(t20) == emp_dept_id(t2), NULL(t20, attr_emp_dept_id) == NULL(t2, attr_emp_dept_id),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t3)), Not(DELETED(t2)), emp_dept_id(t2) == dept_id(t3))),
        DELETED(t20),
    ),
    # t21 = (t4, t2)
    Implies(
        And(Not(DELETED(t4)), Not(DELETED(t2)), emp_dept_id(t2) == dept_id(t4)),
        And(
            Not(DELETED(t21)),

            dept_id(t21) == dept_id(t4), NULL(t21, attr_dept_id) == NULL(t4, attr_dept_id),
            dept_name(t21) == dept_name(t4), NULL(t21, attr_dept_name) == NULL(t4, attr_dept_name),

            emp_id(t21) == emp_id(t2), NULL(t21, attr_emp_id) == NULL(t2, attr_emp_id),
            emp_name(t21) == emp_name(t2), NULL(t21, attr_emp_name) == NULL(t2, attr_emp_name),
            emp_age(t21) == emp_age(t2), NULL(t21, attr_emp_age) == NULL(t2, attr_emp_age),
            emp_dept_id(t21) == emp_dept_id(t2), NULL(t21, attr_emp_dept_id) == NULL(t2, attr_emp_dept_id),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t4)), Not(DELETED(t2)), emp_dept_id(t2) == dept_id(t4))),
        DELETED(t21),
    ),
    # t22 = (NULL, t2)
    Implies(
        And(DELETED(t20), DELETED(t21)),
        And(
            Not(DELETED(t22)),

            emp_id(t22) == emp_id(t2), NULL(t22, attr_emp_id) == NULL(t2, attr_emp_id),
            emp_name(t22) == emp_name(t2), NULL(t22, attr_emp_name) == NULL(t2, attr_emp_name),
            emp_age(t22) == emp_age(t2), NULL(t22, attr_emp_age) == NULL(t2, attr_emp_age),
            emp_dept_id(t22) == emp_dept_id(t2), NULL(t22, attr_emp_dept_id) == NULL(t2, attr_emp_dept_id),

            NULL(t22, attr_dept_id),
            NULL(t22, attr_dept_name),
        ),
    ),
    Implies(
        Not(And(DELETED(t20), DELETED(t21))),
        DELETED(t22),
    ),

    # SELECT EMP.ID FROM (...) WHERE EMP.age > 25
    # t17 -> t23
    Implies(
        And(Not(DELETED(t17)), emp_age(t17) > 25),
        And(
            Not(DELETED(t23)),
            emp_id(t23) == emp_id(t17), NULL(t23, attr_emp_id) == NULL(t17, attr_emp_id),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t17)), emp_age(t17) > 25)),
        DELETED(t23),
    ),
    # t18 -> t24
    Implies(
        And(Not(DELETED(t18)), emp_age(t18) > 25),
        And(
            Not(DELETED(t24)),
            emp_id(t24) == emp_id(t18), NULL(t24, attr_emp_id) == NULL(t18, attr_emp_id),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t18)), emp_age(t18) > 25)),
        DELETED(t24),
    ),
    # t19 -> t25
    Implies(
        And(Not(DELETED(t19)), emp_age(t19) > 25),
        And(
            Not(DELETED(t25)),
            emp_id(t25) == emp_id(t19), NULL(t25, attr_emp_id) == NULL(t19, attr_emp_id),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t19)), emp_age(t19) > 25)),
        DELETED(t25),
    ),
    # t20 -> t26
    Implies(
        And(Not(DELETED(t20)), emp_age(t20) > 25),
        And(
            Not(DELETED(t26)),
            emp_id(t26) == emp_id(t20), NULL(t26, attr_emp_id) == NULL(t20, attr_emp_id),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t20)), emp_age(t20) > 25)),
        DELETED(t26),
    ),
    # t21 -> t27
    Implies(
        And(Not(DELETED(t21)), emp_age(t21) > 25),
        And(
            Not(DELETED(t27)),
            emp_id(t27) == emp_id(t21), NULL(t27, attr_emp_id) == NULL(t21, attr_emp_id),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t21)), emp_age(t21) > 25)),
        DELETED(t27),
    ),
    # t22 -> t28
    Implies(
        And(Not(DELETED(t22)), emp_age(t22) > 25),
        And(
            Not(DELETED(t28)),
            emp_id(t28) == emp_id(t22), NULL(t28, attr_emp_id) == NULL(t22, attr_emp_id),
        ),
    ),
    Implies(
        Not(And(Not(DELETED(t22)), emp_age(t22) > 25)),
        DELETED(t28),
    ),
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


conclusion = equals(ltuples=[t11, t12, t13, t14, t15, t16], rtuples=[t23, t24, t25, t26, t27, t28])

solver.add(Not(
    Implies(prerequisites, conclusion)
))

if solver.check() == sat:
    print(solver.model())

print(solver.check())
