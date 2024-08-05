from z3 import *


def main():
    T = DeclareSort('T')
    deleted = Function('deleted', T, BoolSort())
    null = Function('null', T, StringSort(), BoolSort())

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

    # suppose we only project EMP.name and EMP.age here for simplicity

    tuple_values = And([
        emp_name(t1) == x2, emp_age(t1) == x3,
        emp_name(t2) == x2, emp_age(t2) == x3,
        # emp_name(t3) == x2, emp_age(t3) == x3,
        emp_name(t4) == x6, emp_age(t4) == x7,

        # emp_name(t5) == x2, emp_age(t5) == x3,
        emp_name(t6) == x2, emp_age(t6) == x3,
        emp_name(t7) == x6, emp_age(t7) == x7,
        emp_name(t8) == x2, emp_age(t8) == x3,
    ])

    tuple_null_facts = And([
        Not(null(t1, attr_emp_name)),
        Not(null(t2, attr_emp_name)),
        # Not(null(t3, attr_emp_name)),
        null(t3, attr_emp_name),
        Not(null(t4, attr_emp_name)),
        # Not(null(t5, attr_emp_name)),
        null(t5, attr_emp_name),
        Not(null(t6, attr_emp_name)),
        Not(null(t7, attr_emp_name)),
        Not(null(t8, attr_emp_name)),
        Not(null(t1, attr_emp_age)),
        Not(null(t2, attr_emp_age)),
        # Not(null(t3, attr_emp_age)),
        null(t3, attr_emp_age),
        Not(null(t4, attr_emp_age)),
        # Not(null(t5, attr_emp_age)),
        null(t5, attr_emp_age),
        Not(null(t6, attr_emp_age)),
        Not(null(t7, attr_emp_age)),
        Not(null(t8, attr_emp_age)),
    ])

    # throughout the encoding, a tuple may be deleted or continue to exist
    r1_r2 = And([
        Not(deleted(t1)), Not(deleted(t2)), deleted(t3), Not(deleted(t4)),
        deleted(t5), Not(deleted(t6)), Not(deleted(t7)), Not(deleted(t8))
    ])

    s = Solver()

    # each table (multiset) contains all output tuples (possibly deleted or not) after the encoding process
    r1_tuples = [t1, t2, t3, t4]
    r2_tuples = [t5, t6, t7, t8]

    # aggregation functions need to b converted to uninterpreted functions (via ==) and invoked upon
    # like regular columns
    def TupleEquals(x, y):
        return And(
            And(Not(deleted(x)), Not(deleted(y))),
            Or(
                And(null(x, attr_emp_name), null(y, attr_emp_name)),
                emp_name(x) == emp_name(y),
            ),
            Or(
                And(null(x, attr_emp_age), null(y, attr_emp_age)),
                emp_age(x) == emp_age(y),
            ),
        )

    f = []
    for t in [*r1_tuples, *r2_tuples]:
        t_multiplicity_r1 = Sum([If(TupleEquals(t, _t), 1, 0) for _t in r1_tuples])
        t_multiplicity_r2 = Sum([If(TupleEquals(t, _t), 1, 0) for _t in r2_tuples])
        f.append(Implies(Not(deleted(t)), t_multiplicity_r1 == t_multiplicity_r2))

    s.add(Not(Implies(
        And([tuple_values, tuple_null_facts, r1_r2]),
        And(f)
    )))

    print(s.check())
    if s.check() == sat:
        print(s.model())


if __name__ == '__main__':
    main()
