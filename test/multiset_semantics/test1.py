# -*- coding:utf-8 -*-

# sql1 = "SELECT name FROM (SELECT name, age, id FROM EMP WHERE age > 25) WHERE age < 30"
# sql2 = "SELECT name FROM (SELECT id, name, age FROM EMP WHERE age < 30) WHERE age > 25"

from z3 import *

T = DeclareSort('T')
id = Function('id', T, IntSort())
age = Function('age', T, IntSort())
name = Function('name', T, IntSort())
dept_id = Function('dept_id', T, IntSort())
deleted = Function('deleted', T, BoolSort())
NULL = Function('null', T, StringSort(), BoolSort())
age_string = Const('age', StringSort())

t1, t2, t3, t4 = Consts('t1 t2 t3 t4', T)
x1, x2, x3, x4 = Ints('x1 x2 x3 x4')
x5, x6, x7, x8 = Ints('x5 x6 x7 x8')

solver = Solver()

# sql1 = "SELECT name FROM (SELECT name, age, id FROM EMP WHERE age > 25) WHERE age < 30"
# sql2 = "SELECT name FROM (SELECT id, name, age FROM EMP WHERE age < 30) WHERE age > 25"

r1 = And(
    Implies(
        And(age(t1) > 25, age(t1) < 30, Not(NULL(t1, age_string))),
        And(name(t1) == x2, age(t1) == x3, Not(deleted(t1))),
    ),
    Implies(
        Not(And(age(t1) > 25, age(t1) < 30, Not(NULL(t1, age_string)))),
        deleted(t1),
    ),
    Implies(
        And(age(t2) > 25, age(t2) < 30, Not(NULL(t2, age_string))),
        And(name(t2) == x6, age(t2) == x7, Not(deleted(t2))),
    ),
    Implies(
        Not(And(age(t2) > 25, age(t2) < 30, Not(NULL(t2, age_string)))),
        deleted(t2),
    ),
)

r2 = And(
    Implies(
        And(age(t3) < 30, age(t3) > 25, Not(NULL(t3, age_string))),
        And(name(t3) == x2, age(t3) == x3, Not(deleted(t3))),
    ),
    Implies(
        Not(And(age(t3) < 30, age(t3) > 25, Not(NULL(t3, age_string)))),
        deleted(t3),
    ),
    Implies(
        And(age(t4) < 30, age(t4) > 25, Not(NULL(t4, age_string))),
        And(name(t4) == x6, age(t4) == x7, Not(deleted(t4))),
    ),
    Implies(
        Not(And(age(t4) < 30, age(t4) > 25, Not(NULL(t4, age_string)))),
        deleted(t4),
    ),
)

solver.add(
    Not(
        Or(
            Implies(
                And(
                    r1, r2,
                    age(t1) == age(t3), age(t2) == age(t4),
                    Not(NULL(t1, age_string)),
                    Not(NULL(t2, age_string)),
                    Not(NULL(t3, age_string)),
                    Not(NULL(t4, age_string)),
                ),
                And(
                    deleted(t1) == deleted(t3),
                    Implies(Not(deleted(t1)), name(t1) == name(t3)),
                    deleted(t2) == deleted(t4),
                    Implies(Not(deleted(t2)), name(t2) == name(t4)),
                ),
            ),
            Implies(
                And(age(t1) == age(t4), age(t2) == age(t3), r1, r2,
                    Not(NULL(t1, age_string)),
                    Not(NULL(t2, age_string)),
                    Not(NULL(t3, age_string)),
                    Not(NULL(t4, age_string)),
                    ),
                And(
                    deleted(t1) == deleted(t4),
                    Implies(Not(deleted(t1)), name(t1) == name(t4)),
                    deleted(t2) == deleted(t3),
                    Implies(Not(deleted(t2)), name(t2) == name(t3)),
                ),
            ),
        )
    )
)

if solver.check() == sat:
    print(solver.model())
