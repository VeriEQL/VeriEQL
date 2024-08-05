# -*- coding: utf-8 -*-

# sql1 = "SELECT * FROM EMP WHERE age IN (SELECT AGE FROM EMP WHERE age > 25)"
# sql2 = "SELECT * FROM EMP WHERE NOT age <= 25"


import itertools

from z3 import *

T = DeclareSort('T')
DELETED = Function('DELETED', T, BoolSort())
NULL = Function('NULL', T, StringSort(), BoolSort())

emp_id = Function('EMP.id', T, IntSort())
emp_name = Function('EMP.name', T, IntSort())
emp_age = Function('EMP.emp_age', T, IntSort())
emp_dept_id = Function('EMP.dept_id', T, IntSort())

attr_emp_id = Const('EMP.id_str', StringSort())
attr_emp_name = Const('EMP.name_str', StringSort())
attr_emp_age = Const('EMP.age_str', StringSort())
attr_emp_dept_id = Const('EMP.dept_id_str', StringSort())

# base tuples and their values from the DBMS
x1, x2, x3, x4 = Ints('x1 x2 x3 x4')
x5, x6, x7, x8 = Ints('x5 x6 x7 x8')
t1, t2, t3 = Consts('t1 t2 t3', T)
t4, t5, t6, t7, t8, t9, t10, t11, t12 = Consts('t4 t5 t6 t7 t8 t9 t10 t11 t12', T)
t13, t14, t15, t16, t17, t18, t19, t20 = Consts('t13 t14 t15 t16 t17 t18 t19 t20', T)
t21, t22, t23, t24, t25, t26, t27 = Consts('t21 t22 t23 t24 t25 t26 t27', T)
t28, t29, t30, t31, t32, t33, t34, t35 = Consts('t28 t29 t30 t31 t32 t33 t34 t35', T)
t36, t37, t38, t39, t40, t41, t42, t43 = Consts('t36 t37 t38 t39 t40 t41 t42 t43', T)
t44, t45, t46, t47, t48, t49, t50, t51 = Consts('t44 t45 t46 t47 t48 t49 t50 t51', T)
t52, t53, t54, t55, t56, t57, t58, t59 = Consts('t52 t53 t54 t55 t56 t57 t58 t59', T)
t60, t61, t62, t63, t64, t65, t66, t67 = Consts('t60 t61 t62 t63 t64 t65 t66 t67', T)
t68, t69, t70, t71, t72, t73, t74, t75 = Consts('t68 t69 t70 t71 t72 t73 t74 t75', T)

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
    # SELECT AGE FROM EMP WHERE age > 25
    # t1 -> t3
    And(
        Implies(
            And(Not(DELETED(t1)), emp_age(t1) > 25),
            And(
                Not(DELETED(t3)),
                And(
                    emp_age(t3) == emp_age(t1),
                    NULL(t3, attr_emp_age) == NULL(t1, attr_emp_age),
                ),
            ),
        ),
        Implies(
            Not(And(Not(DELETED(t1)), emp_age(t1) > 25)),
            DELETED(t3),
        ),
    ),
    # t2 -> t4
    And(
        Implies(
            And(Not(DELETED(t2)), emp_age(t2) > 25),
            And(
                Not(DELETED(t4)),
                And(
                    emp_age(t4) == emp_age(t2),
                    NULL(t4, attr_emp_age) == NULL(t2, attr_emp_age),
                ),
            ),
        ),
        Implies(
            Not(And(Not(DELETED(t2)), emp_age(t2) > 25)),
            DELETED(t4),
        ),
    ),

    # SELECT * FROM EMP WHERE age IN (...)
    # t1 IN (t3, t4) -> t5
    And(
        Implies(
            And(
                Not(DELETED(t1)),
                Or(
                    And(
                        Not(DELETED(t3)),
                        Or(
                            And(NULL(t1, attr_emp_age), NULL(t3, attr_emp_age)),
                            And(
                                Not(NULL(t1, attr_emp_age)), Not(NULL(t3, attr_emp_age)),
                                emp_age(t1) == emp_age(t3),
                            )
                        ),
                    ),
                    And(
                        Not(DELETED(t4)),
                        Or(
                            And(NULL(t1, attr_emp_age), NULL(t4, attr_emp_age)),
                            And(
                                Not(NULL(t1, attr_emp_age)), Not(NULL(t4, attr_emp_age)),
                                emp_age(t1) == emp_age(t4),
                            )
                        ),
                    ),
                ),
            ),
            And(
                Not(DELETED(t5)),
                t5 == t1,
            ),
        ),
        Implies(
            Not(And(
                Not(DELETED(t1)),
                Or(
                    And(
                        Not(DELETED(t3)),
                        Or(
                            And(NULL(t1, attr_emp_age), NULL(t3, attr_emp_age)),
                            And(
                                Not(NULL(t1, attr_emp_age)), Not(NULL(t3, attr_emp_age)),
                                emp_age(t1) == emp_age(t3),
                            )
                        ),
                    ),
                    And(
                        Not(DELETED(t4)),
                        Or(
                            And(NULL(t1, attr_emp_age), NULL(t4, attr_emp_age)),
                            And(
                                Not(NULL(t1, attr_emp_age)), Not(NULL(t4, attr_emp_age)),
                                emp_age(t1) == emp_age(t4),
                            )
                        ),
                    ),
                ),
            )),
            DELETED(t5),
        ),
    ),
    # t2 IN (t3, t4) -> t6
    And(
        Implies(
            And(
                Not(DELETED(t2)),
                Or(
                    And(
                        Not(DELETED(t3)),
                        Or(
                            And(NULL(t2, attr_emp_age), NULL(t3, attr_emp_age)),
                            And(
                                Not(NULL(t2, attr_emp_age)), Not(NULL(t3, attr_emp_age)),
                                emp_age(t2) == emp_age(t3),
                            )
                        ),
                    ),
                    And(
                        Not(DELETED(t4)),
                        Or(
                            And(NULL(t2, attr_emp_age), NULL(t4, attr_emp_age)),
                            And(
                                Not(NULL(t2, attr_emp_age)), Not(NULL(t4, attr_emp_age)),
                                emp_age(t2) == emp_age(t4),
                            )
                        ),
                    ),
                ),
            ),
            And(
                Not(DELETED(t6)),
                t6 == t2,
            ),
        ),
        Implies(
            Not(And(
                Not(DELETED(t2)),
                Or(
                    And(
                        Not(DELETED(t3)),
                        Or(
                            And(NULL(t2, attr_emp_age), NULL(t3, attr_emp_age)),
                            And(
                                NULL(t2, attr_emp_age), NULL(t3, attr_emp_age),
                                emp_age(t2) == emp_age(t3),
                            )
                        ),
                    ),
                    And(
                        Not(DELETED(t4)),
                        Or(
                            And(NULL(t2, attr_emp_age), NULL(t4, attr_emp_age)),
                            And(
                                NULL(t2, attr_emp_age), NULL(t4, attr_emp_age),
                                emp_age(t2) == emp_age(t4),
                            )
                        ),
                    ),
                ),
            )),
            DELETED(t6),
        ),
    ),
)

result2 = And(
    # SELECT * FROM EMP WHERE NOT age <= 25
    # t1 -> t7
    And(
        Implies(
            And(Not(DELETED(t1)), Not(emp_age(t1) <= 25)),
            And(
                Not(DELETED(t7)),
                t7 == t1,
            ),
        ),
        Implies(
            Not(And(Not(DELETED(t1)), Not(emp_age(t1) <= 25))),
            DELETED(t7),
        ),
    ),
    # t2 -> t8
    And(
        Implies(
            And(Not(DELETED(t2)), Not(emp_age(t2) <= 25)),
            And(
                Not(DELETED(t8)),
                t8 == t2,
            ),
        ),
        Implies(
            Not(And(Not(DELETED(t2)), Not(emp_age(t2) <= 25))),
            DELETED(t8),
        ),
    ),
)

prerequisites = And(DBMS_facts, result1, result2)


def equals(ltuples, rtuples):
    def _tuple_equals(tuple1, tuple2):
        return If(
            And(DELETED(tuple1), DELETED(tuple2)),
            True,
            And(
                And(Not(DELETED(tuple1)), Not(DELETED(tuple2))),
                And(
                    Or(
                        And(NULL(tuple1, attr_emp_id), NULL(tuple2, attr_emp_id)),
                        emp_id(tuple1) == emp_id(tuple2),
                    ),
                    Or(
                        And(NULL(tuple1, attr_emp_age), NULL(tuple2, attr_emp_age)),
                        emp_age(tuple1) == emp_age(tuple2),
                    ),
                    Or(
                        And(NULL(tuple1, attr_emp_name), NULL(tuple2, attr_emp_name)),
                        emp_name(tuple1) == emp_name(tuple2),
                    ),
                    Or(
                        And(NULL(tuple1, attr_emp_dept_id), NULL(tuple2, attr_emp_dept_id)),
                        emp_dept_id(tuple1) == emp_dept_id(tuple2),
                    ),
                )
            )
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


conclusion = equals(ltuples=[t5, t6], rtuples=[t7, t8])

solver.add(Not(
    Implies(prerequisites, conclusion)
))

if solver.check() == sat:
    model = solver.model()
    print(model)

print(solver.check())
