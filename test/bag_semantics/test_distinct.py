# -*- coding:utf-8 -*-
import itertools

from z3 import *

# SELECT DISTINCT age, dept_id FROM EMP WHERE age > 25
# SELECT DISTINCT age, dept_id FROM EMP WHERE NOT age <= 25

# define z3 Sorts
__TupleSort = DeclareSort("TupleSort")  # define `Tuple` sort
__Int = IntSort()  # define `Int` sort
__String = StringSort()  # define `String` sort
__Boolean = BoolSort()  # define `Boolean` sort

# Special functions
DELETED = Function("DELETED", __TupleSort,
                   __Boolean)  # define `DELETE` function to represent a tuple does not exist; Not(DELETE) means the existence of a tuple
NULL = Function("NULL", __TupleSort, __String, __Boolean)  # define `NULL` function
EMP_id = Function('EMP_id', __TupleSort, __Int)  # define `EMP_id` function to retrieve columns of tuples
EMP_name = Function('EMP_name', __TupleSort, __Int)  # define `EMP_name` function to retrieve columns of tuples
EMP_age = Function('EMP_age', __TupleSort, __Int)  # define `EMP_age` function to retrieve columns of tuples
EMP_dept_id = Function('EMP_dept_id', __TupleSort, __Int)  # define `EMP_dept_id` function to retrieve columns of tuples
DEPT_id = Function('DEPT_id', __TupleSort, __Int)  # define `DEPT_id` function to retrieve columns of tuples
DEPT_name = Function('DEPT_name', __TupleSort, __Int)  # define `DEPT_name` function to retrieve columns of tuples

EMP_id__String = Const('EMP_id', __String)  # define `EMP_id__String` for NULL function
Upper_Bound_EMP_id__Int = Const(f"Upper_Bound_EMP_id__Int", __Int)  # Upper bound of EMP_id
Lower_Bound_EMP_id__Int = Const(f"Lower_Bound_EMP_id__Int", __Int)  # Lower bound of EMP_id
MAX_EMP_id__String = Const(f"MAX_EMP_id__String", __String)  # define `MAX` variable of EMP_id
MIN_EMP_id__String = Const(f"MIN_EMP_id__String", __String)  # define `MIN` variable of EMP_id
COUNT_EMP_id__String = Const(f"COUNT_EMP_id__String", __String)  # define `COUNT` variable of EMP_id
COUNT_ALL__String = Const(f"COUNT_ALL__String", __String)  # define `COUNT(*)` variable of EMP_id
AVG_EMP_id__String = Const(f"AVG_String", __String)  # define `AVG` variable of EMP_id
SUM_EMP_id__String = Const(f"SUM_String", __String)  # define `SUM` variable of EMP_id
x1__Int = Const('x1', __Int)  # define `x1__Int` for NULL function
EMP_name__String = Const('EMP_name', __String)  # define `EMP_name__String` for NULL function
Upper_Bound_EMP_name__Int = Const(f"Upper_Bound_EMP_name__Int", __Int)  # Upper bound of EMP_name
Lower_Bound_EMP_name__Int = Const(f"Lower_Bound_EMP_name__Int", __Int)  # Lower bound of EMP_name
MAX_EMP_name__String = Const(f"MAX_EMP_name__String", __String)  # define `MAX` variable of EMP_name
MIN_EMP_name__String = Const(f"MIN_EMP_name__String", __String)  # define `MIN` variable of EMP_name
COUNT_EMP_name__String = Const(f"COUNT_EMP_name__String", __String)  # define `COUNT` variable of EMP_name
AVG_EMP_name__String = Const(f"AVG_String", __String)  # define `AVG` variable of EMP_name
SUM_EMP_name__String = Const(f"SUM_String", __String)  # define `SUM` variable of EMP_name
x2__Int = Const('x2', __Int)  # define `x2__Int` for NULL function
EMP_age__String = Const('EMP_age', __String)  # define `EMP_age__String` for NULL function
Upper_Bound_EMP_age__Int = Const(f"Upper_Bound_EMP_age__Int", __Int)  # Upper bound of EMP_age
Lower_Bound_EMP_age__Int = Const(f"Lower_Bound_EMP_age__Int", __Int)  # Lower bound of EMP_age
MAX_EMP_age__String = Const(f"MAX_EMP_age__String", __String)  # define `MAX` variable of EMP_age
MIN_EMP_age__String = Const(f"MIN_EMP_age__String", __String)  # define `MIN` variable of EMP_age
COUNT_EMP_age__String = Const(f"COUNT_EMP_age__String", __String)  # define `COUNT` variable of EMP_age
AVG_EMP_age__String = Const(f"AVG_String", __String)  # define `AVG` variable of EMP_age
SUM_EMP_age__String = Const(f"SUM_String", __String)  # define `SUM` variable of EMP_age
x3__Int = Const('x3', __Int)  # define `x3__Int` for NULL function
EMP_dept_id__String = Const('EMP_dept_id', __String)  # define `EMP_dept_id__String` for NULL function
Upper_Bound_EMP_dept_id__Int = Const(f"Upper_Bound_EMP_dept_id__Int", __Int)  # Upper bound of EMP_dept_id
Lower_Bound_EMP_dept_id__Int = Const(f"Lower_Bound_EMP_dept_id__Int", __Int)  # Lower bound of EMP_dept_id
MAX_EMP_dept_id__String = Const(f"MAX_EMP_dept_id__String", __String)  # define `MAX` variable of EMP_dept_id
MIN_EMP_dept_id__String = Const(f"MIN_EMP_dept_id__String", __String)  # define `MIN` variable of EMP_dept_id
COUNT_EMP_dept_id__String = Const(f"COUNT_EMP_dept_id__String", __String)  # define `COUNT` variable of EMP_dept_id
AVG_EMP_dept_id__String = Const(f"AVG_String", __String)  # define `AVG` variable of EMP_dept_id
SUM_EMP_dept_id__String = Const(f"SUM_String", __String)  # define `SUM` variable of EMP_dept_id
x4__Int = Const('x4', __Int)  # define `x4__Int` for NULL function
t1 = Const('t1', __TupleSort)  # define a tuple `t1`
x5__Int = Const('x5', __Int)  # define `x5__Int` for NULL function
x6__Int = Const('x6', __Int)  # define `x6__Int` for NULL function
x7__Int = Const('x7', __Int)  # define `x7__Int` for NULL function
x8__Int = Const('x8', __Int)  # define `x8__Int` for NULL function
t2 = Const('t2', __TupleSort)  # define a tuple `t2`
x9__Int = Const('x9', __Int)  # define `x9__Int` for NULL function
x10__Int = Const('x10', __Int)  # define `x10__Int` for NULL function
x11__Int = Const('x11', __Int)  # define `x11__Int` for NULL function
x12__Int = Const('x12', __Int)  # define `x12__Int` for NULL function
t3 = Const('t3', __TupleSort)  # define a tuple `t3`
DEPT_id__String = Const('DEPT_id', __String)  # define `DEPT_id__String` for NULL function
Upper_Bound_DEPT_id__Int = Const(f"Upper_Bound_DEPT_id__Int", __Int)  # Upper bound of DEPT_id
Lower_Bound_DEPT_id__Int = Const(f"Lower_Bound_DEPT_id__Int", __Int)  # Lower bound of DEPT_id
MAX_DEPT_id__String = Const(f"MAX_DEPT_id__String", __String)  # define `MAX` variable of DEPT_id
MIN_DEPT_id__String = Const(f"MIN_DEPT_id__String", __String)  # define `MIN` variable of DEPT_id
COUNT_DEPT_id__String = Const(f"COUNT_DEPT_id__String", __String)  # define `COUNT` variable of DEPT_id
AVG_DEPT_id__String = Const(f"AVG_String", __String)  # define `AVG` variable of DEPT_id
SUM_DEPT_id__String = Const(f"SUM_String", __String)  # define `SUM` variable of DEPT_id
v1__Int = Const('v1', __Int)  # define `v1__Int` for NULL function
DEPT_name__String = Const('DEPT_name', __String)  # define `DEPT_name__String` for NULL function
Upper_Bound_DEPT_name__Int = Const(f"Upper_Bound_DEPT_name__Int", __Int)  # Upper bound of DEPT_name
Lower_Bound_DEPT_name__Int = Const(f"Lower_Bound_DEPT_name__Int", __Int)  # Lower bound of DEPT_name
MAX_DEPT_name__String = Const(f"MAX_DEPT_name__String", __String)  # define `MAX` variable of DEPT_name
MIN_DEPT_name__String = Const(f"MIN_DEPT_name__String", __String)  # define `MIN` variable of DEPT_name
COUNT_DEPT_name__String = Const(f"COUNT_DEPT_name__String", __String)  # define `COUNT` variable of DEPT_name
AVG_DEPT_name__String = Const(f"AVG_String", __String)  # define `AVG` variable of DEPT_name
SUM_DEPT_name__String = Const(f"SUM_String", __String)  # define `SUM` variable of DEPT_name
v2__Int = Const('v2', __Int)  # define `v2__Int` for NULL function
t4 = Const('t4', __TupleSort)  # define a tuple `t4`
v3__Int = Const('v3', __Int)  # define `v3__Int` for NULL function
v4__Int = Const('v4', __Int)  # define `v4__Int` for NULL function
t5 = Const('t5', __TupleSort)  # define a tuple `t5`
t6 = Const('t6', __TupleSort)  # define a tuple `t6`
t7 = Const('t7', __TupleSort)  # define a tuple `t7`
t8 = Const('t8', __TupleSort)  # define a tuple `t8`
t9 = Const('t9', __TupleSort)  # define a tuple `t9`
t10 = Const('t10', __TupleSort)  # define a tuple `t10`
t11 = Const('t11', __TupleSort)  # define a tuple `t11`
t12 = Const('t12', __TupleSort)  # define a tuple `t12`
t13 = Const('t13', __TupleSort)  # define a tuple `t13`
t14 = Const('t14', __TupleSort)  # define a tuple `t14`
t15 = Const('t15', __TupleSort)  # define a tuple `t15`
t16 = Const('t16', __TupleSort)  # define a tuple `t16`
t17 = Const('t17', __TupleSort)  # define a tuple `t17`


def _MAX(*args):
    return functools.reduce(lambda x, y: If(x >= y, x, y), args)


def _MIN(*args):
    return functools.reduce(lambda x, y: If(x < y, x, y), args)


DBMS_facts = And(
    # Database tuples
    Not(DELETED(t1)),
    EMP_id(t1) == x1__Int,
    Not(NULL(t1, EMP_id__String)),
    EMP_name(t1) == x2__Int,
    Not(NULL(t1, EMP_name__String)),
    EMP_age(t1) == x3__Int,
    Not(NULL(t1, EMP_age__String)),
    EMP_dept_id(t1) == x4__Int,
    Not(NULL(t1, EMP_dept_id__String)),
    Not(DELETED(t2)),
    EMP_id(t2) == x5__Int,
    Not(NULL(t2, EMP_id__String)),
    EMP_name(t2) == x6__Int,
    Not(NULL(t2, EMP_name__String)),
    EMP_age(t2) == x7__Int,
    Not(NULL(t2, EMP_age__String)),
    EMP_dept_id(t2) == x8__Int,
    Not(NULL(t2, EMP_dept_id__String)),
    Not(DELETED(t3)),
    EMP_id(t3) == x9__Int,
    Not(NULL(t3, EMP_id__String)),
    EMP_name(t3) == x10__Int,
    Not(NULL(t3, EMP_name__String)),
    EMP_age(t3) == x11__Int,
    Not(NULL(t3, EMP_age__String)),
    EMP_dept_id(t3) == x12__Int,
    Not(NULL(t3, EMP_dept_id__String)),
    Not(DELETED(t4)),
    DEPT_id(t4) == v1__Int,
    Not(NULL(t4, DEPT_id__String)),
    DEPT_name(t4) == v2__Int,
    Not(NULL(t4, DEPT_name__String)),
    Not(DELETED(t5)),
    DEPT_id(t5) == v3__Int,
    Not(NULL(t5, DEPT_id__String)),
    DEPT_name(t5) == v4__Int,
    Not(NULL(t5, DEPT_name__String))
)

premise1 = And(
    # t6 := Filter(t1, Cond = (EMP_age > 25), )
    And(Implies(And(Not(DELETED(t1)), EMP_age(t1) > 25),
                And(Not(DELETED(t6)), t6 == t1)),
        Implies(Not(And(Not(DELETED(t1)), EMP_age(t1) > 25)),
                DELETED(t6))),

    # t7 := Filter(t2, Cond = (EMP_age > 25), )
    And(Implies(And(Not(DELETED(t2)), EMP_age(t2) > 25),
                And(Not(DELETED(t7)), t7 == t2)),
        Implies(Not(And(Not(DELETED(t2)), EMP_age(t2) > 25)),
                DELETED(t7))),

    # t8 := Filter(t3, Cond = (EMP_age > 25), )
    And(Implies(And(Not(DELETED(t3)), EMP_age(t3) > 25),
                And(Not(DELETED(t8)), t8 == t3)),
        Implies(Not(And(Not(DELETED(t3)), EMP_age(t3) > 25)),
                DELETED(t8))),

    # t9 := Projection(t6, Cond = DISTINCT ([EMP_age, EMP_dept_id]), )
    And(Implies(Not(DELETED(t6)),
                And(Not(DELETED(t9)),
                    EMP_age(t9) == EMP_age(t6),
                    NULL(t9, EMP_age__String) ==
                    NULL(t6, EMP_age__String),
                    EMP_dept_id(t9) == EMP_dept_id(t6),
                    NULL(t9, EMP_dept_id__String) ==
                    NULL(t6, EMP_dept_id__String))),
        Implies(Not(Not(DELETED(t6))), DELETED(t9))),

    # t10 := Projection(t7, Cond = DISTINCT ([EMP_age, EMP_dept_id]), )
    And(
        Implies(
            And(
                And(
                    Or(
                        Implies(
                            Not(DELETED(t6)),
                            Not(
                                And(
                                    Or(
                                        EMP_age(t7) == EMP_age(t6),
                                        And(NULL(t7, EMP_age__String), NULL(t6, EMP_age__String))
                                    ),
                                    Or(
                                        EMP_dept_id(t7) == EMP_dept_id(t6),
                                        And(NULL(t7, EMP_dept_id__String), NULL(t6, EMP_dept_id__String))
                                    )
                                )
                            )
                        )
                    ),
                    Not(DELETED(t7))
                )
            ),
            And(Not(DELETED(t10)),
                EMP_age(t10) == EMP_age(t7),
                NULL(t10, EMP_age__String) ==
                NULL(t7, EMP_age__String),
                EMP_dept_id(t10) == EMP_dept_id(t7),
                NULL(t10, EMP_dept_id__String) ==
                NULL(t7, EMP_dept_id__String))),
        Implies(Not(And(And(Or(Implies(Not(DELETED(t6)),
                                       Not(And(Or(EMP_age(t7) ==
                                                  EMP_age(t6),
                                                  And(NULL(t7,
                                                           EMP_age__String),
                                                      NULL(t6,
                                                           EMP_age__String))),
                                               Or(EMP_dept_id(t7) ==
                                                  EMP_dept_id(t6),
                                                  And(NULL(t7,
                                                           EMP_dept_id__String),
                                                      NULL(t6,
                                                           EMP_dept_id__String))))))),
                            Not(DELETED(t7))))),
                DELETED(t10))),

    # t11 := Projection(t8, Cond = DISTINCT ([EMP_age, EMP_dept_id]), )
    And(Implies(And(And(Or(Implies(Not(DELETED(t6)),
                                   Not(And(Or(EMP_age(t8) ==
                                              EMP_age(t6),
                                              And(NULL(t8,
                                                       EMP_age__String),
                                                  NULL(t6,
                                                       EMP_age__String))),
                                           Or(EMP_dept_id(t8) ==
                                              EMP_dept_id(t6),
                                              And(NULL(t8,
                                                       EMP_dept_id__String),
                                                  NULL(t6,
                                                       EMP_dept_id__String)))))),
                           Implies(Not(DELETED(t7)),
                                   Not(And(Or(EMP_age(t8) ==
                                              EMP_age(t7),
                                              And(NULL(t8,
                                                       EMP_age__String),
                                                  NULL(t7,
                                                       EMP_age__String))),
                                           Or(EMP_dept_id(t8) ==
                                              EMP_dept_id(t7),
                                              And(NULL(t8,
                                                       EMP_dept_id__String),
                                                  NULL(t7,
                                                       EMP_dept_id__String))))))),
                        Not(DELETED(t8)))),
                And(Not(DELETED(t11)),
                    EMP_age(t11) == EMP_age(t8),
                    NULL(t11, EMP_age__String) ==
                    NULL(t8, EMP_age__String),
                    EMP_dept_id(t11) == EMP_dept_id(t8),
                    NULL(t11, EMP_dept_id__String) ==
                    NULL(t8, EMP_dept_id__String))),
        Implies(Not(And(And(Or(Implies(Not(DELETED(t6)),
                                       Not(And(Or(EMP_age(t8) ==
                                                  EMP_age(t6),
                                                  And(NULL(t8,
                                                           EMP_age__String),
                                                      NULL(t6,
                                                           EMP_age__String))),
                                               Or(EMP_dept_id(t8) ==
                                                  EMP_dept_id(t6),
                                                  And(NULL(t8,
                                                           EMP_dept_id__String),
                                                      NULL(t6,
                                                           EMP_dept_id__String)))))),
                               Implies(Not(DELETED(t7)),
                                       Not(And(Or(EMP_age(t8) ==
                                                  EMP_age(t7),
                                                  And(NULL(t8,
                                                           EMP_age__String),
                                                      NULL(t7,
                                                           EMP_age__String))),
                                               Or(EMP_dept_id(t8) ==
                                                  EMP_dept_id(t7),
                                                  And(NULL(t8,
                                                           EMP_dept_id__String),
                                                      NULL(t7,
                                                           EMP_dept_id__String))))))),
                            Not(DELETED(t8))))),
                DELETED(t11)))  # 1st SQL query formulas
)

premise2 = And(
    # t12 := Filter(t1, Cond = (¬(EMP_age <= 25)), )
    And(Implies(And(Not(DELETED(t1)), Not(EMP_age(t1) <= 25)),
                And(Not(DELETED(t12)), t12 == t1)),
        Implies(Not(And(Not(DELETED(t1)),
                        Not(EMP_age(t1) <= 25))),
                DELETED(t12))),

    # t13 := Filter(t2, Cond = (¬(EMP_age <= 25)), )
    And(Implies(And(Not(DELETED(t2)), Not(EMP_age(t2) <= 25)),
                And(Not(DELETED(t13)), t13 == t2)),
        Implies(Not(And(Not(DELETED(t2)),
                        Not(EMP_age(t2) <= 25))),
                DELETED(t13))),

    # t14 := Filter(t3, Cond = (¬(EMP_age <= 25)), )
    And(Implies(And(Not(DELETED(t3)), Not(EMP_age(t3) <= 25)),
                And(Not(DELETED(t14)), t14 == t3)),
        Implies(Not(And(Not(DELETED(t3)),
                        Not(EMP_age(t3) <= 25))),
                DELETED(t14))),

    # t15 := Projection(t12, Cond = DISTINCT ([EMP_age, EMP_dept_id]), )
    And(Implies(Not(DELETED(t12)),
                And(Not(DELETED(t15)),
                    EMP_age(t15) == EMP_age(t12),
                    NULL(t15, EMP_age__String) ==
                    NULL(t12, EMP_age__String),
                    EMP_dept_id(t15) == EMP_dept_id(t12),
                    NULL(t15, EMP_dept_id__String) ==
                    NULL(t12, EMP_dept_id__String))),
        Implies(Not(Not(DELETED(t12))), DELETED(t15))),

    # t16 := Projection(t13, Cond = DISTINCT ([EMP_age, EMP_dept_id]), )
    And(Implies(And(And(Or(Implies(Not(DELETED(t12)),
                                   Not(And(Or(EMP_age(t13) ==
                                              EMP_age(t12),
                                              And(NULL(t13,
                                                       EMP_age__String),
                                                  NULL(t12,
                                                       EMP_age__String))),
                                           Or(EMP_dept_id(t13) ==
                                              EMP_dept_id(t12),
                                              And(NULL(t13,
                                                       EMP_dept_id__String),
                                                  NULL(t12,
                                                       EMP_dept_id__String))))))),
                        Not(DELETED(t13)))),
                And(Not(DELETED(t16)),
                    EMP_age(t16) == EMP_age(t13),
                    NULL(t16, EMP_age__String) ==
                    NULL(t13, EMP_age__String),
                    EMP_dept_id(t16) == EMP_dept_id(t13),
                    NULL(t16, EMP_dept_id__String) ==
                    NULL(t13, EMP_dept_id__String))),
        Implies(Not(And(And(Or(Implies(Not(DELETED(t12)),
                                       Not(And(Or(EMP_age(t13) ==
                                                  EMP_age(t12),
                                                  And(NULL(t13,
                                                           EMP_age__String),
                                                      NULL(t12,
                                                           EMP_age__String))),
                                               Or(EMP_dept_id(t13) ==
                                                  EMP_dept_id(t12),
                                                  And(NULL(t13,
                                                           EMP_dept_id__String),
                                                      NULL(t12,
                                                           EMP_dept_id__String))))))),
                            Not(DELETED(t13))))),
                DELETED(t16))),

    # t17 := Projection(t14, Cond = DISTINCT ([EMP_age, EMP_dept_id]), )
    And(Implies(And(
        And(
            Or(
                Implies(Not(DELETED(t12)),
                        Not(And(Or(EMP_age(t14) ==
                                   EMP_age(t12),
                                   And(NULL(t14,
                                            EMP_age__String),
                                       NULL(t12,
                                            EMP_age__String))),
                                Or(EMP_dept_id(t14) ==
                                   EMP_dept_id(t12),
                                   And(NULL(t14,
                                            EMP_dept_id__String),
                                       NULL(t12,
                                            EMP_dept_id__String)))))),
                Implies(Not(DELETED(t13)),
                        Not(And(Or(EMP_age(t14) ==
                                   EMP_age(t13),
                                   And(NULL(t14,
                                            EMP_age__String),
                                       NULL(t13,
                                            EMP_age__String))),
                                Or(EMP_dept_id(t14) ==
                                   EMP_dept_id(t13),
                                   And(NULL(t14,
                                            EMP_dept_id__String),
                                       NULL(t13,
                                            EMP_dept_id__String))))))
            ),
            Not(DELETED(t14))
        )
    ),
        And(Not(DELETED(t17)),
            EMP_age(t17) == EMP_age(t14),
            NULL(t17, EMP_age__String) ==
            NULL(t14, EMP_age__String),
            EMP_dept_id(t17) == EMP_dept_id(t14),
            NULL(t17, EMP_dept_id__String) ==
            NULL(t14, EMP_dept_id__String))),
        Implies(Not(And(And(Or(Implies(Not(DELETED(t12)),
                                       Not(And(Or(EMP_age(t14) ==
                                                  EMP_age(t12),
                                                  And(NULL(t14,
                                                           EMP_age__String),
                                                      NULL(t12,
                                                           EMP_age__String))),
                                               Or(EMP_dept_id(t14) ==
                                                  EMP_dept_id(t12),
                                                  And(NULL(t14,
                                                           EMP_dept_id__String),
                                                      NULL(t12,
                                                           EMP_dept_id__String)))))),
                               Implies(Not(DELETED(t13)),
                                       Not(And(Or(EMP_age(t14) ==
                                                  EMP_age(t13),
                                                  And(NULL(t14,
                                                           EMP_age__String),
                                                      NULL(t13,
                                                           EMP_age__String))),
                                               Or(EMP_dept_id(t14) ==
                                                  EMP_dept_id(t13),
                                                  And(NULL(t14,
                                                           EMP_dept_id__String),
                                                      NULL(t13,
                                                           EMP_dept_id__String))))))),
                            Not(DELETED(t14))))),
                DELETED(t17)))  # 2nd SQL query formulas
)

premise = And(DBMS_facts, premise1, premise2)


def equals(ltuples, rtuples):
    def _tuple_equals(tuple1, tuple2):
        return And(
            And(Not(DELETED(tuple1)), Not(DELETED(tuple2))),
            Or(
                And(NULL(tuple1, EMP_age__String), NULL(tuple2, EMP_age__String)),
                EMP_age(tuple1) == EMP_age(tuple2),
            ),
            Or(
                And(NULL(tuple1, EMP_dept_id__String), NULL(tuple2, EMP_dept_id__String)),
                EMP_dept_id(tuple1) == EMP_dept_id(tuple2),
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


conclusion = equals(ltuples=[t9, t10, t11], rtuples=[t15, t16, t17])

solver = Solver()

solver.add(Not(Or(
    Implies(premise, conclusion)
)))

out = solver.check()

print(f'Symbolic Reasoning Output: ==> {out} <==')

if out == sat:
    print(solver.model())
