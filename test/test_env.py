# -*- coding: utf-8 -*-

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
        if result == True:
            print("\033[1;32;40m>>> Equivalent! \033[0m")
        else:
            print("\033[1;31;40m>>> Non-Equivalent! Found an counterexample! \033[0m")


def test1():
    sql1, sql2 = [
        "SELECT ID FROM EMP1",
        "(SELECT ID FROM EMP1 UNION ALL SELECT ID FROM EMP2) EXCEPT ALL SELECT ID FROM EMP2",
    ]
    schema = {"EMP1": {"ID": "INT"}, "EMP2": {"ID": "INT"}, }
    constants = None
    config = {'generate_code': False, 'timer': False}
    main(sql1, sql2, schema, ROW_NUM=1, constraints=constants, **config)


def test2():
    sql1, sql2 = [
        "SELECT DISTINCT PAGE_ID AS RECOMMENDED_PAGE FROM (SELECT CASE WHEN USER1_ID=1 THEN USER2_ID WHEN USER2_ID=1 THEN USER1_ID ELSE NULL END AS USER_ID FROM FRIENDSHIP) AS TB1 JOIN LIKES AS TB2 ON TB1.USER_ID=TB2.USER_ID WHERE PAGE_ID NOT IN (SELECT PAGE_ID FROM LIKES WHERE USER_ID=1)",
        "SELECT DISTINCT PAGE_ID AS RECOMMENDED_PAGE FROM (SELECT B.USER_ID, B.PAGE_ID FROM FRIENDSHIP A LEFT OUTER JOIN LIKES B ON (A.USER2_ID=B.USER_ID OR A.USER1_ID=B.USER_ID) AND (A.USER1_ID=1 OR A.USER2_ID=1) WHERE B.PAGE_ID NOT IN (SELECT DISTINCT PAGE_ID FROM LIKES WHERE USER_ID=1)) T",
    ]
    schema = {"FRIENDSHIP": {"USER1_ID": "INT", "USER2_ID": "INT"}, "LIKES": {"USER_ID": "INT", "PAGE_ID": "INT"}, }
    constants = [
        {"primary": [{"value": "FRIENDSHIP__USER1_ID"}, {"value": "FRIENDSHIP__USER2_ID"}]},
        {"primary": [{"value": "LIKES__USER_ID"}, {"value": "LIKES__PAGE_ID"}]},
        {"neq": [{"value": "FRIENDSHIP__USER1_ID"}, {"value": "FRIENDSHIP__USER2_ID"}]},
    ]
    config = {'generate_code': False, 'timer': False}
    main(sql1, sql2, schema, ROW_NUM=1, constraints=constants, **config)


if __name__ == '__main__':
    print("Testing python evironment...")
    test1()
    test2()
    print("Finished testing.")
