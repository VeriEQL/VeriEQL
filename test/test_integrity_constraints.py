from unittest import TestCase

from environment import Environment

FILE = 'test.py'


def is_eq(
        q1, q2,
        constraints=[],
        schema={
            'EMP': {'id': 'int', 'name': 'int', 'age': 'int', 'dept_id': 'int'},
            'DEPT': {'id': 'int', 'name': 'int'}
        },
        ROW_NUM=2,
):
    with Environment() as env:
        for k, v in schema.items():
            env.create_database(attributes=list(v.keys()), name=k, rows=ROW_NUM)
        env.save_checkpoints()
        out = env.analyze(q1, q2, out_file=FILE)
        return out


class TestIntegrityConstraints(TestCase):
    def test_membership_value_range(self):
        constraints = ['EMP.age <- [1, 100]']
        sql1 = "SELECT id FROM EMP"
        sql2 = "SELECT id FROM EMP WHERE age >= 1 AND age <= 100"
        self.assertTrue(is_eq(sql1, sql2, constraints))

    def test_membership_value_list(self):
        constraints = ["DEPT.name <- {'Math', 'Physics'}"]
        sql1 = "SELECT id FROM DEPT"
        sql2 = "SELECT id FROM DEPT WHERE name = 'Math' OR name = 'Physics'"
        self.assertTrue(is_eq(sql1, sql2, constraints))

    def test_membership_value_column_dependency(self):
        constraints = ["EMP.name <- DEPT.name"]
        sql1 = "SELECT COUNT(name) FROM EMP WHERE name IN (SELECT name FROM DEPT)"
        sql2 = "SELECT COUNT(name) FROM EMP"
        self.assertTrue(is_eq(sql1, sql2, constraints))

    def test_comparison(self):
        constraints = ["EMP.age >= 10", "EMP.id > 0"]
        sql1 = "SELECT * FROM EMP"
        sql2 = "SELECT * FROM EMP WHERE age >= 10 AND id > 0"
        self.assertTrue(is_eq(sql1, sql2, constraints))

    def test_not_null(self):
        constraints = ["EMP.name != NULL"]
        sql1 = "SELECT * FROM EMP"
        sql2 = "SELECT * FROM EMP WHERE name IS NOT NULL"
        self.assertTrue(is_eq(sql1, sql2, constraints))

    def test_unique(self):
        constraints = ["unique(EMP.id)"]
        sql1 = "SELECT id FROM EMP"
        sql2 = "SELECT DISTINCT id FROM EMP"
        self.assertTrue(is_eq(sql1, sql2, constraints))
