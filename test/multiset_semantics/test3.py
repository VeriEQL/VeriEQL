from z3 import *


def debug2():
    """
    "SELECT EMP.id, EMP.name, EMP.age, EMP.dept_id, DEPT.id, DEPT.name FROM EMP LEFT OUTER JOIN DEPT ON EMP.dept_id = DEPT.id WHERE EMP.age > 25"
    "SELECT EMP.id, EMP.name, EMP.age, EMP.dept_id, DEPT.id, DEPT.name FROM DEPT RIGHT OUTER JOIN EMP ON EMP.dept_id = DEPT.id WHERE EMP.age > 25"
    """

    T = DeclareSort('T')
    deleted = Function('deleted', T, BoolSort())
    null = Function('null', T, StringSort(), BoolSort())

    emp_id = Function('EMP.id', T, IntSort())
    emp_name = Function('EMP.name', T, IntSort())
    emp_age = Function('EMP.age', T, IntSort())
    emp_dept_id = Function('EMP.dept_id', T, IntSort())
    dept_id = Function('DEPT.id', T, IntSort())
    dept_name = Function('DEPT.name', T, IntSort())

    attr_dept_name = Const('DEPT.name_str', StringSort())
    attr_dept_id = Const('DEPT.id_str', StringSort())

    attr_emp_id = Const('EMP.id_str', StringSort())
    attr_emp_name = Const('EMP.name_str', StringSort())
    attr_emp_age = Const('EMP.age_str', StringSort())
    attr_emp_dept_id = Const('EMP.dept_id_str', StringSort())

    t1_0 = Const('t1_0', T)  # base case for t1
    t1_1 = Const('t1_1', T)  # t1 join first tuple in DEPT
    t1_2 = Const('t1_2', T)  # t1 join second tuple in DEPT

    t3_0 = Const('t3_0', T)
    t3_1 = Const('t3_1', T)
    t3_2 = Const('t3_2', T)

    # suppose we only project EMP.name (from the left table) and DEPT.name (from the right table) for simplicity

    x1, x2, x3, x4 = Ints('x1 x2 x3 x4')  # t1
    x5, x6, x7, x8 = Ints('x5 x6 x7 x8')  #
    v1, v2 = Ints('v1 v2')  #
    v3, v4 = Ints('v3 v4')  #

    s = Solver()

    # SQL 1
    r1 = And([
        # Base cases
        Implies(
            And([
                And([
                    emp_age(t1_0) > 25,  # WHERE condition
                    Not(null(t1_0, attr_emp_age)),

                    deleted(t1_1),
                    deleted(t1_2),
                ]),
            ]),
            And([
                Not(deleted(t1_0)),

                # # attributes from base tuples
                # emp_id(t1_0) == x1,
                # emp_name(t1_0) == x2,
                # emp_age(t1_0) == x3,
                # emp_dept_id(t1_0) == x4,
                # null(t1_0, attr_dept_id),
                # null(t1_0, attr_dept_name),
            ])
        ),
        Implies(
            Not(
                And([
                    emp_age(t1_0) > 25,
                    Not(null(t1_0, attr_emp_age)),

                    deleted(t1_1),
                    deleted(t1_2),
                ])
            ),
            deleted(t1_0),
        ),

        # Left 1 --concat--> Right 1
        Implies(
            And([
                emp_age(t1_1) > 25,  # WHERE condition
                Not(null(t1_1, attr_emp_age)),

                emp_dept_id(t1_1) == dept_id(t1_1),  # JOIN condition
                Not(null(t1_1, attr_emp_dept_id)),
                Not(null(t1_1, attr_dept_id)),
            ]),
            And([
                # # attributes from base tuples
                # emp_id(t1_1) == x1,
                # emp_name(t1_1) == x2,
                # emp_age(t1_1) == x3,
                # emp_dept_id(t1_1) == x4,
                # dept_id(t1_1) == v1,
                # dept_name(t1_1) == v2,

                Not(deleted(t1_1)),
                deleted(t1_0),
            ])
        ),
        Implies(
            Not(
                And([
                    emp_age(t1_1) > 25,  # WHERE condition
                    Not(null(t1_1, attr_emp_age)),

                    emp_dept_id(t1_1) == dept_id(t1_1),  # JOIN condition
                    Not(null(t1_1, attr_emp_dept_id)),
                    Not(null(t1_1, attr_dept_id)),
                ])
            ),
            And([
                deleted(t1_1),
            ])
        ),

        # Left 1 --concat--> Right 2
        Implies(
            And([
                emp_age(t1_2) > 25,  # WHERE condition
                Not(null(t1_2, attr_emp_age)),

                emp_dept_id(t1_2) == dept_id(t1_2),  # JOIN condition
                Not(null(t1_2, attr_emp_dept_id)),
                Not(null(t1_2, attr_dept_id)),
            ]),
            And([
                # # attributes from base tuples
                # emp_id(t1_2) == x1,
                # emp_name(t1_2) == x2,
                # emp_age(t1_2) == x3,
                # emp_dept_id(t1_2) == x4,
                # dept_id(t1_2) == v3,
                # dept_name(t1_2) == v4,

                Not(deleted(t1_2)),
                deleted(t1_0),
            ])
        ),
        Implies(
            Not(
                And([
                    emp_age(t1_2) > 25,  # WHERE condition
                    Not(null(t1_2, attr_emp_age)),

                    emp_dept_id(t1_2) == dept_id(t1_2),  # JOIN condition
                    Not(null(t1_2, attr_emp_dept_id)),
                    Not(null(t1_2, attr_dept_id)),
                ])
            ),
            And([
                deleted(t1_2),
            ])
        ),
    ])

    # SQL 2
    r2 = And([
        # Base cases
        Implies(
            And([
                emp_age(t3_0) > 25,  # WHERE condition
                Not(null(t3_0, attr_emp_age)),

                deleted(t3_1),
                deleted(t3_2),
            ]),
            And([
                # # attributes from base tuples
                # emp_id(t3_0) == x1,
                # emp_name(t3_0) == x2,
                # emp_age(t3_0) == x3,
                # emp_dept_id(t3_0) == x4,
                # dept_id(t3_0) == v3,
                # dept_name(t3_0) == v4,

                Not(deleted(t3_0)),
            ])
        ),
        Implies(
            Not(
                And([
                    emp_age(t3_0) > 25,
                    Not(null(t3_0, attr_emp_age)),

                    deleted(t3_1),
                    deleted(t3_2),
                ])
            ),
            deleted(t3_0),
        ),

        # Left 1 --concat--> Right 1
        Implies(
            And([
                emp_dept_id(t3_1) == dept_id(t3_1),  # JOIN condition
                Not(null(t3_1, attr_emp_dept_id)),
                Not(null(t3_1, attr_dept_id)),

                emp_age(t3_1) > 25,  # WHERE condition
                Not(null(t3_1, attr_emp_age)),
            ]),
            And([
                # # attributes from base tuples
                # emp_id(t3_1) == x1,
                # emp_name(t3_1) == x2,
                # emp_age(t3_1) == x3,
                # emp_dept_id(t3_1) == x4,
                # dept_id(t3_1) == v1,
                # dept_name(t3_1) == v2,

                Not(deleted(t3_1)),
                deleted(t3_0),
            ]),
        ),
        Implies(
            Not(
                And([
                    emp_age(t3_1) > 25,  # WHERE condition
                    Not(null(t3_1, attr_emp_age)),
                    emp_dept_id(t3_1) == dept_id(t3_1),  # JOIN condition
                    Not(null(t3_1, attr_emp_dept_id)),
                    Not(null(t3_1, attr_dept_id)),
                ])
            ),
            And([
                deleted(t3_1),
            ]),
        ),

        # Left 1 --concat--> Right 2
        Implies(
            And([
                emp_dept_id(t3_2) == dept_id(t3_2),  # JOIN condition
                Not(null(t3_2, attr_emp_dept_id)),
                Not(null(t3_2, attr_dept_id)),

                emp_age(t3_2) > 25,  # WHERE condition
                Not(null(t3_2, attr_emp_age)),
            ]),
            And([
                # # attributes from base tuples
                # emp_id(t3_2) == x1,
                # emp_name(t3_2) == x2,
                # emp_age(t3_2) == x3,
                # emp_dept_id(t3_2) == x4,
                # dept_id(t3_2) == v3,
                # dept_name(t3_2) == v4,

                Not(deleted(t3_2)),
                deleted(t3_0),
            ]),
        ),
        Implies(
            Not(
                And([
                    emp_age(t3_2) > 25,  # WHERE condition
                    Not(null(t3_2, attr_emp_age)),
                    emp_dept_id(t3_2) == dept_id(t3_2),  # JOIN condition
                    Not(null(t3_2, attr_emp_dept_id)),
                    Not(null(t3_2, attr_dept_id)),
                ])
            ),
            And([
                deleted(t3_2),
            ]),
        ),
    ])

    # load all symbolic tuples' values (can load columns ad hoc or load just all columns) as the premise
    tuple_values = And([
        # LEFT JOIN
        emp_id(t1_1) == x1,
        emp_name(t1_1) == x2, emp_age(t1_1) == x3, emp_dept_id(t1_1) == x4,
        dept_name(t1_1) == v2, dept_id(t1_1) == v1,

        emp_id(t1_2) == x1,
        emp_name(t1_2) == x2, emp_age(t1_2) == x3, emp_dept_id(t1_2) == x4,
        dept_name(t1_2) == v4, dept_id(t1_2) == v3,

        emp_id(t1_0) == x1,
        emp_name(t1_0) == x2, emp_age(t1_0) == x3, emp_dept_id(t1_0) == x4,

        # RIGHT JOIN
        emp_id(t3_1) == x1,
        emp_name(t3_1) == x2, emp_age(t3_1) == x3, emp_dept_id(t3_1) == x4,
        dept_name(t3_1) == v2, dept_id(t3_1) == v1,

        emp_id(t3_2) == x1,
        emp_name(t3_2) == x2, emp_age(t3_2) == x3, emp_dept_id(t3_2) == x4,
        dept_name(t3_2) == v4, dept_id(t3_2) == v3,

        emp_id(t3_0) == x1,
        emp_name(t3_0) == x2, emp_age(t3_0) == x3, emp_dept_id(t3_0) == x4,
    ])

    tuple_null_facts = And([
        #
        Not(null(t1_1, attr_emp_name)), Not(null(t1_1, attr_emp_age)), Not(null(t1_1, attr_emp_dept_id)),
        Not(null(t1_1, attr_emp_id)),
        Not(null(t1_1, attr_dept_name)), Not(null(t1_1, attr_dept_id)),

        Not(null(t1_2, attr_emp_name)), Not(null(t1_2, attr_emp_age)), Not(null(t1_2, attr_emp_dept_id)),
        Not(null(t1_2, attr_emp_id)),
        Not(null(t1_2, attr_dept_name)), Not(null(t1_2, attr_dept_id)),

        Not(null(t1_0, attr_emp_name)), Not(null(t1_0, attr_emp_age)),
        Not(null(t1_0, attr_emp_id)), Not(null(t1_0, attr_emp_dept_id)),
        null(t1_0, attr_dept_name), null(t1_0, attr_dept_id),

        Not(null(t3_1, attr_emp_name)), Not(null(t3_1, attr_emp_age)), Not(null(t3_1, attr_emp_dept_id)),
        Not(null(t3_1, attr_emp_id)),
        Not(null(t3_1, attr_dept_name)), Not(null(t3_1, attr_dept_id)),

        Not(null(t3_2, attr_emp_name)), Not(null(t3_2, attr_emp_age)), Not(null(t3_2, attr_emp_dept_id)),
        Not(null(t3_2, attr_emp_id)),
        Not(null(t3_2, attr_dept_name)), Not(null(t3_2, attr_dept_id)),

        Not(null(t3_0, attr_emp_name)), Not(null(t3_0, attr_emp_age)), Not(null(t3_0, attr_emp_dept_id)),
        Not(null(t3_0, attr_emp_id)),
        null(t3_0, attr_dept_name), null(t3_0, attr_dept_id),
    ])

    s.add(Not(
        Implies(
            And([
                # don't need to add equalities of where and join conditions here anymore
                tuple_values,
                tuple_null_facts,
                r1, r2
            ]),
            And([
                deleted(t1_0) == deleted(t3_0),
                Implies(
                    Not(deleted(t1_0)),
                    And([
                        # projection attributes that are not NULL
                        null(t1_0, attr_emp_id) == null(t3_0, attr_emp_id),
                        Implies(
                            And(Not(null(t1_0, attr_emp_id)), Not(null(t3_0, attr_emp_id))),
                            emp_id(t1_0) == emp_id(t3_0),
                        ),

                        null(t1_0, attr_emp_name) == null(t3_0, attr_emp_name),
                        Implies(
                            And(Not(null(t1_0, attr_emp_name)), Not(null(t3_0, attr_emp_name))),
                            emp_name(t1_0) == emp_name(t3_0),
                        ),

                        null(t1_0, attr_emp_age) == null(t3_0, attr_emp_age),
                        Implies(
                            And(Not(null(t1_0, attr_emp_age)), Not(null(t3_0, attr_emp_age))),
                            emp_age(t1_0) == emp_age(t3_0),
                        ),

                        null(t1_0, attr_emp_dept_id) == null(t3_0, attr_emp_dept_id),
                        Implies(
                            And(Not(null(t1_0, attr_emp_dept_id)), Not(null(t3_0, attr_emp_dept_id))),
                            emp_dept_id(t1_0) == emp_dept_id(t3_0)
                        ),

                        # projection attributes that are NULL
                        null(t1_0, attr_dept_name) == null(t3_0, attr_dept_name),
                        null(t1_0, attr_dept_id) == null(t3_0, attr_dept_id),
                    ])
                ),

                deleted(t1_1) == deleted(t3_1),
                Implies(
                    Not(deleted(t1_1)),
                    And([
                        # check all attributes
                        # if not deleted, first check if null is ==
                        # if not null, check equality of the column
                        null(t1_1, attr_emp_id) == null(t3_1, attr_emp_id),
                        Implies(
                            And(Not(null(t1_1, attr_emp_id)), Not(null(t3_1, attr_emp_id))),
                            emp_id(t1_1) == emp_id(t3_1),
                        ),

                        null(t1_1, attr_emp_name) == null(t3_1, attr_emp_name),
                        Implies(
                            And(Not(null(t1_1, attr_emp_name)), Not(null(t3_1, attr_emp_name))),
                            emp_name(t1_1) == emp_name(t3_1),
                        ),

                        null(t1_1, attr_emp_age) == null(t3_1, attr_emp_age),
                        Implies(
                            And(Not(null(t1_1, attr_emp_age)), Not(null(t3_1, attr_emp_age))),
                            emp_age(t1_1) == emp_age(t3_1),
                        ),

                        null(t1_1, attr_emp_dept_id) == null(t3_1, attr_emp_dept_id),
                        Implies(
                            And(Not(null(t1_1, attr_emp_dept_id)), Not(null(t3_1, attr_emp_dept_id))),
                            emp_dept_id(t1_1) == emp_dept_id(t3_1)
                        ),

                        null(t1_1, attr_dept_id) == null(t3_1, attr_dept_id),
                        Implies(
                            And(Not(null(t1_1, attr_dept_id)), Not(null(t3_1, attr_dept_id))),
                            dept_id(t1_1) == dept_id(t3_1)
                        ),

                        null(t1_1, attr_dept_name) == null(t3_1, attr_dept_name),
                        Implies(
                            And(Not(null(t1_1, attr_dept_name)), Not(null(t3_1, attr_dept_name))),
                            dept_name(t1_1) == dept_name(t3_1),
                        ),
                    ])
                ),

                deleted(t1_2) == deleted(t3_2),
                Implies(
                    Not(deleted(t1_2)),
                    And([
                        # check all attributes
                        null(t1_2, attr_emp_id) == null(t3_2, attr_emp_id),
                        Implies(
                            And(Not(null(t1_2, attr_emp_id)), Not(null(t3_2, attr_emp_id))),
                            emp_id(t1_2) == emp_id(t3_2),
                        ),

                        null(t1_2, attr_emp_name) == null(t3_2, attr_emp_name),
                        Implies(
                            And(Not(null(t1_2, attr_emp_name)), Not(null(t3_2, attr_emp_name))),
                            emp_name(t1_2) == emp_name(t3_2),
                        ),

                        null(t1_2, attr_emp_age) == null(t3_2, attr_emp_age),
                        Implies(
                            And(Not(null(t1_2, attr_emp_age)), Not(null(t3_2, attr_emp_age))),
                            emp_age(t1_2) == emp_age(t3_2),
                        ),

                        null(t1_2, attr_emp_dept_id) == null(t3_2, attr_emp_dept_id),
                        Implies(
                            And(Not(null(t1_2, attr_emp_dept_id)), Not(null(t3_2, attr_emp_dept_id))),
                            emp_dept_id(t1_2) == emp_dept_id(t3_2)
                        ),

                        null(t1_2, attr_dept_id) == null(t3_2, attr_dept_id),
                        Implies(
                            And(Not(null(t1_2, attr_dept_id)), Not(null(t3_2, attr_dept_id))),
                            dept_id(t1_2) == dept_id(t3_2)
                        ),

                        null(t1_2, attr_dept_name) == null(t3_2, attr_dept_name),
                        Implies(
                            And(Not(null(t1_2, attr_dept_name)), Not(null(t3_2, attr_dept_name))),
                            dept_name(t1_2) == dept_name(t3_2)
                        ),
                    ])
                ),
            ])
        )))
    print(s.check())
    if s.check() == sat:
        print(s.model())


if __name__ == '__main__':
    debug2()
