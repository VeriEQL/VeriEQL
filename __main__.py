# -*- coding: utf-8 -*-

from constants import DIALECT
from environment import Environment


def main(sql1, sql2, schema, ROW_NUM=2, constraints=None, **kwargs):
    with Environment(**kwargs) as env:
        for k, v in schema.items():
            env.create_database(attributes=v, bound_size=ROW_NUM, name=k)
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
        "SELECT S.CUSTOMERKEY FROM SALES AS S",
        "SELECT S.CUSTOMERKEY+1 FROM SALES AS S WHERE EXISTS (SELECT SALES.CUSTOMERKEY FROM CUSTOMER JOIN SALES ON CUSTOMER.CUSTOMERKEY = SALES.CUSTOMERKEY WHERE SALES.CUSTOMERKEY != S.CUSTOMERKEY)",
    ]
    # Customer: CustomerKey [PK]
    # Sales: (CustomerKey [FK], OrderDateKey [FK]) [PK], ShipDate, DueDate
    # Date: DateKey [PK]
    schema = {
        "CUSTOMER": {"CUSTOMERKEY": "INT"},
        "SALES": {"CUSTOMERKEY": "INT", "ORDERDATEKEY": "INT", "SHIPDATE": "DATE", "DUEDATE": "DATE"},
        "DATE": {"DATEKEY": "INT"},
    }
    constants = [
        # use `__` to replace `.`, e.g., FRIENDSHIP.USER1_ID => FRIENDSHIP__USER1_ID
        {"primary": [{"value": "CUSTOMER__CUSTOMERKEY"}]},
        {"primary": [{"value": "SALES__CUSTOMERKEY"}, {"value": "SALES__ORDERDATEKEY"}]},
        {"primary": [{"value": "DATE__DATEKEY"}]},
        {"foreign": [{"value": "SALES__CUSTOMERKEY"}, {"value": "CUSTOMER__CUSTOMERKEY"}]},
        {"foreign": [{"value": "SALES__ORDERDATEKEY"}, {"value": "DATE__DATEKEY"}]},
    ]
    bound_size = 2
    # generate_code: generate SQL code and running outputs if you find a counterexample
    # timer: show time costs
    # show_counterexample: print counterexample?
    config = {'generate_code': True, 'timer': True, 'show_counterexample': True, "dialect": DIALECT.MYSQL}
    main(sql1, sql2, schema, ROW_NUM=bound_size, constraints=constants, **config)
