# -*- coding: utf-8 -*-

from constants import DIALECT
from environment import Environment


def main(sql1, sql2, schema, ROW_NUM=2, constraints=None, **kwargs):
    with Environment(**kwargs) as env:
        for k, v in schema.items():
            env.create_database(attributes=v, bound_size=ROW_NUM, name=k, test_dbs=kwargs.get("test_dbs", None))
        env.add_constraints(constraints)
        env.save_checkpoints()
        if env._script_writer is not None:
            env._script_writer.save_checkpoints()
        result = env.analyze(sql1, sql2, out_file="test/test.py")
        if env.show_counterexample:
            print(env.counterexample)
        if env.traversing_time is not None:
            print(f"Time cost: {env.traversing_time + env.solving_time:.2f}")
        if result == True:
            print("\033[1;32;40m>>> Equivalent! \033[0m")
        else:
            print("\033[1;31;40m>>> Non-Equivalent! Found a counterexample! \033[0m")


if __name__ == '__main__':
    sql1, sql2 = [
        "SELECT E.DEPT_ID, COUNT(*) FROM EMPLOYEE E JOIN DEPARTMENT D ON E.DEPT_ID = D.ID GROUP BY E.DEPT_ID ORDER BY COUNT(*) DESC",
        "SELECT E.DEPT_ID, COUNT(*) FROM DEPARTMENT D JOIN EMPLOYEE E ON D.ID = E.DEPT_ID GROUP BY E.DEPT_ID ORDER BY COUNT(*) DESC",
    ]
    schema = {
        'DEPARTMENT': {
            'ID': 'INT',
        },
        'EMPLOYEE': {
            'DEPT_ID': 'INT',
        }
    }
    constraints = [
        {'primary': [{'value': 'DEPARTMENT__ID'}]},
        {'foreign': [{'value': 'EMPLOYEE__DEPT_ID'}, {'value': 'DEPARTMENT__ID'}]},
    ]
    bound_size = 3
    # generate_code: generate SQL code and running outputs if you find a counterexample
    # timer: show time costs
    # show_counterexample: print counterexample?
    config = {'generate_code': True, 'timer': True, 'show_counterexample': True, "dialect": DIALECT.MYSQL,
              "test_dbs": {
                  "DEPARTMENT": [[-2], [-1], [0]],
                  "EMPLOYEE": [[0], [-2], [0]],
              }}
    main(sql1, sql2, schema, ROW_NUM=bound_size, constraints=constraints, **config)
