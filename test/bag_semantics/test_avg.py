# -*- coding: utf-8 -*-

# sql1 = "SELECT AVG(age), AVG(id) FROM EMP WHERE age > 25"
# sql2 = "SELECT AVG(id), AVG(age) FROM EMP WHERE NOT age <= 25"

# EMP = [
#     t1 = [id=x1, name=x2, age=x3, dept_id=x4],
#     t2 = [id=x5, name=x6, age=x7, dept_id=x8],
# ]


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

# aggregation

AVG = Function('AVG(...)', T, StringSort(), IntSort())

attr_avg_emp_id = Const('AVG(EMP.id)_str', StringSort())
attr_avg_emp_name = Const('AVG(EMP.name)_str', StringSort())
attr_avg_emp_age = Const('AVG(EMP.age)_str', StringSort())
attr_avg_emp_dept_id = Const('AVG(EMP.dept_id)_str', StringSort())

attr_avg_dept_name = Const('AVG(DEPT.name)_str', StringSort())
attr_avg_dept_id = Const('AVG(DEPT.id)_str', StringSort())

# base tuples and their values from the DBMS
t1, t2 = Consts('t1 t2', T)
x1, x2, x3, x4 = Ints('x1 x2 x3 x4')
x5, x6, x7, x8 = Ints('x5 x6 x7 x8')
v1, v2, v3, v4 = Ints('v1 v2 v3 v4')
# final tuples of sql1 and sql2
t3, t4 = Consts('t3 t4', T)

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
    # SELECT AVG(age), AVG(id) FROM EMP WHERE age > 25
    # t1, t2 -> t3
    Not(DELETED(t3)),
    # AVG(age)
    AVG(t3, attr_avg_emp_age) == Sum([
        If(And(Not(DELETED(t1)), Not(NULL(t1, attr_emp_age)), emp_age(t1) > 25), emp_age(t1), 0),
        If(And(Not(DELETED(t2)), Not(NULL(t2, attr_emp_age)), emp_age(t2) > 25), emp_age(t2), 0),
    ]) / Sum([
        If(And(Not(DELETED(t1)), Not(NULL(t1, attr_emp_age)), emp_age(t1) > 25), 1, 0),
        If(And(Not(DELETED(t2)), Not(NULL(t2, attr_emp_age)), emp_age(t2) > 25), 1, 0),
    ]),
    Not(NULL(t3, attr_avg_emp_age)),
    # AVG(id)
    AVG(t3, attr_avg_emp_id) == Sum([
        If(And(Not(DELETED(t1)), Not(NULL(t1, attr_emp_id)), emp_id(t1) > 25), emp_id(t1), 0),
        If(And(Not(DELETED(t2)), Not(NULL(t2, attr_emp_id)), emp_id(t2) > 25), emp_id(t2), 0),
    ]) / Sum([
        If(And(Not(DELETED(t1)), Not(NULL(t1, attr_emp_id)), emp_id(t1) > 25), 1, 0),
        If(And(Not(DELETED(t2)), Not(NULL(t2, attr_emp_id)), emp_id(t2) > 25), 1, 0),
    ]),
    Not(NULL(t3, attr_avg_emp_id)),
)

result2 = And(
    # SELECT AVG(id), AVG(age) FROM EMP WHERE NOT age <= 25
    # t1, t2 -> t4
    Not(DELETED(t4)),
    # AVG(id)
    AVG(t4, attr_avg_emp_id) == Sum([
        If(And(Not(DELETED(t1)), Not(NULL(t1, attr_emp_id)), Not(emp_id(t1) <= 25)), emp_id(t1), 0),
        If(And(Not(DELETED(t2)), Not(NULL(t2, attr_emp_id)), Not(emp_id(t2) <= 25)), emp_id(t2), 0),
    ]) / Sum([
        If(And(Not(DELETED(t1)), Not(NULL(t1, attr_emp_id)), Not(emp_id(t1) <= 25)), 1, 0),
        If(And(Not(DELETED(t2)), Not(NULL(t2, attr_emp_id)), Not(emp_id(t2) <= 25)), 1, 0),
    ]),
    Not(NULL(t4, attr_avg_emp_id)),
    # AVG(age)
    AVG(t4, attr_avg_emp_age) == Sum([
        If(And(Not(DELETED(t1)), Not(NULL(t1, attr_emp_age)), Not(emp_age(t1) <= 25)), emp_age(t1), 0),
        If(And(Not(DELETED(t2)), Not(NULL(t2, attr_emp_age)), Not(emp_age(t2) <= 25)), emp_age(t2), 0),
    ]) / Sum([
        If(And(Not(DELETED(t1)), Not(NULL(t1, attr_emp_age)), Not(emp_age(t1) <= 25)), 1, 0),
        If(And(Not(DELETED(t2)), Not(NULL(t2, attr_emp_age)), Not(emp_age(t2) <= 25)), 1, 0),
    ]),
    Not(NULL(t4, attr_avg_emp_age)),
)

prerequisites = And(DBMS_facts, result1, result2)


def equals(ltuples, rtuples):
    def _tuple_equals(tuple1, tuple2):
        return And(
            And(Not(DELETED(tuple1)), Not(DELETED(tuple2))),
            Or(
                And(NULL(tuple1, attr_avg_emp_age), NULL(tuple2, attr_avg_emp_age)),
                AVG(tuple1, attr_avg_emp_age) == AVG(tuple2, attr_avg_emp_age),
            ),
            Or(
                And(NULL(tuple1, attr_avg_emp_id), NULL(tuple2, attr_avg_emp_id)),
                AVG(tuple1, attr_avg_emp_id) == AVG(tuple2, attr_avg_emp_id),
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


conclusion = equals(ltuples=[t3], rtuples=[t4])

solver.add(Not(
    Implies(prerequisites, conclusion)
))

if solver.check() == sat:
    print(solver.model())

print(solver.check())
