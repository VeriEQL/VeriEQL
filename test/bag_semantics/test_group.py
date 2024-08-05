# -*- coding: utf-8 -*-


import itertools

from z3 import *

T = DeclareSort('T')
DELETED = Function('DELETED', T, BoolSort())
NULL = Function('NULL', T, StringSort(), BoolSort())

EMP_id = Function('EMP_id', T, IntSort())
EMP_name = Function('EMP_name', T, IntSort())
EMP_age = Function('EMP_age', T, IntSort())
EMP_dept_id = Function('EMP_dept_id', T, IntSort())
DEPT_id = Function('DEPT_id', T, IntSort())
DEPT_name = Function('DEPT_name', T, IntSort())

EMP_id_str = Const('EMP_id_str', StringSort())
EMP_name_str = Const('EMP_name_str', StringSort())
EMP_age_str = Const('EMP_age_str', StringSort())
EMP_dept_id_str = Const('EMP_dept_id_str', StringSort())
DEPT_name_str = Const('DEPT_name_str', StringSort())
DEPT_id_str = Const('DEPT_id_str', StringSort())

# aggregation

ALL = Const('*', StringSort())
COUNT = Function('COUNT', T, StringSort(), IntSort())
COUNT_ALL_str = Const('COUNT_ALL_str', StringSort())

COUNT_EMP_id__str = Const('COUNT_EMP_id__str', StringSort())
COUNT_EMP_name__str = Const('COUNT_EMP_name__str', StringSort())
COUNT_EMP_age__str = Const('COUNT_EMP_age__str', StringSort())
COUNT_EMP_dept_id__str = Const('COUNT_EMP_dept_id__str', StringSort())

COUNT_DEPT_name__str = Const('COUNT_DEPT_name__str', StringSort())
COUNT_DEPT_id__str = Const('COUNT_DEPT_id__str', StringSort())

# base tuples and their values from the DBMS
t1, t2, t3 = Consts('t1 t2 t3', T)
x1, x2, x3, x4 = Ints('x1 x2 x3 x4')
x5, x6, x7, x8 = Ints('x5 x6 x7 x8')
x9, x10, x11, x12 = Ints('x9 x10 x11 x12')

t4, t5, t6, t7, t8, t9, t10, t11, t12 = Consts('t4 t5 t6 t7 t8 t9 t10 t11 t12', T)
t13, t14, t15, t16, t17, t18, t19, t20 = Consts('t13 t14 t15 t16 t17 t18 t19 t20', T)
t21, t22, t23, t24, t25, t26, t27 = Consts('t21 t22 t23 t24 t25 t26 t27', T)
t28, t29, t30, t31, t32, t33, t34, t35 = Consts('t28 t29 t30 t31 t32 t33 t34 t35', T)
t36, t37, t38, t39, t40, t41, t42, t43 = Consts('t36 t37 t38 t39 t40 t41 t42 t43', T)
t44, t45, t46, t47, t48, t49, t50, t51 = Consts('t44 t45 t46 t47 t48 t49 t50 t51', T)
t52, t53, t54, t55, t56, t57, t58, t59 = Consts('t52 t53 t54 t55 t56 t57 t58 t59', T)
t60, t61, t62, t63, t64, t65, t66, t67 = Consts('t60 t61 t62 t63 t64 t65 t66 t67', T)
t68, t69, t70, t71, t72, t73, t74, t75 = Consts('t68 t69 t70 t71 t72 t73 t74 t75', T)

solver = Solver()

DBMS_facts = And(
    Not(DELETED(t1)),
    Not(DELETED(t2)),
    Not(DELETED(t3)),

    EMP_id(t1) == x1, EMP_name(t1) == x2, EMP_age(t1) == x3, EMP_dept_id(t1) == x4,
    Not(NULL(t1, EMP_id_str)), Not(NULL(t1, EMP_name_str)), Not(NULL(t1, EMP_age_str)),
    Not(NULL(t1, EMP_dept_id_str)),

    EMP_id(t2) == x5, EMP_name(t2) == x6, EMP_age(t2) == x7, EMP_dept_id(t2) == x8,
    Not(NULL(t2, EMP_id_str)), Not(NULL(t2, EMP_name_str)), Not(NULL(t2, EMP_age_str)),
    Not(NULL(t2, EMP_dept_id_str)),

    EMP_id(t3) == x9, EMP_name(t3) == x10, EMP_age(t3) == x11, EMP_dept_id(t3) == x12,
    Not(NULL(t3, EMP_id_str)), Not(NULL(t3, EMP_name_str)), Not(NULL(t3, EMP_age_str)),
    Not(NULL(t3, EMP_dept_id_str)),
)


# sql1 = "SELECT DEPT_id, COUNT(DEPT_id) FROM EMP WHERE age >= 25 GROUP BY DEPT_id, age HAVING COUNT(DEPT_id) > 0 AND COUNT(age) > 0"

# EMP = [
#     t1 = [id=x1, name=x2, age=x3, DEPT_id=x4],
#     t2 = [id=x5, name=x6, age=x7, DEPT_id=x8],
#     t3 = [id=x9, name=x10, age=x11, DEPT_id=x12],
# ]

# SELECT DEPT_id FROM EMP GROUP BY DEPT_id, age
def expand1(prev_tuples, curr_tuples, attribute):
    assert len(prev_tuples) == len(curr_tuples)

    out = []
    criterion = attribute(prev_tuples[0])
    for prev_t, curr_t in zip(prev_tuples, curr_tuples):
        out.extend(
            [
                # prev_t -> curr_t
                Implies(
                    And(Not(DELETED(prev_t)), EMP_age(prev_t) >= 25, attribute(prev_t) == criterion),
                    And(
                        Not(DELETED(curr_t)),
                        # equal mapping
                        EMP_id(curr_t) == EMP_id(prev_t), NULL(curr_t, EMP_id_str) == NULL(prev_t, EMP_id_str),
                        EMP_name(curr_t) == EMP_name(prev_t), NULL(curr_t, EMP_name_str) == NULL(prev_t, EMP_name_str),
                        EMP_age(curr_t) == EMP_age(prev_t), NULL(curr_t, EMP_age_str) == NULL(prev_t, EMP_age_str),
                        EMP_dept_id(curr_t) == EMP_dept_id(prev_t),
                        NULL(curr_t, EMP_dept_id_str) == NULL(prev_t, EMP_dept_id_str),
                    ),
                ),
                Implies(
                    Not(And(Not(DELETED(prev_t)), EMP_age(prev_t) >= 25, attribute(prev_t) == criterion)),
                    DELETED(curr_t),
                ),
            ]
        )
    return out


# (t1, t2, t3) -> (t4, t5, t6)
# (    t2, t3) -> (    t7, t8)
# (        t3) -> (        t9)
# 1) BY DEPT_id
group1_dept_id = And(*[
    *expand1([t1, t2, t3], [t4, t5, t6], attribute=EMP_dept_id),
    *expand1([t2, t3], [t7, t8], attribute=EMP_dept_id),
    *expand1([t3], [t9], attribute=EMP_dept_id),
])


def mutex_constraints(tuple_matrix):
    out = []
    LENGTH = len(tuple_matrix[0])
    for array_idx, tuple_array in enumerate(tuple_matrix[1:], start=1):
        tmux_tuples = [array[array_idx - LENGTH] for idx, array in enumerate(tuple_matrix[:array_idx])]
        out.extend(
            [
                Implies(
                    # at least 1 previous tuple in the same column exist
                    Or(*[Not(DELETED(t)) for t in tmux_tuples]),
                    And(*[DELETED(t) for t in tuple_array]),  # delete all tuples in the row
                ),
                Implies(
                    # all previous tuples in the same column do not exist
                    And(*[DELETED(t) for t in tmux_tuples]),
                    # the head tuple cannot be deleted, as for the subsequent tuples will be determined by conditions and later mutex contrainst
                    Not(DELETED(tuple_array[0])),
                ),
            ]
        )
    for idx in range(1, 1 + LENGTH):
        # row: 0-idx, col: idx-0
        tuple_ids = [tuple_matrix[i][j] for i, j in zip(range(idx), reversed(range(idx)))]
        out.append(
            Sum([If(DELETED(t), 0, 1) for t in tuple_ids]) == 1
        )
    return out


group1_dept_id_mutex_check = mutex_constraints([
    [t4, t5, t6],
    [t7, t8],
    [t9],
])
group1_dept_id_mutex_check = And(*group1_dept_id_mutex_check)

# 2) BY age
# (t1, t2, t3) -> (t10, t11, t12)
# (    t2, t3) -> (     t13, t14)
# (        t3) -> (          t15)
group1_age = And(*[
    *expand1([t1, t2, t3], [t10, t11, t12], attribute=EMP_age),
    *expand1([t2, t3], [t13, t14], attribute=EMP_age),
    *expand1([t3], [t15], attribute=EMP_age),
])

group1_age_mutex_check = mutex_constraints([
    [t10, t11, t12],
    [t13, t14],
    [t15],
])
group1_age_mutex_check = And(*group1_age_mutex_check)


# SELECT DEPT_id, COUNT(DEPT_id), AVG(age) FROM (...) HAVING COUNT(DEPT_id) > 0 and COUNT(age) > 0
# GROUP BY DEPT_id, age

# DEPT_id:
# (t1, t2, t3) -> (t4, t5, t6)
# (    t2, t3) -> (    t7, t8)
# (        t3) -> (        t9)

# age:
# (t1, t2, t3) -> (t10, t11, t12)
# (    t2, t3) -> (     t13, t14)
# (        t3) -> (          t15)


def merge(prev_tuples, curr_tuple, attribute):
    # HAVING: (t4, t5, t6) -> t16
    return [
        Implies(
            Or(*[Not(DELETED(t)) for t in prev_tuples]),  # group is not empty
            And(
                Not(DELETED(curr_tuple)),
                attribute(curr_tuple) == attribute(prev_tuples[0]),  # GROUP BY DEPT_id
            ),
        ),
        Implies(
            And(*[DELETED(t) for t in prev_tuples]),  # group is empty
            DELETED(curr_tuple),
        ),
    ]


concated_group1 = [
    # DEPT_id
    *merge([t4, t5, t6], t16, attribute=EMP_dept_id),
    *merge([t7, t8], t17, attribute=EMP_dept_id),
    *merge([t9], t18, attribute=EMP_dept_id),
    # age
    *merge([t10, t11, t12], t19, attribute=EMP_age),
    *merge([t13, t14], t20, attribute=EMP_age),
    *merge([t15], t21, attribute=EMP_age),
]


def attribute_mapping(prev_tuples, curr_tuple, reversed_tuple_mapping):
    # (t4, t5, t6) X (t10, t11, t12) -> (t16, t19) -> t22
    # (t4, t5, t6) X (     t11, t12) -> (t16, t20) -> t23
    # (t4, t5, t6) X (          t12) -> (t16, t21) -> t24
    # (    t7, t8) X (t10, t11, t12) -> (t17, t19) -> t25
    # (    t7, t8) X (     t11, t12) -> (t17, t20) -> t26
    # (    t7, t8) X (          t12) -> (t17, t21) -> t27
    # (        t9) X (t10, t11, t12) -> (t18, t19) -> t28
    # (        t9) X (     t11, t12) -> (t18, t20) -> t29
    # (        t9) X (          t12) -> (t18, t21) -> t30
    return [
        Implies(
            And(*[Not(DELETED(t)) for t in prev_tuples]),
            And(
                Not(DELETED(curr_tuple)),
                EMP_dept_id(curr_tuple) == EMP_dept_id(prev_tuples[0]),
                NULL(curr_tuple, EMP_dept_id_str) == NULL(prev_tuples[0], EMP_dept_id_str),
                EMP_age(curr_tuple) == EMP_age(prev_tuples[1]),
                NULL(curr_tuple, EMP_age_str) == NULL(prev_tuples[0], EMP_age_str),

                COUNT(curr_tuple, COUNT_EMP_age__str) == Sum([
                    *[
                        If(And(Not(DELETED(t)), Not(NULL(t, EMP_age_str))), 1, 0)
                        for t in reversed_tuple_mapping[prev_tuples[0]]
                    ],
                    *[
                        If(And(Not(DELETED(t)), Not(NULL(t, EMP_age_str))), 1, 0)
                        for t in reversed_tuple_mapping[prev_tuples[1]]
                    ],

                ]),
                COUNT(curr_tuple, COUNT_EMP_dept_id__str) == Sum([
                    *[
                        If(And(Not(DELETED(t)), Not(NULL(t, EMP_dept_id_str))), 1, 0)
                        for t in reversed_tuple_mapping[prev_tuples[0]]
                    ],
                    *[
                        If(And(Not(DELETED(t)), Not(NULL(t, EMP_dept_id_str))), 1, 0)
                        for t in reversed_tuple_mapping[prev_tuples[1]]
                    ],
                ]),
            ),
        ),
        Implies(
            Not(And(*[Not(DELETED(t)) for t in prev_tuples])),
            DELETED(curr_tuple),
        ),
    ]


reversed_tuple_mapping = {
    t16: [t4, t5, t6],
    t17: [t7, t8],
    t18: [t9],
    t19: [t10, t11, t12],
    t20: [t13, t14],
    t21: [t15],
}

concated_group1.extend([
    *attribute_mapping([t16, t19], t22, reversed_tuple_mapping),
    *attribute_mapping([t16, t20], t23, reversed_tuple_mapping),
    *attribute_mapping([t16, t21], t24, reversed_tuple_mapping),
    *attribute_mapping([t17, t19], t25, reversed_tuple_mapping),
    *attribute_mapping([t17, t20], t26, reversed_tuple_mapping),
    *attribute_mapping([t17, t21], t27, reversed_tuple_mapping),
    *attribute_mapping([t18, t19], t28, reversed_tuple_mapping),
    *attribute_mapping([t18, t20], t29, reversed_tuple_mapping),
    *attribute_mapping([t18, t21], t30, reversed_tuple_mapping),
])
concated_group1 = And(*concated_group1)


def having1(prev_tuple, curr_tuple):
    # HAVING COUNT(DEPT_id) > 0 AND COUNT(age) > 0"
    return [
        Implies(
            And(Not(DELETED(prev_tuple)),
                COUNT(prev_tuple, COUNT_EMP_dept_id__str) > 0,
                COUNT(prev_tuple, COUNT_EMP_age__str) > 0,
                ),
            And(
                Not(DELETED(curr_tuple)),

                EMP_dept_id(curr_tuple) == EMP_dept_id(prev_tuple),
                NULL(curr_tuple, EMP_dept_id_str) == NULL(prev_tuple, EMP_dept_id_str),

                EMP_age(curr_tuple) == EMP_age(prev_tuple),
                NULL(curr_tuple, EMP_age_str) == NULL(prev_tuple, EMP_age_str),

                COUNT(curr_tuple, COUNT_EMP_dept_id__str) == COUNT(prev_tuple, COUNT_EMP_dept_id__str),
                COUNT(curr_tuple, COUNT_EMP_age__str) == COUNT(prev_tuple, COUNT_EMP_age__str),
            ),
        ),
        Implies(
            Not(
                And(Not(DELETED(prev_tuple)),
                    COUNT(prev_tuple, COUNT_EMP_dept_id__str) > 0,
                    COUNT(prev_tuple, COUNT_EMP_age__str) > 0,
                    ),
            ),
            DELETED(curr_tuple),
        ),
    ]


group1_having = And(*[
    *having1(t22, t31),
    *having1(t23, t32),
    *having1(t24, t33),
    *having1(t25, t34),
    *having1(t26, t35),
    *having1(t27, t36),
    *having1(t28, t37),
    *having1(t29, t38),
    *having1(t30, t39),
])

result1 = And(
    # group of 1st key
    group1_dept_id,
    group1_dept_id_mutex_check,
    # group of 2nd key
    group1_age,
    group1_age_mutex_check,
    concated_group1,  # concatenate groups
    group1_having,  # having condition
)


# sql2 = "SELECT DEPT_id, COUNT(DEPT_id) FROM EMP WHERE NOT age < 25 GROUP BY age, DEPT_id HAVING NOT COUNT(DEPT_id) <= 0 AND NOT and COUNT(age) <= 0"

def expand2(prev_tuples, curr_tuples, attribute):
    assert len(prev_tuples) == len(curr_tuples)

    out = []
    criterion = attribute(prev_tuples[0])
    for prev_t, curr_t in zip(prev_tuples, curr_tuples):
        out.extend(
            [
                # prev_t -> curr_t
                Implies(
                    And(Not(DELETED(prev_t)), Not(EMP_age(prev_t) < 25), attribute(prev_t) == criterion),
                    And(
                        Not(DELETED(curr_t)),
                        # equal mapping
                        EMP_id(curr_t) == EMP_id(prev_t), NULL(curr_t, EMP_id_str) == NULL(prev_t, EMP_id_str),
                        EMP_name(curr_t) == EMP_name(prev_t), NULL(curr_t, EMP_name_str) == NULL(prev_t, EMP_name_str),
                        EMP_age(curr_t) == EMP_age(prev_t), NULL(curr_t, EMP_age_str) == NULL(prev_t, EMP_age_str),
                        EMP_dept_id(curr_t) == EMP_dept_id(prev_t),
                        NULL(curr_t, EMP_dept_id_str) == NULL(prev_t, EMP_dept_id_str),
                    ),
                ),
                Implies(
                    Not(And(Not(DELETED(prev_t)), Not(EMP_age(prev_t) < 25), attribute(prev_t) == criterion)),
                    DELETED(curr_t),
                ),
            ]
        )
    return out


# 1) BY age
# (t1, t2, t3) -> (t40, t41, t42)
# (    t2, t3) -> (     t43, t44)
# (        t3) -> (          t45)
group2_age = And(*[
    *expand2([t1, t2, t3], [t40, t41, t42], attribute=EMP_age),
    *expand2([t2, t3], [t43, t44], attribute=EMP_age),
    *expand2([t3], [t45], attribute=EMP_age),
])

group2_age_mutex_check = mutex_constraints([
    [t40, t41, t42],
    [t43, t44],
    [t45],
])
group2_age_mutex_check = And(*group2_age_mutex_check)

# 2) BY DEPT_id
# (t1, t2, t3) -> (t46, t47, t48)
# (    t2, t3) -> (     t49, t50)
# (        t3) -> (          t51)
group2_dept_id = And(*[
    *expand1([t1, t2, t3], [t46, t47, t48], attribute=EMP_dept_id),
    *expand1([t2, t3], [t49, t50], attribute=EMP_dept_id),
    *expand1([t3], [t51], attribute=EMP_dept_id),
])

group2_dept_id_mutex_check = mutex_constraints([
    [t46, t47, t48],
    [t49, t50],
    [t51],
])
group2_dept_id_mutex_check = And(*group2_dept_id_mutex_check)

# SELECT DEPT_id, COUNT(DEPT_id), AVG(age) FROM (...) HAVING COUNT(DEPT_id) > 0 and COUNT(age) > 0
# GROUP BY age, DEPT_id

# age:
# (t1, t2, t3) -> (t40, t41, t42)
# (    t2, t3) -> (     t43, t44)
# (        t3) -> (          t45)

# DEPT_id:
# (t1, t2, t3) -> (t46, t47, t48)
# (    t2, t3) -> (     t49, t50)
# (        t3) -> (          t51)


concated_group2 = [
    # age
    *merge([t40, t41, t42], t52, attribute=EMP_age),
    *merge([t43, t44], t53, attribute=EMP_age),
    *merge([t45], t54, attribute=EMP_age),
    # DEPT_id
    *merge([t46, t47, t48], t55, attribute=EMP_dept_id),
    *merge([t49, t50], t56, attribute=EMP_dept_id),
    *merge([t51], t57, attribute=EMP_age),
]

reversed_tuple_mapping = {
    t52: [t40, t41, t42],
    t53: [t43, t44],
    t54: [t45],
    t55: [t46, t47, t48],
    t56: [t49, t50],
    t57: [t51],
}

# (t40, t41, t42) X (t46, t47, t48) -> (t52, t55) -> t58
# (t40, t41, t42) X (     t47, t48) -> (t52, t56) -> t59
# (t40, t41, t42) X (          t48) -> (t52, t57) -> t60
# (     t41, t42) X (t46, t47, t48) -> (t53, t55) -> t61
# (     t41, t42) X (     t47, t48) -> (t53, t56) -> t62
# (     t41, t42) X (          t48) -> (t53, t57) -> t63
# (          t42) X (t46, t47, t48) -> (t54, t55) -> t64
# (          t42) X (     t47, t48) -> (t54, t56) -> t65
# (          t42) X (          t48) -> (t54, t57) -> t66

concated_group2.extend([
    *attribute_mapping([t52, t55], t58, reversed_tuple_mapping),
    *attribute_mapping([t52, t56], t59, reversed_tuple_mapping),
    *attribute_mapping([t52, t57], t60, reversed_tuple_mapping),
    *attribute_mapping([t53, t55], t61, reversed_tuple_mapping),
    *attribute_mapping([t53, t56], t62, reversed_tuple_mapping),
    *attribute_mapping([t53, t57], t63, reversed_tuple_mapping),
    *attribute_mapping([t54, t55], t64, reversed_tuple_mapping),
    *attribute_mapping([t54, t56], t65, reversed_tuple_mapping),
    *attribute_mapping([t54, t57], t66, reversed_tuple_mapping),
])
concated_group2 = And(*concated_group2)


def having2(prev_tuple, curr_tuple):
    # HAVING NOT COUNT(DEPT_id) <= 0 AND NOT and COUNT(age) <= 0
    return [
        Implies(
            And(Not(DELETED(prev_tuple)),
                Not(COUNT(prev_tuple, COUNT_EMP_dept_id__str) <= 0),
                Not(COUNT(prev_tuple, COUNT_EMP_age__str) <= 0),
                ),
            And(
                Not(DELETED(curr_tuple)),

                EMP_dept_id(curr_tuple) == EMP_dept_id(prev_tuple),
                NULL(curr_tuple, EMP_dept_id_str) == NULL(prev_tuple, EMP_dept_id_str),

                EMP_age(curr_tuple) == EMP_age(prev_tuple),
                NULL(curr_tuple, EMP_age_str) == NULL(prev_tuple, EMP_age_str),

                COUNT(curr_tuple, COUNT_EMP_dept_id__str) == COUNT(prev_tuple, COUNT_EMP_dept_id__str),
                COUNT(curr_tuple, COUNT_EMP_age__str) == COUNT(prev_tuple, COUNT_EMP_age__str),
            ),
        ),
        Implies(
            Not(
                And(Not(DELETED(prev_tuple)),
                    Not(COUNT(prev_tuple, COUNT_EMP_dept_id__str) <= 0),
                    Not(COUNT(prev_tuple, COUNT_EMP_age__str) <= 0),
                    ),
            ),
            DELETED(curr_tuple),
        ),
    ]


group2_having = And(*[
    *having2(t58, t67),
    *having2(t59, t68),
    *having2(t60, t69),
    *having2(t61, t70),
    *having2(t62, t71),
    *having2(t63, t72),
    *having2(t64, t73),
    *having2(t65, t74),
    *having2(t66, t75),
])

result2 = And(
    # group of 1st key
    group2_dept_id,
    group2_dept_id_mutex_check,
    # group of 2nd key
    group2_age,
    group2_age_mutex_check,
    concated_group2,  # concatenate groups
    group2_having,  # having condition
)

prerequisites = And(DBMS_facts, result1, result2)


def equals(ltuples, rtuples):
    def _tuple_equals(tuple1, tuple2):
        # DEPT_id, COUNT(dept_id), AVG(age)
        return And(
            And(Not(DELETED(tuple1)), Not(DELETED(tuple2))),
            Or(
                And(NULL(tuple1, EMP_dept_id_str), NULL(tuple2, EMP_dept_id_str)),
                EMP_dept_id(tuple1) == EMP_dept_id(tuple2),
                COUNT(tuple1, COUNT_EMP_dept_id__str) == COUNT(tuple2, COUNT_EMP_dept_id__str),
                COUNT(tuple1, COUNT_EMP_age__str) == COUNT(tuple2, COUNT_EMP_age__str),
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


conclusion = equals(
    ltuples=[t31, t32, t33, t34, t35, t36, t37, t38, t39],
    rtuples=[t67, t68, t69, t70, t71, t72, t73, t74, t75],
)

solver.add(Not(
    Implies(prerequisites, conclusion)
))

if solver.check() == sat:
    model = solver.model()
    print(model)

print(solver.check())
