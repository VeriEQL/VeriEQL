from z3 import *


def main():
    T = DeclareSort('T')
    deleted = Function('deleted', T, BoolSort())
    joined = Function('joined', T, BoolSort())
    null = Function('null', T, StringSort(), BoolSort())

    emp_name = Function('EMP.name', T, IntSort())
    emp_age = Function('EMP.age', T, IntSort())
    emp_dept_id = Function('EMP.dept_id', T, IntSort())
    dept_id = Function('DEPT.id', T, IntSort())
    dept_name = Function('DEPT.name', T, IntSort())

    attr_dept_name = Const('DEPT.name', StringSort())

    # there are two tuples in EMP - t1 and t2

    t1 = Const('t1', T)
    t1_0 = Const('t1_0', T)  # base case for t1
    t1_1 = Const('t1_1', T)  # t1 join first tuple in DEPT
    t1_2 = Const('t1_2', T)  # t1 join second tuple in DEPT
    t2 = Const('t2', T)
    t2_0 = Const('t2_0', T)
    t2_1 = Const('t2_1', T)
    t2_2 = Const('t2_2', T)

    t3 = Const('t3', T)
    t3_0 = Const('t3_0', T)
    t3_1 = Const('t3_1', T)
    t3_2 = Const('t3_2', T)
    t4 = Const('t4', T)
    t4_0 = Const('t4_0', T)
    t4_1 = Const('t4_1', T)
    t4_2 = Const('t4_2', T)

    # suppose we only project EMP.name (from the left table) and DEPT.name (from the right table) for brevity

    x2 = Const('x2', IntSort())
    x3 = Const('x3', IntSort())
    x6 = Const('x6', IntSort())
    x7 = Const('x7', IntSort())
    v2 = Const('v2', IntSort())
    v4 = Const('v4', IntSort())

    s = Solver()

    # SQL 1
    r1 = And([

        # Left 1 --concat--> Right 1
        Implies(
            emp_age(t1_1) > 25,  # WHERE condition
            And([
                Implies(
                    emp_dept_id(t1_1) == dept_id(t1_1),  # JOIN condition
                    And([
                        # equalities of projected attributes in both table
                        emp_name(t1_1) == x2,
                        dept_name(t1_1) == v2,
                        # not(null([each attribute in the RIGHT table]))
                        Not(null(t1_1, attr_dept_name)),
                        Not(deleted(t1_1)),
                        joined(t1)
                    ])
                ),
                Implies(Not(emp_dept_id(t1_1) == dept_id(t1_1)), deleted(t1_1)),
            ])
        ),
        Implies(Not(emp_age(t1_1) > 25), deleted(t1_1)),

        # Left 1 --concat--> Right 2
        Implies(
            emp_age(t1_2) > 25,  # WHERE condition
            And([
                Implies(
                    emp_dept_id(t1_2) == dept_id(t1_2),  # JOIN condition
                    And([
                        # equalities of projected attributes in both table
                        emp_name(t1_2) == x2,
                        dept_name(t1_2) == v4,
                        # not(null([each attribute in the RIGHT table]))
                        Not(null(t1_2, attr_dept_name)),
                        Not(deleted(t1_2)),
                        joined(t1)
                    ])
                ),
                Implies(Not(emp_dept_id(t1_2) == dept_id(t1_2)), deleted(t1_2))
            ])
        ),
        Implies(Not(emp_age(t1_2) > 25), deleted(t1_2)),
        # Left 2 --concat--> Right 1
        Implies(
            emp_age(t2_1) > 25,  # WHERE condition
            And([
                Implies(
                    emp_dept_id(t2_1) == dept_id(t2_1),  # JOIN condition
                    And([
                        # equalities of projected attributes in both table
                        emp_name(t2_1) == x6,
                        dept_name(t2_1) == v2,
                        # not(null([each attribute in the RIGHT table]))
                        Not(null(t2_1, attr_dept_name)),
                        Not(deleted(t2_1)),
                        joined(t2)
                    ])
                ),
                Implies(Not(emp_dept_id(t2_1) == dept_id(t2_1)), deleted(t2_1))
            ])
        ),
        Implies(Not(emp_age(t2_1) > 25), deleted(t2_1)),
        # Left 2 --concat--> Right 2
        Implies(
            emp_age(t2_2) > 25,  # WHERE condition
            And([
                Implies(
                    emp_dept_id(t2_2) == dept_id(t2_2),  # JOIN condition
                    And([
                        # equalities of projected attributes in both table
                        emp_name(t2_2) == x6,
                        dept_name(t2_2) == v4,
                        # not(null([each attribute in the RIGHT table]))
                        Not(null(t2_2, attr_dept_name)),
                        Not(deleted(t2_2)),
                        joined(t2)
                    ])
                ),
                Implies(Not(emp_dept_id(t2_2) == dept_id(t2_2)), deleted(t2_2))
            ])
        ),
        Implies(Not(emp_age(t2_2) > 25), deleted(t2_2)),

        # Base cases
        Implies(
            emp_age(t1_0) > 25,  # WHERE condition
            Implies(
                Not(joined(t1)),
                And([
                    # equalities of attributes in the LEFT table
                    emp_name(t1_0) == x2,
                    # null([each attribute in the RIGHT table]
                    null(t1_0, attr_dept_name),
                    Not(deleted(t1_0))
                ])
            )
        ),
        Implies(joined(t1), deleted(t1_0)),
        Implies(Not(emp_age(t1_0) > 25), deleted(t1_0)),

        Implies(
            emp_age(t2_0) > 25,  # WHERE condition
            Implies(
                Not(joined(t2)),
                And([
                    # equalities of attributes in the LEFT table
                    emp_name(t2_0) == x6,
                    # null([each attribute in the RIGHT table]
                    null(t2_0, attr_dept_name),
                    Not(deleted(t2_0))
                ])
            )
        ),
        Implies(joined(t2), deleted(t2_0)),
        Implies(Not(emp_age(t2_0) > 25), deleted(t2_0)),
    ])

    # SQL 2
    r2 = And([
        # Left 1 --concat--> Right 1
        Implies(
            emp_age(t3_1) > 25,  # WHERE condition
            And([
                Implies(
                    emp_dept_id(t3_1) == dept_id(t3_1),  # JOIN condition
                    And([
                        # equalities of projected attributes in both table
                        emp_name(t3_1) == x2,
                        dept_name(t3_1) == v2,
                        # not(null([each attribute in the RIGHT table]))
                        Not(null(t3_1, attr_dept_name)),
                        Not(deleted(t3_1)),
                        joined(t3)
                    ])
                ),
                Implies(Not(emp_dept_id(t3_1) == dept_id(t3_1)), deleted(t3_1)),
            ])
        ),
        Implies(Not(emp_age(t3_1) > 25), deleted(t3_1)),
        # Left 1 --concat--> Right 2
        Implies(
            emp_age(t3_2) > 25,  # WHERE condition
            And([
                Implies(
                    emp_dept_id(t3_2) == dept_id(t3_2),  # JOIN condition
                    And([
                        # equalities of projected attributes in both table
                        emp_name(t3_2) == x2,
                        dept_name(t3_2) == v4,
                        # not(null([each attribute in the RIGHT table]))
                        Not(null(t3_2, attr_dept_name)),
                        Not(deleted(t3_2)),
                        joined(t3)
                    ])
                ),
                Implies(Not(emp_dept_id(t3_2) == dept_id(t3_2)), deleted(t3_2))
            ])
        ),
        Implies(Not(emp_age(t3_2) > 25), deleted(t3_2)),
        # Left 2 --concat--> Right 1
        Implies(
            emp_age(t4_1) > 25,  # WHERE condition
            And([
                Implies(
                    emp_dept_id(t4_1) == dept_id(t4_1),  # JOIN condition
                    And([
                        # equalities of projected attributes in both table
                        emp_name(t4_1) == x6,
                        dept_name(t4_1) == v2,
                        # not(null([each attribute in the RIGHT table]))
                        Not(null(t4_1, attr_dept_name)),
                        Not(deleted(t4_1)),
                        joined(t4)
                    ])
                ),
                Implies(Not(emp_dept_id(t4_1) == dept_id(t4_1)), deleted(t4_1))
            ])
        ),
        Implies(Not(emp_age(t4_1) > 25), deleted(t4_1)),
        # Left 2 --concat--> Right 2
        Implies(
            emp_age(t4_2) > 25,  # WHERE condition
            And([
                Implies(
                    emp_dept_id(t4_2) == dept_id(t4_2),  # JOIN condition
                    And([
                        # equalities of projected attributes in both table
                        emp_name(t4_2) == x6,
                        dept_name(t4_2) == v4,
                        # not(null([each attribute in the RIGHT table]))
                        Not(null(t4_2, attr_dept_name)),
                        Not(deleted(t4_2)),
                        joined(t4)
                    ])
                ),
                Implies(Not(emp_dept_id(t4_2) == dept_id(t4_2)), deleted(t4_2))
            ])
        ),
        Implies(Not(emp_age(t4_2) > 25), deleted(t4_2)),

        # Base cases
        Implies(
            emp_age(t3_0) > 25,  # WHERE condition
            Implies(
                Not(joined(t3)),
                And([
                    # equalities of attributes in the LEFT table
                    emp_name(t3_0) == x2,
                    # null([each attribute in the RIGHT table]
                    null(t3_0, attr_dept_name),
                    Not(deleted(t3_0))
                ])
            )
        ),
        Implies(joined(t3), deleted(t3_0)),
        Implies(Not(emp_age(t3_0) > 25), deleted(t3_0)),
        Implies(
            emp_age(t4_0) > 25,  # WHERE condition
            Implies(
                Not(joined(t4)),
                And([
                    # equalities of attributes in the LEFT table
                    emp_name(t4_0) == x6,
                    # null([each attribute in the RIGHT table]
                    null(t4_0, attr_dept_name),
                    Not(deleted(t4_0))
                ])
            )
        ),
        Implies(joined(t4), deleted(t4_0)),
        Implies(Not(emp_age(t4_0) > 25), deleted(t4_0)),
    ])

    s.add(Not(Implies(
        And([
            emp_age(t1_1) == x3,
            emp_age(t1_2) == x3,
            emp_age(t2_1) == x7,
            emp_age(t2_2) == x7,
            emp_age(t1_0) == x3,
            emp_age(t2_0) == x7,

            emp_age(t3_1) == x3,
            emp_age(t3_2) == x3,
            emp_age(t4_1) == x7,
            emp_age(t4_2) == x7,
            emp_age(t3_0) == x3,
            emp_age(t4_0) == x7,
            r1, r2
        ]),
        And([
            deleted(t1_1) == deleted(t3_1),
            deleted(t1_2) == deleted(t3_2),
            deleted(t2_1) == deleted(t4_1),
            deleted(t2_2) == deleted(t4_2),
            deleted(t1_0) == deleted(t3_0),
            deleted(t2_0) == deleted(t4_0),
            Implies(
                Not(deleted(t1_1)),
                And([
                    Implies(
                        And([
                            emp_dept_id(t1_1) == emp_dept_id(t3_1),
                            dept_id(t1_1) == dept_id(t3_1)
                        ]),
                        Implies(
                            joined(t1) == joined(t3),
                            And([
                                null(t1_1, attr_dept_name) == null(t3_1, attr_dept_name),
                                Implies(
                                    Not(null(t1_1, attr_dept_name)),
                                    dept_name(t1_1) == dept_name(t3_1)
                                )
                            ])
                        )
                    ),
                    emp_name(t1_1) == emp_name(t3_1)
                ])
            ),
            Implies(
                Not(deleted(t1_2)),
                And([
                    Implies(
                        And([
                            emp_dept_id(t1_2) == emp_dept_id(t3_2),
                            dept_id(t1_2) == dept_id(t3_2)
                        ]),
                        Implies(
                            joined(t1) == joined(t3),
                            And([
                                null(t1_2, attr_dept_name) == null(t3_2, attr_dept_name),
                                Implies(
                                    Not(null(t1_2, attr_dept_name)),
                                    dept_name(t1_2) == dept_name(t3_2)
                                )
                            ])
                        )
                    ),
                    emp_name(t1_2) == emp_name(t3_2)
                ])
            ),
            Implies(
                Not(deleted(t2_1)),
                And([
                    Implies(
                        And([
                            emp_dept_id(t2_1) == emp_dept_id(t4_1),
                            dept_id(t2_1) == dept_id(t4_1)
                        ]),
                        Implies(
                            joined(t2) == joined(t4),
                            And([
                                null(t2_1, attr_dept_name) == null(t4_1, attr_dept_name),
                                Implies(
                                    Not(null(t2_1, attr_dept_name)),
                                    dept_name(t2_1) == dept_name(t4_1)
                                )
                            ])
                        )
                    ),
                    emp_name(t2_1) == emp_name(t4_1)
                ])
            ),
            Implies(
                Not(deleted(t2_2)),
                And([
                    Implies(
                        And([
                            emp_dept_id(t2_2) == emp_dept_id(t4_2),
                            dept_id(t2_2) == dept_id(t4_2)
                        ]),
                        Implies(
                            joined(t2) == joined(t4),
                            And([
                                null(t2_2, attr_dept_name) == null(t4_2, attr_dept_name),
                                Implies(
                                    Not(null(t2_2, attr_dept_name)),
                                    dept_name(t2_2) == dept_name(t4_2)
                                )
                            ])
                        )
                    ),
                    emp_name(t2_2) == emp_name(t4_2)
                ])
            ),
            Implies(
                Not(deleted(t1_0)),
                And([
                    Implies(
                        And([
                            emp_dept_id(t1_0) == emp_dept_id(t3_0),
                            dept_id(t1_0) == dept_id(t3_0)
                        ]),
                        And([
                            null(t1_0, attr_dept_name),
                            null(t3_0, attr_dept_name)
                        ])
                    ),
                    emp_name(t1_0) == emp_name(t3_0)
                ])
            ),
            Implies(
                Not(deleted(t2_0)),
                And([
                    Implies(
                        And([
                            emp_dept_id(t2_0) == emp_dept_id(t4_0),
                            dept_id(t2_0) == dept_id(t4_0)
                        ]),
                        And([
                            null(t2_0, attr_dept_name),
                            null(t4_0, attr_dept_name)
                        ])
                    ),
                    emp_name(t2_0) == emp_name(t4_0)
                ])
            ),
        ])
    )))
    print(s.check())
    if s.check() == sat:
        print(s.model())


def debug():
    T = DeclareSort('T')
    deleted = Function('deleted', T, BoolSort())
    null = Function('null', T, StringSort(), BoolSort())

    emp_name = Function('EMP.name', T, IntSort())
    emp_age = Function('EMP.age', T, IntSort())
    emp_dept_id = Function('EMP.dept_id', T, IntSort())
    dept_id = Function('DEPT.id', T, IntSort())
    dept_name = Function('DEPT.name', T, IntSort())

    attr_dept_name = Const('DEPT.name', StringSort())

    t1_0 = Const('t1_0', T)  # base case for t1
    t1_1 = Const('t1_1', T)  # t1 join first tuple in DEPT
    t1_2 = Const('t1_2', T)  # t1 join second tuple in DEPT

    t3_0 = Const('t3_0', T)
    t3_1 = Const('t3_1', T)
    t3_2 = Const('t3_2', T)

    # suppose we only project EMP.name (from the left table) and DEPT.name (from the right table) for simplicity

    x2 = Const('x2', IntSort())
    v2 = Const('v2', IntSort())
    v4 = Const('v4', IntSort())

    s = Solver()

    # SQL 1
    r1 = And([
        # Left 1 --concat--> Right 1
        Implies(
            emp_age(t1_1) > 25,  # WHERE condition
            And([
                Implies(
                    emp_dept_id(t1_1) == dept_id(t1_1),  # JOIN condition
                    And([
                        # equalities of projected attributes in both table
                        emp_name(t1_1) == x2,
                        dept_name(t1_1) == v2,
                        # not(null([each attribute in the RIGHT table]))
                        Not(null(t1_1, attr_dept_name)),
                        Not(deleted(t1_1)),
                        deleted(t1_0)
                    ])
                ),
                Implies(Not(emp_dept_id(t1_1) == dept_id(t1_1)), deleted(t1_1)),
            ])
        ),
        Implies(Not(emp_age(t1_1) > 25), deleted(t1_1)),
        # Left 1 --concat--> Right 2
        Implies(
            emp_age(t1_2) > 25,  # WHERE condition
            And([
                Implies(
                    emp_dept_id(t1_2) == dept_id(t1_2),  # JOIN condition
                    And([
                        # equalities of projected attributes in both table
                        emp_name(t1_2) == x2,
                        dept_name(t1_2) == v4,
                        # not(null([each attribute in the RIGHT table]))
                        Not(null(t1_2, attr_dept_name)),
                        Not(deleted(t1_2)),
                        deleted(t1_0)
                    ])
                ),
                Implies(Not(emp_dept_id(t1_2) == dept_id(t1_2)), deleted(t1_2))
            ])
        ),
        Implies(Not(emp_age(t1_2) > 25), deleted(t1_2)),

        # Implies(
        #     And([
        #         Or([
        #             emp_age(t1_1) > 25,
        #             emp_age(t1_2) > 25,
        #             emp_age(t1_0) > 25,
        #         ]),
        #         And([
        #             Not(emp_dept_id(t1_1) == dept_id(t1_1)),
        #             Not(emp_dept_id(t1_2) == dept_id(t1_2))
        #         ])
        #     ]),
        #     Not(deleted(t1_0))
        # ),

        # Base cases
        Implies(
            And([
                emp_age(t1_0) > 25,  # WHERE condition
                And([
                    Not(emp_dept_id(t1_1) == dept_id(t1_1)),
                    Not(emp_dept_id(t1_2) == dept_id(t1_2))
                ])
            ]),
            And([
                # equalities of attributes in the LEFT table
                emp_name(t1_0) == x2,
                # null([each attribute in the RIGHT table]
                null(t1_0, attr_dept_name),
                Not(deleted(t1_0))
            ])
        ),
        Implies(Not(emp_age(t1_0) > 25), deleted(t1_0)),
    ])

    # SQL 2
    r2 = And([
        # Left 1 --concat--> Right 1
        Implies(
            emp_age(t3_1) > 25,  # WHERE condition
            And([
                Implies(
                    emp_dept_id(t3_1) == dept_id(t3_1),  # JOIN condition
                    And([
                        # equalities of projected attributes in both table
                        emp_name(t3_1) == x2,
                        dept_name(t3_1) == v2,
                        # not(null([each attribute in the RIGHT table]))
                        Not(null(t3_1, attr_dept_name)),
                        Not(deleted(t3_1)),
                        deleted(t3_0)
                    ])
                ),
                Implies(Not(emp_dept_id(t3_1) == dept_id(t3_1)), deleted(t3_1)),
            ])
        ),
        Implies(Not(emp_age(t3_1) > 25), deleted(t3_1)),
        # Left 1 --concat--> Right 2
        Implies(
            emp_age(t3_2) > 25,  # WHERE condition
            And([
                Implies(
                    emp_dept_id(t3_2) == dept_id(t3_2),  # JOIN condition
                    And([
                        # equalities of projected attributes in both table
                        emp_name(t3_2) == x2,
                        dept_name(t3_2) == v4,
                        # not(null([each attribute in the RIGHT table]))
                        Not(null(t3_2, attr_dept_name)),
                        Not(deleted(t3_2)),
                        deleted(t3_0)
                    ])
                ),
                Implies(Not(emp_dept_id(t3_2) == dept_id(t3_2)), deleted(t3_2))
            ])
        ),
        Implies(Not(emp_age(t3_2) > 25), deleted(t3_2)),

        # Implies(
        #     And([
        #         Or([
        #             emp_age(t3_1) > 25,
        #             emp_age(t3_2) > 25,
        #             emp_age(t3_0) > 25,
        #         ]),
        #         And([
        #             Not(emp_dept_id(t3_1) == dept_id(t3_1)),
        #             Not(emp_dept_id(t3_2) == dept_id(t3_2))
        #         ])
        #     ]),
        #     Not(deleted(t3_0))
        # ),

        # Base cases
        Implies(
            And([
                emp_age(t3_0) > 25,  # WHERE condition
                And([
                    Not(emp_dept_id(t3_1) == dept_id(t3_1)),
                    Not(emp_dept_id(t3_2) == dept_id(t3_2))
                ])
            ]),
            And([
                # equalities of attributes in the LEFT table
                emp_name(t3_0) == x2,
                # null([each attribute in the RIGHT table]
                null(t3_0, attr_dept_name),
                Not(deleted(t3_0))
            ])
        ),
        Implies(Not(emp_age(t3_0) > 25), deleted(t3_0)),
    ])

    s.add(Not(Implies(
        And([
            # equalities of WHERE condition
            emp_age(t1_1) == emp_age(t3_1),
            emp_age(t3_1) == emp_age(t1_2),
            emp_age(t1_2) == emp_age(t3_2),
            emp_age(t3_2) == emp_age(t1_0),
            emp_age(t1_0) == emp_age(t3_0),
            # emp_age(t1_2) == emp_age(t3_2),
            # emp_age(t1_0) == emp_age(t3_0),

            # equalities of JOIN condition
            emp_dept_id(t1_1) == emp_dept_id(t3_1),
            emp_dept_id(t3_1) == emp_dept_id(t1_2),
            emp_dept_id(t1_2) == emp_dept_id(t3_2),
            emp_dept_id(t3_2) == emp_dept_id(t1_0),
            emp_dept_id(t1_0) == emp_dept_id(t3_0),

            dept_id(t1_1) == dept_id(t3_1),
            dept_id(t3_1) == dept_id(t1_2),
            dept_id(t1_2) == dept_id(t3_2),
            dept_id(t3_2) == dept_id(t1_0),
            dept_id(t1_0) == dept_id(t3_0),
            # emp_dept_id(t1_2) == emp_dept_id(t3_2),
            # dept_id(t1_2) == dept_id(t3_2),
            # emp_dept_id(t1_0) == emp_dept_id(t3_0),
            # dept_id(t1_0) == dept_id(t3_0),
            r1, r2
        ]),
        And([
            deleted(t1_1) == deleted(t3_1),
            deleted(t1_2) == deleted(t3_2),
            deleted(t1_0) == deleted(t3_0),
            Implies(
                Not(deleted(t1_1)),
                And([
                    emp_name(t1_1) == emp_name(t3_1),
                    null(t1_1, attr_dept_name) == null(t3_1, attr_dept_name),
                    Implies(
                        Not(null(t1_1, attr_dept_name)),
                        dept_name(t1_1) == dept_name(t3_1)
                    )
                ])
            ),
            Implies(
                Not(deleted(t1_2)),
                And([
                    emp_name(t1_2) == emp_name(t3_2),
                    null(t1_2, attr_dept_name) == null(t3_2, attr_dept_name),
                    Implies(
                        Not(null(t1_2, attr_dept_name)),
                        dept_name(t1_2) == dept_name(t3_2)
                    )
                ])
            ),
            Implies(
                Not(deleted(t1_0)),
                And([
                    emp_name(t1_0) == emp_name(t3_0),
                    null(t1_0, attr_dept_name) == null(t3_0, attr_dept_name),
                    Implies(
                        Not(null(t1_0, attr_dept_name)),
                        dept_name(t1_0) == dept_name(t3_0)
                    )
                ])
            ),
        ])
    )))
    print(s.check())
    if s.check() == sat:
        print(s.model())


def debug2():
    T = DeclareSort('T')
    deleted = Function('deleted', T, BoolSort())
    null = Function('null', T, StringSort(), BoolSort())

    emp_name = Function('EMP.name', T, IntSort())
    emp_age = Function('EMP.age', T, IntSort())
    emp_dept_id = Function('EMP.dept_id', T, IntSort())
    dept_id = Function('DEPT.id', T, IntSort())
    dept_name = Function('DEPT.name', T, IntSort())

    attr_dept_name = Const('DEPT.name', StringSort())
    attr_emp_name = Const('EMP.name', StringSort())
    attr_emp_age = Const('EMP.age', StringSort())
    attr_emp_dept_id = Const('EMP.dept_id', StringSort())
    attr_dept_id = Const('DEPT.id', StringSort())

    t1_0 = Const('t1_0', T)  # base case for t1
    t1_1 = Const('t1_1', T)  # t1 join first tuple in DEPT
    t1_2 = Const('t1_2', T)  # t1 join second tuple in DEPT

    t3_0 = Const('t3_0', T)
    t3_1 = Const('t3_1', T)
    t3_2 = Const('t3_2', T)

    # suppose we only project EMP.name (from the left table) and DEPT.name (from the right table) for simplicity

    x2 = Const('x2', IntSort())
    x3 = Const('x3', IntSort())
    x4 = Const('x4', IntSort())
    v1 = Const('v1', IntSort())
    v2 = Const('v2', IntSort())
    v3 = Const('v3', IntSort())
    v4 = Const('v4', IntSort())

    s = Solver()

    # load all symbolic tuples' values (can load columns ad hoc or load just all columns) as the premise
    tuple_values = And([
        emp_name(t1_1) == x2, emp_age(t1_1) == x3, emp_dept_id(t1_1) == x4,
        dept_name(t1_1) == v2, dept_id(t1_1) == v1,

        emp_name(t1_2) == x2, emp_age(t1_2) == x3, emp_dept_id(t1_2) == x4,
        dept_name(t1_2) == v4, dept_id(t1_2) == v3,

        emp_name(t1_0) == x2, emp_age(t1_0) == x3, emp_dept_id(t1_0) == x4,

        emp_name(t3_1) == x2, emp_age(t3_1) == x3, emp_dept_id(t3_1) == x4,
        dept_name(t3_1) == v2, dept_id(t3_1) == v1,

        emp_name(t3_2) == x2, emp_age(t3_2) == x3, emp_dept_id(t3_2) == x4,
        dept_name(t3_2) == v4, dept_id(t3_2) == v3,

        emp_name(t3_0) == x2, emp_age(t3_0) == x3, emp_dept_id(t3_0) == x4,
    ])

    tuple_null_facts = And([
        Not(null(t1_1, attr_emp_name)), Not(null(t1_1, attr_emp_age)), Not(null(t1_1, attr_emp_dept_id)),
        Not(null(t1_1, attr_dept_name)), Not(null(t1_1, attr_dept_id)),

        Not(null(t1_2, attr_emp_name)), Not(null(t1_2, attr_emp_age)), Not(null(t1_2, attr_emp_dept_id)),
        Not(null(t1_2, attr_dept_name)), Not(null(t1_2, attr_dept_id)),

        Not(null(t1_0, attr_emp_name)), Not(null(t1_0, attr_emp_age)),
        null(t1_0, attr_dept_name), null(t1_0, attr_dept_id),

        Not(null(t3_1, attr_emp_name)), Not(null(t3_1, attr_emp_age)), Not(null(t3_1, attr_emp_dept_id)),
        Not(null(t3_1, attr_dept_name)), Not(null(t3_1, attr_dept_id)),

        Not(null(t3_2, attr_emp_name)), Not(null(t3_2, attr_emp_age)), Not(null(t3_2, attr_emp_dept_id)),
        Not(null(t3_2, attr_dept_name)), Not(null(t3_2, attr_dept_id)),

        Not(null(t3_0, attr_emp_name)), Not(null(t3_0, attr_emp_age)),
        null(t3_0, attr_dept_name), null(t3_0, attr_dept_id),
    ])

    # SQL 1
    r1 = And([
        # Left 1 --concat--> Right 1
        Implies(
            And([
                emp_age(t1_1) > 25,  # WHERE condition
                Not(null(t1_1, attr_emp_age))
            ]),
            And([
                Implies(
                    And([
                        emp_dept_id(t1_1) == dept_id(t1_1),  # JOIN condition
                        Not(null(t1_1, attr_emp_dept_id)),
                        Not(null(t1_1, attr_dept_id))
                    ]),
                    And([
                        Not(deleted(t1_1)),
                        deleted(t1_0)
                    ])
                ),
                Implies(Not(emp_dept_id(t1_1) == dept_id(t1_1)), deleted(t1_1)),
            ])
        ),
        Implies(Not(And([emp_age(t1_1) > 25, Not(null(t1_1, attr_emp_age))])), deleted(t1_1)),

        # Left 1 --concat--> Right 2
        Implies(
            And([
                emp_age(t1_2) > 25,  # WHERE condition
                Not(null(t1_2, attr_emp_age))
            ]),
            And([
                Implies(
                    And([
                        emp_dept_id(t1_2) == dept_id(t1_2),  # JOIN condition
                        Not(null(t1_2, attr_emp_dept_id)),
                        Not(null(t1_2, attr_dept_id))
                    ]),
                    And([
                        Not(deleted(t1_2)),
                        deleted(t1_0)
                    ])
                ),
                Implies(Not(emp_dept_id(t1_2) == dept_id(t1_2)), deleted(t1_2))
            ])
        ),
        Implies(Not(And([emp_age(t1_2) > 25, Not(null(t1_2, attr_emp_age))])), deleted(t1_2)),

        # Base cases
        Implies(
            And([
                And([
                    emp_age(t1_0) > 25,  # WHERE condition
                    Not(null(t1_0, attr_emp_age))
                ]),
                And([
                    deleted(t1_1),
                    deleted(t1_2),
                ])
            ]),
            Not(deleted(t1_0))
        ),
        Implies(Not(And([emp_age(t1_0) > 25, Not(null(t1_0, attr_emp_age))])), deleted(t1_0)),
    ])

    # SQL 2
    r2 = And([
        # Left 1 --concat--> Right 1
        Implies(
            And([
                emp_age(t3_1) > 25,  # WHERE condition
                Not(null(t3_1, attr_emp_age))
            ]),
            And([
                Implies(
                    And([
                        emp_dept_id(t3_1) == dept_id(t3_1),  # JOIN condition
                        Not(null(t3_1, attr_emp_dept_id)),
                        Not(null(t3_1, attr_dept_id))
                    ]),
                    And([
                        Not(deleted(t3_1)),
                        deleted(t3_0)
                    ])
                ),
                Implies(Not(emp_dept_id(t3_1) == dept_id(t3_1)), deleted(t3_1)),
            ])
        ),
        Implies(Not(And([emp_age(t3_1) > 25, Not(null(t3_1, attr_emp_age))])), deleted(t3_1)),
        # Left 1 --concat--> Right 2
        Implies(
            And([
                emp_age(t3_2) > 25,  # WHERE condition
                Not(null(t3_2, attr_emp_age))
            ]),
            And([
                Implies(
                    And([
                        emp_dept_id(t3_2) == dept_id(t3_2),  # JOIN condition
                        Not(null(t3_2, attr_emp_dept_id)),
                        Not(null(t3_2, attr_dept_id))
                    ]),
                    And([
                        Not(deleted(t3_2)),
                        deleted(t3_0)
                    ])
                ),
                Implies(Not(emp_dept_id(t3_2) == dept_id(t3_2)), deleted(t3_2))
            ])
        ),
        Implies(Not(And([emp_age(t3_2) > 25, Not(null(t3_2, attr_emp_age))])), deleted(t3_2)),

        # Base cases
        Implies(
            And([
                And([
                    emp_age(t3_0) > 25,  # WHERE condition
                    Not(null(t3_0, attr_emp_age))
                ]),
                And([
                    deleted(t3_1),
                    deleted(t3_2)
                ])
            ]),
            Not(deleted(t3_0))
        ),
        Implies(Not(And([emp_age(t3_0) > 25, Not(null(t3_0, attr_emp_age))])), deleted(t3_0)),
    ])

    s.add(Not(Implies(
        And([
            # don't need to add equalities of where and join conditions here anymore

            tuple_values,
            tuple_null_facts,
            r1, r2
        ]),
        And([
            deleted(t1_1) == deleted(t3_1),
            deleted(t1_2) == deleted(t3_2),
            deleted(t1_0) == deleted(t3_0),
            Implies(
                Not(deleted(t1_1)),
                And([
                    # if not deleted, first check if null is ==
                    # if not null, check equality of the column
                    null(t1_1, attr_emp_name) == null(t3_1, attr_emp_name),
                    Implies(
                        Not(null(t1_1, attr_emp_name)),
                        emp_name(t1_1) == emp_name(t3_1),
                    ),
                    null(t1_1, attr_dept_name) == null(t3_1, attr_dept_name),
                    Implies(
                        Not(null(t1_1, attr_dept_name)),
                        dept_name(t1_1) == dept_name(t3_1)
                    )
                ])
            ),
            Implies(
                Not(deleted(t1_2)),
                And([
                    null(t1_2, attr_emp_name) == null(t3_2, attr_emp_name),
                    Implies(
                        Not(null(t1_2, attr_emp_name)),
                        emp_name(t1_2) == emp_name(t3_2),
                    ),
                    null(t1_2, attr_dept_name) == null(t3_2, attr_dept_name),
                    Implies(
                        Not(null(t1_2, attr_dept_name)),
                        dept_name(t1_2) == dept_name(t3_2)
                    )
                ])
            ),
            Implies(
                Not(deleted(t1_0)),
                And([
                    null(t1_0, attr_emp_name) == null(t3_0, attr_emp_name),
                    Implies(
                        Not(null(t1_0, attr_emp_name)),
                        emp_name(t1_0) == emp_name(t3_0),
                    ),
                    null(t1_0, attr_dept_name) == null(t3_0, attr_dept_name),
                    Implies(
                        Not(null(t1_0, attr_dept_name)),
                        dept_name(t1_0) == dept_name(t3_0)
                    )
                ])
            ),
        ])
    )))
    print(s.check())
    if s.check() == sat:
        print(s.model())


if __name__ == '__main__':
    debug2()
