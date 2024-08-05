# -*- coding: utf-8 -*-

# sql1 = "SELECT COUNT(*), COUNT(name) FROM EMP WHERE age < 30"
# sql2 = "SELECT COUNT(name), COUNT(*) FROM EMP WHERE NOT age >= 30"

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

count = Function('COUNT(...)', T, StringSort(), IntSort())
attr_count_all = Const('COUNT(*).str', StringSort())

attr_count_emp_id = Const('COUNT(EMP.id)_str', StringSort())
attr_count_emp_name = Const('COUNT(EMP.name)_str', StringSort())
attr_count_emp_age = Const('COUNT(EMP.age)_str', StringSort())
attr_count_emp_dept_id = Const('COUNT(EMP.dept_id)_str', StringSort())

attr_count_dept_name = Const('COUNT(DEPT.name)_str', StringSort())
attr_count_dept_id = Const('COUNT(DEPT.id)_str', StringSort())

# base tuples and their values from the DBMS
t1, t2 = Consts('t1 t2', T)
x1, x2, x3, x4 = Ints('x1 x2 x3 x4')
x5, x6, x7, x8 = Ints('x5 x6 x7 x8')
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
    # SELECT COUNT(*), COUNT(name) FROM EMP WHERE age < 30
    # t1, t2 -> t3
    Not(DELETED(t3)),
    # COUNT(*)
    count(t3, attr_count_all) == Sum([
        If(And(Not(DELETED(t1)), emp_age(t1) < 30), 1, 0),
        If(And(Not(DELETED(t2)), emp_age(t2) < 30), 1, 0),
    ]),
    Not(NULL(t3, attr_count_all)),
    # COUNT(name)
    count(t3, attr_emp_name) == Sum([
        If(And(Not(DELETED(t1)), Not(NULL(t1, attr_emp_name)), emp_age(t1) < 30), 1, 0),
        If(And(Not(DELETED(t2)), Not(NULL(t2, attr_emp_name)), emp_age(t2) < 30), 1, 0),
    ]),
    Not(NULL(t3, attr_count_emp_name)),
)
result2 = And(
    # SELECT COUNT(name), COUNT(*) FROM EMP WHERE age < 30
    # t1, t2 -> t4
    Not(DELETED(t4)),
    # COUNT(name)
    count(t4, attr_emp_name) == Sum([
        If(And(Not(DELETED(t1)), Not(NULL(t1, attr_emp_name)), emp_age(t1) < 30), 1, 0),
        If(And(Not(DELETED(t2)), Not(NULL(t2, attr_emp_name)), emp_age(t2) < 30), 1, 0),
    ]),
    Not(NULL(t4, attr_count_emp_name)),
    # COUNT(*)
    count(t4, attr_count_all) == Sum([
        If(And(Not(DELETED(t1)), emp_age(t1) < 30), 1, 0),
        If(And(Not(DELETED(t2)), emp_age(t2) < 30), 1, 0),
    ]),
    Not(NULL(t4, attr_count_all)),
)

prerequisites = And(DBMS_facts, result1, result2)


def equals(ltuples, rtuples):
    def _tuple_equals(tuple1, tuple2):
        return And(
            And(Not(DELETED(tuple1)), Not(DELETED(tuple2))),
            Or(
                And(NULL(tuple1, attr_count_emp_name), NULL(tuple2, attr_count_emp_name)),
                count(tuple1, attr_emp_name) == count(tuple2, attr_emp_name),
            ),
            Or(
                And(NULL(tuple1, attr_count_all), NULL(tuple2, attr_count_all)),
                count(tuple1, attr_count_all) == count(tuple2, attr_count_all),
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
