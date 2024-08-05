# -*- coding:utf-8 -*-

# sql1 = "SELECT name FROM (SELECT name, emp_age, id FROM EMP WHERE emp_age > 25) WHERE emp_age < 30"
# sql2 = "SELECT name FROM (SELECT id, name, emp_age FROM EMP WHERE emp_age < 30) WHERE emp_age > 25"

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

t1, t2, t3, t4 = Consts('t1 t2 t3 t4', T)
x1, x2, x3, x4 = Ints('x1 x2 x3 x4')
x5, x6, x7, x8 = Ints('x5 x6 x7 x8')

solver = Solver()

# sql1 = "SELECT COUNT(*) FROM (SELECT name, age, id FROM EMP WHERE age > 25) WHERE age < 30"
# sql2 = "SELECT COUNT(*) FROM (SELECT id, name, age FROM EMP WHERE age < 30) WHERE age > 25"

r1 = And(
    Implies(
        And(emp_age(t1) > 25, emp_age(t1) < 30, Not(NULL(t1, attr_emp_age))),
        Not(DELETED(t1)),
    ),
    Implies(
        Not(And(emp_age(t1) > 25, emp_age(t1) < 30, Not(NULL(t1, attr_emp_age)))),
        DELETED(t1),
    ),
    Implies(
        And(emp_age(t2) > 25, emp_age(t2) < 30, Not(NULL(t2, attr_emp_age))),
        Not(DELETED(t2)),
    ),
    Implies(
        Not(And(emp_age(t2) > 25, emp_age(t2) < 30, Not(NULL(t2, attr_emp_age)))),
        DELETED(t2),
    ),
)

r2 = And(
    Implies(
        And(emp_age(t3) < 30, emp_age(t3) > 25, Not(NULL(t3, attr_emp_age))),
        Not(DELETED(t3)),
    ),
    Implies(
        Not(And(emp_age(t3) < 30, emp_age(t3) > 25, Not(NULL(t3, attr_emp_age)))),
        DELETED(t3),
    ),
    Implies(
        And(emp_age(t4) < 30, emp_age(t4) > 25, Not(NULL(t4, attr_emp_age))),
        Not(DELETED(t4)),
    ),
    Implies(
        Not(And(emp_age(t4) < 30, emp_age(t4) > 25, Not(NULL(t4, attr_emp_age)))),
        DELETED(t4),
    ),
)

EQUALITY_FACTS1 = And(
    emp_id(t1) == x1, emp_name(t1) == x2, emp_age(t1) == x3, emp_dept_id(t1) == x4,
    emp_id(t2) == x5, emp_name(t2) == x6, emp_age(t2) == x7, emp_dept_id(t2) == x8,

    emp_id(t3) == x1, emp_name(t3) == x2, emp_age(t3) == x3, emp_dept_id(t3) == x4,
    emp_id(t4) == x5, emp_name(t4) == x6, emp_age(t4) == x7, emp_dept_id(t4) == x8,
)
EQUALITY_FACTS2 = And(
    emp_id(t1) == x1, emp_name(t1) == x2, emp_age(t1) == x3, emp_dept_id(t1) == x4,
    emp_id(t2) == x5, emp_name(t2) == x6, emp_age(t2) == x7, emp_dept_id(t2) == x8,

    emp_id(t3) == x5, emp_name(t3) == x6, emp_age(t3) == x7, emp_dept_id(t3) == x8,
    emp_id(t4) == x1, emp_name(t4) == x2, emp_age(t4) == x3, emp_dept_id(t4) == x4,
)
NULL_OR_NOT_FACTS = And(
    Not(NULL(t1, attr_emp_id)), Not(NULL(t1, attr_emp_name)), Not(NULL(t1, attr_emp_age)),
    Not(NULL(t1, attr_emp_dept_id)),
    Not(NULL(t2, attr_emp_id)), Not(NULL(t2, attr_emp_name)), Not(NULL(t2, attr_emp_age)),
    Not(NULL(t2, attr_emp_dept_id)),
    Not(NULL(t3, attr_emp_id)), Not(NULL(t3, attr_emp_name)), Not(NULL(t3, attr_emp_age)),
    Not(NULL(t3, attr_emp_dept_id)),
    Not(NULL(t4, attr_emp_id)), Not(NULL(t4, attr_emp_name)), Not(NULL(t4, attr_emp_age)),
    Not(NULL(t4, attr_emp_dept_id)),
)

solver.add(
    Not(
        Or(
            Implies(
                And([
                    EQUALITY_FACTS1,
                    NULL_OR_NOT_FACTS,
                    r1, r2,
                ]),
                And([
                    If(Not(DELETED(t1)), 1, 0) + If(Not(DELETED(t2)), 1, 0) == \
                    If(Not(DELETED(t3)), 1, 0) + If(Not(DELETED(t4)), 1, 0)
                ])
            ),
            Implies(
                And([
                    EQUALITY_FACTS2,
                    NULL_OR_NOT_FACTS,
                    r1, r2,
                ]),
                And([
                    Sum([
                        If(Not(DELETED(t1)), 1, 0),
                        If(Not(DELETED(t2)), 1, 0),
                    ]) == Sum([
                        If(Not(DELETED(t3)), 1, 0),
                        If(Not(DELETED(t4)), 1, 0),
                    ])
                ])
            ),
        )
    )
)

if solver.check() == sat:
    print(solver.model())

print(solver.check())
