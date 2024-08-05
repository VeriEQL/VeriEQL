from z3 import *

T = DeclareSort('T')
deleted = Function('deleted', T, BoolSort())
null = Function('null', T, StringSort(), BoolSort())

emp_name = Function('EMP.name', T, IntSort())
emp_age = Function('EMP.age', T, IntSort())

attr_emp_name = Const('EMP.name', StringSort())
attr_emp_age = Const('EMP.age', StringSort())
counter = 20


def order_by(lst, keys):
    global counter
    f = []
    n = len(lst)
    sorted_list = [Const(f't{i}', T) for i in range(counter, counter + n)]
    counter += n + 1

    for i in range(n):
        f.append(sorted_list[i] == lst[i])

    def should_swap(x, y):
        swap_cond = []
        should_compare_next_col = []
        for key in keys:
            if key[1] == 'DESC':
                swap_cond.append(And(*should_compare_next_col, key[0](x) < key[0](y)))
            else:
                swap_cond.append(And(*should_compare_next_col, key[0](x) > key[0](y)))
            should_compare_next_col.append(key[0](x) == key[0](y))
        return Or(swap_cond)

    # bubble sort to shift deleted tuples to the end of the list
    for _ in range(len(sorted_list)):
        constraints = []
        for i in range(len(sorted_list) - 1):
            x = sorted_list[i]
            y = sorted_list[i + 1]

            _x, _y = Const(f't{counter}', T), Const(f't{counter + 1}', T)
            counter += 2

            constraint = If(
                Or([And(deleted(x), Not(deleted(y)))]),
                And(_x == y, _y == x),
                And(_x == x, _y == y)
            )

            sorted_list[i] = _x
            sorted_list[i + 1] = _y
            constraints.append(constraint)
        f.extend(constraints)

    # bubble sort to actually sort tuples according to keys
    for _ in range(len(sorted_list)):
        constraints = []
        for i in range(len(sorted_list) - 1):
            x = sorted_list[i]
            y = sorted_list[i + 1]

            _x, _y = Const(f't{counter}', T), Const(f't{counter + 1}', T)
            counter += 2

            constraint = If(
                should_swap(x, y),
                And(_x == y, _y == x),
                And(_x == x, _y == y),
            )

            sorted_list[i] = _x
            sorted_list[i + 1] = _y
            constraints.append(constraint)
        f.extend(constraints)
    return sorted_list, f


def main():
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
        emp_name(t1) == x2, emp_age(t1) == x3,
        emp_name(t2) == x2, emp_age(t2) == x3,
        emp_name(t3) == x2, emp_age(t3) == x3,
        emp_name(t4) == x6, emp_age(t4) == x7,

        emp_name(t5) == x2, emp_age(t5) == x3,
        emp_name(t6) == x2, emp_age(t6) == x3,
        emp_name(t7) == x6, emp_age(t7) == x7,
        emp_name(t8) == x2, emp_age(t8) == x3,
    ])

    r1_r2 = And([
        Not(deleted(t1)), Not(deleted(t2)), deleted(t3), Not(deleted(t4)),
        deleted(t5), Not(deleted(t6)), Not(deleted(t7)), Not(deleted(t8))
    ])

    r1_tuples = [t1, t2, t4, t3]
    r2_tuples = [t5, t7, t8, t6]

    # if both queries have ORDER BY age DESC, the column `name` should be auto-filled
    r1_sorted, sort_constraints1 = order_by(r1_tuples, [(emp_age, "DESC"), (emp_name, "ASC")])
    r2_sorted, sort_constraints2 = order_by(r2_tuples, [(emp_age, "DESC"), (emp_name, "ASC")])

    s = Solver()
    # s.add(And([r1_r2, tuple_values, *sort_constraints1, *sort_constraints2]))
    s.add(Not(Implies(
        And([r1_r2, tuple_values, *sort_constraints1, *sort_constraints2]),
        And([And(deleted(x) == deleted(y),
                 Implies(Not(deleted(x)), And([emp_name(x) == emp_name(y), emp_age(x) == emp_age(y)])))
             for x, y in zip(r1_sorted, r2_sorted)])
    )))

    print(s.check())
    if s.check() == sat:
        model = s.model()
        print(model)
        print([model.eval(emp_age(x), model_completion=True) for x in r1_sorted])
        print([model.eval(emp_age(x), model_completion=True) for x in r2_sorted])
        print([model.eval(emp_name(x), model_completion=True) for x in r1_sorted])
        print([model.eval(emp_name(x), model_completion=True) for x in r2_sorted])
        print([model.eval(deleted(x), model_completion=True) for x in r1_sorted])
        print([model.eval(deleted(x), model_completion=True) for x in r2_sorted])


if __name__ == '__main__':
    main()
