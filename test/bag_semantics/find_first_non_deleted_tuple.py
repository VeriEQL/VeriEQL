# -*- coding:utf-8 -*-
from z3 import *

# SELECT name, id FROM (SELECT name, age, id FROM EMP WHERE age > 25) WHERE age < 30
# SELECT name, id FROM EMP WHERE age > 25 AND age < 30

# define z3 Sorts
__TupleSort = DeclareSort("TupleSort")  # define `Tuple` sort
__Int = IntSort()  # define `Int` sort
__String = StringSort()  # define `String` sort
__Boolean = BoolSort()  # define `Boolean` sort

# Special functions
DELETED = Function("DELETED", __TupleSort,
                   __Boolean)  # define `DELETE` function to represent a tuple does not exist; Not(DELETE) means the existence of a tuple

t1 = Const('t1', __TupleSort)  # define a tuple `t1`
t2 = Const('t2', __TupleSort)  # define a tuple `t2`
t3 = Const('t3', __TupleSort)  # define a tuple `t3`
t4 = Const('t4', __TupleSort)  # define a tuple `t4`
t5 = Const('t5', __TupleSort)  # define a tuple `t5`
t6 = Const('t6', __TupleSort)  # define a tuple `t6`
t7 = Const('t7', __TupleSort)  # define a tuple `t7`
t8 = Const('t8', __TupleSort)  # define a tuple `t8`

tuples = [t1, t2, t3, t4]
copied_tuples = [t5, t6, t7, t8]

facts = And(
    DELETED(t1),
    DELETED(t2),
    Not(DELETED(t3)),
    DELETED(t4),

    t5 == t1,
    t6 == t2,
    t7 == t3,
    t8 == t4,
)

count = 20

constraints = []

print(tuples)
print(copied_tuples)
for i in range(1, len(tuples)):
    x = copied_tuples[0]
    y = copied_tuples[i]

    _x, _y = Const(f'p{count}', __TupleSort), Const(f'p{count + 1}', __TupleSort)
    count += 2

    constraints.append(
        If(
            And(DELETED(x), Not(DELETED(y))),
            And(_x == y, _y == x),
            And(_x == x, _y == y)
        )
    )

    copied_tuples[0] = _x
    copied_tuples[i] = _y
    print(copied_tuples)

solver = Solver()

prerequisites = And(facts, And(*[constraints]))
conclusion = And(
    Not(DELETED(copied_tuples[0])),
    copied_tuples[0] == t3,
    copied_tuples[0] == t7,
)

solver.add(Not(
    Implies(prerequisites, conclusion)
))

if solver.check() == sat:
    model = solver.model()
    print(model)
    print([model.eval(DELETED(t)) for t in [t5, t6, t7, t8]])
    print(model.eval(copied_tuples[0]))

print(solver.check())
