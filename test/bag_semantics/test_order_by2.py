# -*- coding: utf-8 -*-

import itertools

from z3 import *

T = DeclareSort('T')
DELETED = Function('DELETED', T, BoolSort())
NULL = Function('NULL', T, StringSort(), BoolSort())

emp_name = Function('EMP.name', T, IntSort())
emp_age = Function('EMP.age', T, IntSort())

attr_emp_name = Const('EMP.name', StringSort())
attr_emp_age = Const('EMP.age', StringSort())

t1 = Const('t1', T)
t2 = Const('t2', T)
t3 = Const('t3', T)
t4 = Const('t4', T)

t5 = Const('t5', T)
t6 = Const('t6', T)
t7 = Const('t7', T)
t8 = Const('t8', T)

x2 = Const('x2', IntSort())
x3 = Const('x3', IntSort())
x6 = Const('x6', IntSort())
x7 = Const('x7', IntSort())

# suppose we only project EMP.name and EMP.age for simplicity

tuple_values = And([
    emp_name(t1) == x2, emp_age(t1) == x3, Not(NULL(t1, attr_emp_name)), Not(NULL(t1, attr_emp_age)),
    emp_name(t2) == x2, emp_age(t2) == x3, Not(NULL(t2, attr_emp_name)), Not(NULL(t2, attr_emp_age)),
    emp_name(t3) == x2, emp_age(t3) == x3, Not(NULL(t3, attr_emp_name)), Not(NULL(t3, attr_emp_age)),
    emp_name(t4) == x6, emp_age(t4) == x7, Not(NULL(t4, attr_emp_name)), Not(NULL(t4, attr_emp_age)),

    emp_name(t5) == x2, emp_age(t5) == x3, Not(NULL(t5, attr_emp_name)), Not(NULL(t5, attr_emp_age)),
    emp_name(t6) == x2, emp_age(t6) == x3, Not(NULL(t6, attr_emp_name)), Not(NULL(t6, attr_emp_age)),
    emp_name(t7) == x6, emp_age(t7) == x7, Not(NULL(t7, attr_emp_name)), Not(NULL(t7, attr_emp_age)),
    emp_name(t8) == x2, emp_age(t8) == x3, Not(NULL(t8, attr_emp_name)), Not(NULL(t8, attr_emp_age)),
])

r1_r2 = And([
    Not(DELETED(t1)), Not(DELETED(t2)), DELETED(t3), Not(DELETED(t4)),
    DELETED(t5), Not(DELETED(t6)), Not(DELETED(t7)), Not(DELETED(t8))
])

r1_tuples = [t1, t2, t4, t3]
r2_tuples = [t5, t7, t8, t6]

counter = 20


def order_by(tuple_list, keys):
    global counter
    # sorted_tuple_list = [Const(f'x{counter + idx}', T) for idx in range(len(tuple_list))]
    counter += len(tuple_list) + 1

    constraints = []
    # for i in range(len(tuple_list)):
    #     constraints.append(sorted_tuple_list[i] == tuple_list[i])
    sorted_tuple_list = tuple_list

    # move DELETED tuples to the tuple_list end
    for j in range(len(sorted_tuple_list)):
        for i in range(len(sorted_tuple_list) - j - 1):
            x = sorted_tuple_list[i]
            y = sorted_tuple_list[i + 1]

            _x, _y = Const(f't{counter}', T), Const(f't{counter + 1}', T)
            counter += 2

            constraints.append(
                If(
                    Or([And(DELETED(x), Not(DELETED(y)))]),
                    And(_x == y, _y == x),
                    And(_x == x, _y == y)
                )
            )

            sorted_tuple_list[i] = _x
            sorted_tuple_list[i + 1] = _y

    def should_swap(x, y):
        # NULL is smaller than every non-NULL variables
        swap_cond = []
        should_compare_next_col = []
        for attr_key, NULL_key, order_key in keys:
            if order_key == 'DESC':
                swap_cond.append(
                    And(
                        *should_compare_next_col,
                        Or(
                            attr_key(x) < attr_key(y),
                            And(NULL(x, NULL_key), Not(NULL(y, NULL_key))),
                        )),
                )
            else:
                swap_cond.append(
                    And(
                        *should_compare_next_col,
                        Or(
                            attr_key(x) > attr_key(y),
                            And(Not(NULL(x, NULL_key)), NULL(y, NULL_key)),
                        ),
                    )
                )
            should_compare_next_col.append(attr_key(x) == attr_key(y))
        return Or(swap_cond)

    """
    foreach key in keys do
        if key is regular column then
            if key uses DESC then
                swap_cond := should_compare_next_col /\ (key(x) < key(y) \/ (key(x) is NULL /\ key(y) is not NULL))
            else
                swap_cond := should_compare_next_col /\ (key(x) > key(y) \/ (key(y) is NULL /\ key(x) is not NULL))
            endif
            should_compare_next_col := should_compare_next_col /\ (key(x) == key(y) \/ (key(x) is NULL /\ key(y) is NULL))
        else if key is a predictae then
            // predicate is usually a atom op atom, if atom is an attribute, for example, name == 2
            // we translate it into something like this for the swap condition: EMP_name(y) == 2 /\ not EMP_name(x) == 2
            swap_cond := should_compare_next_col /\ predictae(y) /\ not predictae(x)
            should_compare_next_col := should_compare_next_col /\ predictae(x) /\ predictae(y)
        endif
    end
    """

    # sort
    for j in range(len(sorted_tuple_list)):
        for i in range(len(sorted_tuple_list) - j - 1):
            x = sorted_tuple_list[i]
            y = sorted_tuple_list[i + 1]

            _x, _y = Const(f't{counter}', T), Const(f't{counter + 1}', T)
            counter += 2

            constraints.append(
                If(
                    should_swap(x, y),
                    And(_x == y, _y == x),
                    And(_x == x, _y == y),
                )
            )

            sorted_tuple_list[i] = _x
            sorted_tuple_list[i + 1] = _y

    return sorted_tuple_list, constraints


ORDER_KEYS = [(emp_age, attr_emp_age, "DESC"), (emp_name, attr_emp_name, "ASC")]
result1, constraints1 = order_by(r1_tuples, ORDER_KEYS)
result2, constraints2 = order_by(r2_tuples, ORDER_KEYS)
cmp_constraints = And([
    And(
        DELETED(x) == DELETED(y),
        Implies(
            And(Not(DELETED(x)), Not(DELETED(y))),
            And([emp_name(x) == emp_name(y), emp_name(x) == emp_name(y)]),
        ),
    )
    for x, y in zip(result1, result2)
])

premise = And([
    r1_r2, tuple_values,  # DBMS facts
    *constraints1, *constraints2,  # result of SQL query 1 and 2
])


def equals(ltuples, rtuples):
    def _tuple_equals(tuple1, tuple2):
        return And(
            And(Not(DELETED(tuple1)), Not(DELETED(tuple2))),
            Or(
                And(NULL(tuple1, attr_emp_name), NULL(tuple2, attr_emp_name)),
                emp_name(tuple1) == emp_name(tuple2),
            ),
            Or(
                And(NULL(tuple1, attr_emp_age), NULL(tuple2, attr_emp_age)),
                emp_age(tuple1) == emp_age(tuple2),
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
    formulas = And(*formulas, cmp_constraints, )
    return formulas


conclusion = equals(ltuples=result1, rtuples=result2)

solver = Solver()

solver.add(Not(
    Implies(premise, conclusion)
))

if solver.check() == sat:
    print(solver.model())

print(solver.check())
