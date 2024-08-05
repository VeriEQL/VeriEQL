# -*- coding:utf-8 -*-

from unittest import TestCase


def is_eq(
        q1, q2,
        schema={
            'EMP': {'id': 'int', 'name': 'int', 'age': 'int', 'dept_id': 'int'},
            'DEPT': {'id': 'int', 'name': 'int'}
        },
        ROW_NUM=2,
):
    from environment import Environment
    with Environment() as env:
        for k, v in schema.items():
            env.create_database(attributes=v, name=k, bound_size=ROW_NUM)
        env.save_checkpoints()
        out = env.analyze(q1, q2)
        return out


class TestSPJ(TestCase):
    def test_simple_subqueries(self):
        sql1 = "SELECT name FROM (SELECT name, age, id FROM EMP WHERE age > 25 and age <30) WHERE age < 30"
        sql2 = "SELECT name FROM (SELECT id, name, age FROM EMP WHERE age < 30) WHERE age > 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_simple_subqueries_2(self):
        sql1 = "SELECT name FROM (SELECT name, age, id FROM EMP WHERE age > 25) WHERE age < 30"
        sql2 = "SELECT name FROM EMP WHERE age > 25 AND age < 30"
        self.assertTrue(is_eq(sql1, sql2))

    def test_multiple_subqueries_with_asterisk_symbol_ignore_permutation(self):
        sql1 = "SELECT id, name FROM (SELECT name, age, id FROM (SELECT * FROM (SELECT * FROM EMP)) WHERE age > 25) WHERE age < 30"
        sql2 = "SELECT id, name FROM (SELECT id, name, age FROM EMP WHERE age < 30) WHERE age > 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_multiple_subqueries_with_asterisk_symbol(self):
        # bad case, duplicate columns `SELECT *, dept_id FROM (SELECT * FROM EMP)`
        # sql1 = "SELECT name, id FROM (SELECT name, age, id FROM (SELECT *, dept_id FROM (SELECT * FROM EMP)) WHERE age > 25) WHERE age < 30"
        sql1 = "SELECT id, name FROM (SELECT name, age, id FROM (SELECT * FROM (SELECT * FROM EMP)) WHERE age > 25) WHERE age < 30"
        sql2 = "SELECT id, name FROM (SELECT id, name, age FROM EMP WHERE age < 30) WHERE age > 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_simple_subqueries_3(self):
        sql1 = "SELECT name FROM (SELECT name, age, id FROM EMP WHERE age > 25 AND age > 1) WHERE age < 30"
        sql2 = "SELECT name FROM EMP WHERE age > 25 AND age < 30 AND age < 500"
        self.assertTrue(is_eq(sql1, sql2))

    def test_subqueries_not_eq(self):
        sql1 = "SELECT name FROM (SELECT name, age, id FROM EMP WHERE age > 25) WHERE age < 30"
        sql2 = "SELECT name FROM EMP WHERE age > 25 AND age < 30"
        self.assertTrue(is_eq(sql1, sql2))

    def test_or(self):
        sql1 = "SELECT name FROM EMP WHERE age > 25 OR age > 50 OR (age > 200 AND age > 300)"
        sql2 = "SELECT name FROM EMP WHERE age > 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_not(self):
        sql1 = "SELECT name FROM EMP WHERE NOT age > 25"
        sql2 = "SELECT name FROM EMP WHERE age <= 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_as1(self):
        sql1 = "SELECT E.name AS name FROM EMP AS E WHERE NOT E.age > 25"
        sql2 = "SELECT name FROM EMP WHERE age <= 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_as2(self):
        sql1 = """SELECT T.EMPNAME, T.DEPTNAME FROM
                  (SELECT E.id, E.name AS EMPNAME, E.age AS EMPAGE, D.name AS DEPTNAME FROM EMP AS E, DEPT AS D WHERE E.dept_id = D.id AND E.age > 23) AS T
                  WHERE EMPAGE > 25"""
        sql2 = "SELECT EMP.name, DEPT.name FROM EMP, DEPT WHERE EMP.dept_id = DEPT.id AND EMP.age > 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_as3(self):
        sql1 = "SELECT COUNT(*) AS COUNT_COUNT_ALL, COUNT(COUNT_AGE) AS COUNT_COUNT_AGE, MAX(MAX_AGE) AS MAX_MAX_AGE, MIN(MIN_AGE) AS MIN_MIN_AGE, SUM(SUM_AGE) AS SUM_SUM_AGE, AVG(AVG_AGE) AS AVG_AVG_AGE FROM (SELECT COUNT(AGE) AS COUNT_AGE, MAX(AGE) AS MAX_AGE, MIN(AGE) AS MIN_AGE, SUM(AGE) AS SUM_AGE, AVG(AGE) AS AVG_AGE FROM EMP)"
        sql2 = "SELECT COUNT(*) AS COUNT___COUNT_ALL, COUNT(__COUNT_AGE) AS COUNT___COUNT_AGE, MAX(__MAX_AGE) AS MAX___MAX_AGE, MIN(__MIN_AGE) AS MIN___MIN_AGE, SUM(__SUM_AGE) AS SUM___SUM_AGE, AVG(__AVG_AGE) AS AVG___AVG_AGE FROM (SELECT COUNT(AGE) AS __COUNT_AGE, MIN(AGE) AS __MIN_AGE, SUM(AGE) AS __SUM_AGE, AVG(AGE) AS __AVG_AGE, MAX(AGE) AS __MAX_AGE FROM EMP)"
        self.assertTrue(is_eq(sql1, sql2))

    def test_as4(self):
        sql1 = "SELECT age, age-1, SUM(age), SUM(age-1), SUM(age-1)-1  FROM EMP"
        sql2 = "SELECT age, age-1 AS AGE_sub_1, SUM(age) AS SUM_AGE, SUM(age-1) AS SUM_AGE_sub_1, SUM(age-1)-1 AS SUM_AGE_sub_1_sub_1 FROM EMP"
        self.assertTrue(is_eq(sql1, sql2))

    def test_subqueries_not_same_cols_in_result(self):
        sql1 = "SELECT name, id FROM (SELECT name, age, id FROM EMP WHERE age > 25) WHERE age < 30"
        sql2 = "SELECT name, id FROM EMP WHERE age > 25 AND age < 30"
        self.assertTrue(is_eq(sql1, sql2))

    def test_dot_notation(self):
        sql1 = "SELECT name FROM (SELECT EMP.name, EMP.age, EMP.id FROM EMP WHERE EMP.age > 25) WHERE age < 30"
        sql2 = "SELECT name FROM (SELECT id, name, age FROM EMP WHERE age < 30) WHERE age > 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_simple_cartesian_product(self):
        sql1 = """SELECT EMP.name, DEPT.name FROM
                  (SELECT EMP.id, EMP.name, EMP.age, DEPT.name FROM EMP, DEPT WHERE EMP.dept_id = DEPT.id)
                  WHERE EMP.age > 25"""
        sql2 = "SELECT EMP.name, DEPT.name FROM EMP, DEPT WHERE EMP.dept_id = DEPT.id AND EMP.age > 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_simple_cartesian_product_2(self):
        sql1 = "SELECT T.name FROM (SELECT EMP.name, EMP.dept_id, DEPT.id, EMP.age FROM EMP, DEPT) AS T WHERE dept_id = T.id AND T.age > 25"
        sql2 = "SELECT EMP.name FROM EMP, DEPT WHERE EMP.dept_id = DEPT.id AND EMP.age > 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_cross_join(self):
        # the same thing as cartesian product
        sql1 = "SELECT EMP.name FROM EMP CROSS JOIN DEPT WHERE EMP.dept_id = DEPT.id"
        sql2 = "SELECT EMP.name FROM EMP, DEPT WHERE EMP.dept_id = DEPT.id"
        self.assertTrue(is_eq(sql1, sql2))

    def test_inner_join(self):
        sql1 = "SELECT EMP.name FROM EMP INNER JOIN DEPT ON EMP.dept_id = DEPT.id WHERE age > 25"
        sql2 = "SELECT EMP.name FROM EMP, DEPT WHERE EMP.dept_id = DEPT.id AND EMP.age > 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_inner_join_with_using(self):
        sql1 = "SELECT EMP.name FROM EMP JOIN DEPT USING (name) WHERE age > 25"
        sql2 = "SELECT EMP.name FROM EMP, DEPT WHERE EMP.name = DEPT.name AND EMP.age > 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_inner_join_with_using_not_same_as_on(self):
        sql1 = "SELECT * FROM EMP INNER JOIN DEPT USING (name) WHERE age > 25"
        sql2 = "SELECT * FROM EMP INNER JOIN DEPT ON EMP.name = DEPT.name WHERE age > 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_inner_join_with_using_same_as_on(self):
        sql1 = "SELECT * FROM EMP INNER JOIN DEPT USING (name) WHERE age > 25"
        sql2 = "SELECT EMP.id, EMP.name, EMP.age, EMP.dept_id, DEPT.id, DEPT.name FROM EMP INNER JOIN DEPT ON EMP.name = DEPT.name WHERE age > 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_natural_join(self):
        sql1 = "SELECT EMP.name FROM EMP NATURAL JOIN DEPT"
        sql2 = "SELECT EMP.name FROM EMP, DEPT WHERE EMP.id = DEPT.id AND EMP.name = DEPT.name"
        self.assertTrue(is_eq(sql1, sql2))

    def test_natural_join_with_using(self):
        sql1 = "SELECT EMP.name FROM EMP NATURAL JOIN DEPT USING (name)"
        sql2 = "SELECT EMP.name FROM EMP, DEPT WHERE EMP.name = DEPT.name"
        self.assertTrue(is_eq(sql1, sql2))

    def test_natural_join_with_using_2(self):
        sql1 = "SELECT EMP.name FROM EMP NATURAL JOIN DEPT USING (id, name)"
        sql2 = "SELECT EMP.name FROM EMP, DEPT WHERE EMP.id = DEPT.id AND EMP.name = DEPT.name"
        self.assertTrue(is_eq(sql1, sql2))

    def test_simple_outer_join(self):
        sql1 = "SELECT * FROM EMP LEFT OUTER JOIN DEPT ON EMP.dept_id = DEPT.id WHERE EMP.age > 25"
        sql2 = "SELECT * FROM DEPT RIGHT OUTER JOIN EMP ON EMP.dept_id = DEPT.id WHERE EMP.age > 25"
        self.assertFalse(is_eq(sql1, sql2))

    def test_simple_outer_join_2(self):
        sql1 = "SELECT * FROM EMP AS A LEFT OUTER JOIN EMP AS B ON A.id = B.id WHERE A.age > 25"
        sql2 = "SELECT * FROM EMP AS A JOIN EMP AS B ON A.id = B.id WHERE B.age > 25"
        self.assertFalse(is_eq(sql1, sql2))

    def test_full_outer_join(self):
        sql1 = "SELECT EMP.name FROM DEPT FULL OUTER JOIN EMP ON EMP.name = DEPT.name WHERE EMP.age > 25"
        sql2 = "SELECT EMP.name FROM EMP FULL OUTER JOIN DEPT ON EMP.name = DEPT.name WHERE NOT EMP.age <= 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_null1(self):
        sql1 = "SELECT E.name AS name FROM EMP AS E WHERE E.age IS NOT NULL AND NOT E.age > 25"
        sql2 = "SELECT name FROM EMP WHERE age <= 25 AND EMP.age IS NOT NULL"
        self.assertTrue(is_eq(sql1, sql2))

    def test_null2(self):
        sql1 = "SELECT name FROM EMP WHERE EMP.age IS NULL"
        sql2 = "SELECT name FROM EMP WHERE NOT EMP.age IS NOT NULL"
        self.assertTrue(is_eq(sql1, sql2))

    def test_agg_count1(self):
        sql1 = "SELECT COUNT(*), COUNT(name), id FROM EMP WHERE age < 30"
        sql2 = "SELECT COUNT(*), COUNT(name), id FROM EMP WHERE NOT age >= 30"
        self.assertTrue(is_eq(sql1, sql2))

    def test_agg_count2(self):
        sql1 = "SELECT COUNT(0), id FROM EMP WHERE age < 30"
        sql2 = "SELECT COUNT(*), id FROM EMP WHERE NOT age >= 30"
        self.assertTrue(is_eq(sql1, sql2))

    # def test_agg_count3(self):
    #     sql1 = "SELECT COUNT(0), COUNT(1), EMP.dept_id FROM EMP LEFT JOIN DEPT ON EMP.dept_id = DEPT.id WHERE age < 30"
    #     sql2 = "SELECT COUNT(0), COUNT(EMP.dept_id), EMP.dept_id FROM EMP LEFT JOIN DEPT ON EMP.dept_id = DEPT.id WHERE NOT age >= 30"
    #     self.assertFalse(is_eq(sql1, sql2))

    def test_agg_sum(self):
        sql1 = "SELECT SUM(age), SUM(id) FROM (SELECT name, age, id FROM EMP WHERE age > 25) WHERE age < 30"
        sql2 = "SELECT SUM(age), SUM(id) FROM (SELECT id, name, age FROM EMP WHERE age < 30) WHERE age > 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_agg_avg(self):
        sql1 = "SELECT AVG(age), AVG(id) FROM (SELECT name, age, id FROM EMP WHERE age > 25) WHERE age < 30"
        sql2 = "SELECT AVG(age), AVG(id) FROM (SELECT id, name, age FROM EMP WHERE age < 30) WHERE age > 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_agg_max(self):
        sql1 = "SELECT MAX(age), MAX(id) FROM (SELECT name, age, id FROM EMP WHERE age > 25) WHERE age < 30"
        sql2 = "SELECT MAX(age), MAX(id) FROM (SELECT id, name, age FROM EMP WHERE age < 30) WHERE age > 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_agg_min(self):
        sql1 = "SELECT MIN(age), MIN(id) FROM (SELECT name, age, id FROM EMP WHERE age > 25) WHERE age < 30"
        sql2 = "SELECT MIN(age), MIN(id) FROM (SELECT id, name, age FROM EMP WHERE age < 30) WHERE age > 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_group1(self):
        sql1 = "SELECT dept_id, COUNT(dept_id) AS dept_num FROM EMP WHERE age >= 25 GROUP BY dept_id"
        sql2 = "SELECT dept_id, COUNT(dept_id) AS dept_num FROM EMP WHERE NOT age < 25 GROUP BY dept_id"
        self.assertTrue(is_eq(sql1, sql2))

    def test_group2(self):
        sql1 = "SELECT dept_id, COUNT(dept_id) AS dept_num FROM EMP WHERE age >= 25 GROUP BY dept_id, age HAVING COUNT(age) > 10"
        sql2 = "SELECT dept_id, COUNT(dept_id) AS dept_num FROM EMP WHERE NOT age < 25 GROUP BY age, dept_id HAVING NOT COUNT(age) <= 10"
        self.assertTrue(is_eq(sql1, sql2))

    def test_group3(self):
        schema = {
            "Views": {"PKeys": [], "article_id": "int", "author_id": "int", "viewer_id": "int", "view_date": "date"}}
        sql1 = "SELECT DISTINCT AUTHOR_ID AS ID FROM VIEWS WHERE AUTHOR_ID = VIEWER_ID ORDER BY AUTHOR_ID"
        sql2 = "SELECT AUTHOR_ID AS ID FROM ( SELECT AUTHOR_ID, CASE WHEN AUTHOR_ID = VIEWER_ID THEN 1 ELSE 0 END AS OWN FROM VIEWS) T GROUP BY 1 HAVING SUM(OWN) >= 1 ORDER BY 1"
        self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_distinct1(self):
        sql1 = "SELECT DISTINCT dept_id, COUNT(age), COUNT(*) FROM EMP WHERE age > 25"
        sql2 = "SELECT DISTINCT dept_id, COUNT(*), COUNT(age) FROM EMP WHERE NOT age <= 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_distinct2(self):
        sql1 = "SELECT DISTINCT(dept_id), id FROM EMP WHERE age > 25"
        sql2 = "SELECT DISTINCT dept_id, id FROM EMP WHERE NOT age <= 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_distinct3(self):
        sql1 = "SELECT COUNT(DISTINCT(dept_id)), id FROM EMP WHERE age > 25"
        sql2 = "SELECT COUNT(DISTINCT dept_id), id FROM EMP WHERE NOT age <= 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_distinct4(self):
        sql1 = 'SELECT DISTINCT L1.num as ConsecutiveNums FROM Logs L1, Logs L2, Logs L3 WHERE L1.id = L2.id-1 AND L2.id = L3.id-1 and L1.num = L2.num and L2.num = L3.num'
        sql2 = 'SELECT DISTINCT l1.Num AS ConsecutiveNums FROM Logs l1 JOIN Logs l2 USING (Num) JOIN Logs l3 USING (Num) WHERE l1.Id + 1 = l2.Id AND l2.Id + 1 = l3.Id'
        schema = {'Logs': {'Id': 'int', 'Num': 'int'}}
        self.assertTrue(is_eq(sql1, sql2, schema))

    def test_distinct5(self):
        sql1 = 'select distinct author_id id from Views where author_id = viewer_id order by author_id'
        sql2 = 'select distinct author_id as id from Views where author_id = viewer_id order by 1'
        schema = {'Views': {'article_id': 'int', 'author_id': 'int', 'viewer_id': 'int', 'view_date': 'date'}}
        self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_distinct_count(self):
        sql1 = "SELECT COUNT(DISTINCT age) FROM EMP WHERE age > 25"
        sql2 = "SELECT COUNT(DISTINCT age) FROM EMP WHERE NOT age <= 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_distinct_avg(self):
        sql1 = "SELECT AVG(DISTINCT age), AVG(DISTINCT age-1) FROM EMP WHERE age > 25"
        sql2 = "SELECT AVG(DISTINCT age), AVG(DISTINCT age+1-2) FROM EMP WHERE NOT age <= 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_distinct_sum(self):
        sql1 = "SELECT SUM(DISTINCT age), SUM(DISTINCT age-1) FROM EMP WHERE age > 25"
        sql2 = "SELECT SUM(DISTINCT age), SUM(DISTINCT age+1-2) FROM EMP WHERE NOT age <= 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_distinct_max(self):
        sql1 = "SELECT MAX(DISTINCT age), MAX(DISTINCT age-1) FROM EMP WHERE age > 25"
        sql2 = "SELECT MAX(DISTINCT age), MAX(DISTINCT age+1-2) FROM EMP WHERE NOT age <= 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_distinct_min(self):
        sql1 = "SELECT MIN(DISTINCT age), MIN(DISTINCT age-1) FROM EMP WHERE age > 25"
        sql2 = "SELECT MIN(DISTINCT age), MIN(DISTINCT age+1-2) FROM EMP WHERE NOT age <= 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_orderby1(self):
        sql1 = "SELECT age FROM EMP ORDER BY AGE DESC"
        sql2 = "SELECT age FROM (SELECT * FROM EMP ORDER BY name ASC) ORDER BY AGE DESC"
        self.assertTrue(is_eq(sql1, sql2))

    def test_orderby2(self):
        sql1 = "SELECT dept_id, COUNT(dept_id) as COUNT_dept_id, COUNT(age) as COUNT_age FROM EMP GROUP BY 1, age ORDER BY 3"
        sql2 = "SELECT dept_id, COUNT(dept_id) as COUNT_dept_id, COUNT(age) as COUNT_age FROM EMP GROUP BY dept_id, age ORDER BY COUNT_age"
        self.assertTrue(is_eq(sql1, sql2))

    def test_orderby3(self):
        sql1 = "SELECT dept_id FROM (SELECT * FROM EMP ORDER BY age)"
        sql2 = "SELECT dept_id FROM (SELECT * FROM EMP) ORDER BY 1"
        self.assertFalse(is_eq(sql1, sql2))

    def test_orderby4(self):
        sql1 = "SELECT dept_id, age FROM (SELECT * FROM EMP ORDER BY dept_id, age)"  # ORDER BY age"
        sql2 = "SELECT dept_id, age FROM EMP"
        self.assertFalse(is_eq(sql1, sql2))

    def test_orderby5(self):
        sql1 = "SELECT dept_id, age FROM (SELECT * FROM EMP ORDER BY dept_id, age)"  # ORDER BY age"
        sql2 = "SELECT dept_id, age FROM EMP ORDER BY dept_id, age"
        self.assertTrue(is_eq(sql1, sql2))

    def test_in1(self):
        sql1 = "SELECT * FROM EMP WHERE age IN (SELECT AGE FROM EMP WHERE age > 25)"
        sql2 = "SELECT * FROM EMP WHERE NOT age <= 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_in2(self):
        sql1 = "SELECT age FROM EMP WHERE age IN (SELECT DISTINCT AGE FROM EMP WHERE age > 25)"
        sql2 = "SELECT age FROM EMP WHERE NOT age <= 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_is_null1(self):
        sql1 = "SELECT * FROM EMP WHERE age IS NOT NULL AND age IS NULL"
        sql2 = "SELECT * FROM EMP WHERE FALSE"
        self.assertTrue(is_eq(sql1, sql2))

    def test_is_null2(self):
        sql1 = "SELECT * FROM EMP WHERE age IS NULL"
        sql2 = "SELECT * FROM EMP WHERE age IS NULL"
        self.assertTrue(is_eq(sql1, sql2))

    def test_dimond(self):
        sql1 = "SELECT A.student_name AS member_A ,B.student_name AS member_B ,C.student_name AS member_C FROM SchoolA A INNER JOIN SchoolB B ON A.student_name <> B.student_name AND A.student_id <> B.student_id INNER JOIN SchoolC C ON C.student_name <> A.student_name AND C.student_name <> B.student_name AND C.student_id <> A.student_id AND C.student_id <> B.student_id"
        sql2 = "SELECT A.student_name AS member_A, B.student_name AS member_B, C.student_name AS member_C FROM SchoolA A, SchoolB B, SchoolC C WHERE A.student_id != B.student_id AND A.student_id != C.student_id AND B.student_id != C.student_id AND A.student_name != B.student_name AND A.student_name != C.student_name AND B.student_name != C.student_name"
        schema = {'SchoolA': {'student_id': 'int', 'student_name': 'varchar'},
                  'SchoolB': {'student_id': 'int', 'student_name': 'varchar'},
                  'SchoolC': {'student_id': 'int', 'student_name': 'varchar'}}
        self.assertTrue(is_eq(sql1, sql2, schema))

    # def test_asterisk_with_table_prefix(self):
    #     # TODO: over time
    #     sql1 = "select DISTINCT(X.id) as id, X.visit_date as visit_date, X.people as people from Stadium as X, (select B.id as id from Stadium as A, Stadium as B, Stadium as C where A.people >= 100 and B.people >= 100 and C.people >= 100 and A.id = (B.id - 1) and C.id = (B.id + 1)) as Y where (X. id = Y.id or X.id + 1 = Y.id or X.id - 1 = Y.id) order by X.id"
    #     sql2 = "select DISTINCT(X.id) as id, X.visit_date as visit_date, X.people as people from Stadium as X, (select B.id as id from Stadium as A, Stadium as B, Stadium as C where A.people >= 100 and B.people >= 100 and C.people >= 100 and A.id = (B.id - 1) and C.id = (B.id + 1)) as Y where (X. id = Y.id or X.id + 1 = Y.id or X.id - 1 = Y.id) order by X.id"
    #     self.assertTrue(is_eq(sql1, sql2, schema={'stadium': {'visit_date': 'date', 'id': 'int', 'people': 'int'}}))

    def test_string1(self):
        sql1 = """SELECT Product_id FROM `Products` WHERE low_fats = 'Y' and recyclable ='Y' GROUP BY product_id"""
        sql2 = """SELECT p.product_id FROM Products p WHERE p.low_fats = 'Y' AND p.recyclable = 'Y'"""
        schema = {
            'Products': {'product_id': 'int', 'low_fats': 'enum,Y,N', 'recyclable': 'enum,Y,N'}}
        self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_string2(self):
        sql1 = """select extra as report_reason, count(extra) as report_count from (select distinct post_id, action, extra from Actions where action = 'report' and action_date = '2019-07-04' ) as T group by extra having report_count > 0"""
        sql2 = """select extra as report_reason, count(extra) as report_count from (select distinct post_id,extra from Actions where action_date='2019-07-04' and action='report' )A group by A.extra having report_count > 0"""
        schema = {'Actions': {'user_id': 'int', 'post_id': 'int', 'action_date': 'date',
                              'action': 'enum,view,like,reaction,comment,report,share',
                              'extra': 'varchar'}}
        self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_expression1(self):
        sql1 = "SELECT (name+age)*age, SUM(name*age) FROM EMP WHERE name*age > 0"
        sql2 = "SELECT (name+age)*age, SUM(name*age) FROM EMP WHERE NOT name*age <= 0"
        self.assertTrue(is_eq(sql1, sql2))

    def test_expression2(self):
        sql1 = 'SELECT event_day AS day, emp_id, SUM((out_time - in_time)) AS total_time FROM Employees GROUP BY event_day, emp_id'
        sql2 = 'SELECT event_day AS day, emp_id, SUM(out_time) - SUM(in_time) AS total_time FROM Employees GROUP BY 1,2'
        schema = {'Employees': {'emp_id': 'int', 'event_day': 'date', 'in_time': 'int', 'out_time': 'int'}}
        self.assertFalse(is_eq(sql1, sql2, schema=schema))

    def test_expression3(self):
        sql1 = 'SELECT name AS WAREHOUSE_NAME, SUM(units*Width* Length* Height) AS VOLUME FROM Warehouse LEFT JOIN Products ON Warehouse.product_id = Products.product_id GROUP BY name'
        sql2 = 'SELECT name AS WAREHOUSE_NAME, sum(units*(Width*Length*Height)) AS VOLUME FROM Warehouse JOIN Products ON Products.product_id=Warehouse.product_id GROUP BY name'
        schema = {
            'Warehouse': {'name': 'varchar', 'product_id': 'int', 'units': 'int'},
            'Products': {'product_id': 'int', 'product_name': 'varchar', 'Width': 'int', 'Length': 'int',
                         'Height': 'int'}
        }
        self.assertFalse(is_eq(sql1, sql2, schema=schema))

    def test_expression4(self):
        sql1 = """SELECT DISTINCT C.customer_id, C.customer_name FROM Customers C JOIN Orders O ON C.customer_id = O.customer_id WHERE C.customer_id in (SELECT D.customer_id from Customers D JOIN Orders E on D.customer_id = E.customer_id WHERE E.product_name= 'A') AND C.customer_id in (SELECT D.customer_id from Customers D JOIN Orders E on D.customer_id = E.customer_id WHERE E.product_name= 'B') AND C.customer_id not in (SELECT D.customer_id from Customers D JOIN Orders E on D.customer_id = E.customer_id WHERE E.product_name= 'C') ORDER BY C.customer_id"""
        sql2 = "SELECT c.customer_id, c.customer_name FROM Customers c JOIN Orders o USING(customer_id) GROUP BY c.customer_id HAVING SUM(o.product_name = 'A') > 0 AND SUM(o.product_name = 'B') > 0 AND SUM(o.product_name = 'C') = 0"
        schema = {'Customers': {'customer_id': 'int', 'customer_name': 'varchar'},
                  'Orders': {'order_id': 'int', 'customer_id': None,
                             'product_name': 'varchar'}}
        self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_XXX2(self):
        sql1 = "SELECT Employee FROM ( SELECT Employee.Name as Employee, Employee.Salary as EmployeeSalary, Manager.ManagerId, Manager.Name as Manager, Manager.Salary as ManagerSalary FROM Employee as Manager , Employee as Employee WHERE Manager.Id = Employee.ManagerId ) AS A WHERE EmployeeSalary > ManagerSalary"
        sql2 = 'SELECT E1.Name as Employee FROM Employee E1 JOIN Employee E2 ON E1.ManagerId=E2.Id WHERe E1.Salary> E2.Salary'
        schema = {'Employee': {'Id': 'int', 'Name': 'varchar', 'Salary': 'int', 'ManagerId': 'int'}}
        self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_XXX3(self):
        sql1 = "SELECT A.student_name AS member_A, B.student_name AS member_B, C.student_name AS member_C FROM SchoolA A, SchoolB B, SchoolC C WHERE A.student_id != B.student_id AND A.student_name != B.student_name AND A.student_id != C.student_id AND A.student_name != C.student_name AND C.student_id != B.student_id AND C.student_name != B.student_name"
        sql2 = "SELECT a.student_name AS member_A, b.student_name AS member_B, c.student_name AS member_C FROM SchoolA AS a, SchoolB AS b, SchoolC AS c WHERE a.student_id != b.student_id AND a.student_id != c.student_id AND b.student_id != c.student_id AND a.student_name != b.student_name AND a.student_name != c.student_name AND b.student_name != c.student_name"
        schema = {'SchoolA': {'student_id': 'int', 'student_name': 'varchar'},
                  'SchoolB': {'student_id': 'int', 'student_name': 'varchar'},
                  'SchoolC': {'student_id': 'int', 'student_name': 'varchar'}}
        self.assertTrue(is_eq(sql1, sql2, schema=schema))

    # def test_XXX4(self):
    #     # ~50s -> 20s
    #     sql1 = 'SELECT I.invoice_id, C1.customer_name, I.price, COUNT(C2.contact_email) AS contacts_cnt, COUNT(C3.customer_name) AS trusted_contacts_cnt FROM Invoices I LEFT JOIN Customers C1 ON I.user_id = C1.customer_id LEFT JOIN Contacts C2 ON C2.user_id = C1.customer_id LEFT JOIN Customers C3 ON C3.customer_name = C2.contact_name GROUP BY I.invoice_id order by I.invoice_id'
    #     sql2 = 'SELECT a.invoice_id, b.customer_name, a.price, COUNT(c.user_id) AS contacts_cnt, COUNT(d.customer_name) AS trusted_contacts_cnt FROM Invoices a LEFT JOIN Customers b ON a.user_id = b.customer_id LEFT JOIN Contacts c ON b.customer_id = c.user_id LEFT JOIN Customers d ON d.customer_name = c.contact_name GROUP BY a.invoice_id, b.customer_name, a.price ORDER BY a.invoice_id'
    #     schema = {
    #         'Customers': {'customer_id': 'int', 'customer_name': 'varchar', 'email': 'varchar'},
    #         'Contacts': {'user_id': 'int', 'contact_email': 'varchar', 'contact_name': 'varchar'},
    #         'Invoices': {'invoice_id': 'int', 'user_id': None, 'price': 'int'}
    #     }
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_with1(self):
        sql1 = "WITH E AS (SELECT * FROM EMP), D (D_id, D_name) AS (SELECT id, name FROM DEPT) SELECT id, age, D_id, D_name FROM E, D"
        sql2 = "SELECT EMP.id, EMP.age, DEPT.id, DEPT.name FROM EMP, DEPT"
        self.assertTrue(is_eq(sql1, sql2))

    def test_case1(self):
        sql1 = "SELECT CASE WHEN age < 10 THEN age WHEN age < 20 THEN age - 10 ELSE age - 20 END, id FROM EMP"
        sql2 = "SELECT CASE WHEN age < 10 THEN age WHEN 10 <= age < 20 THEN age - 10 ELSE age - 20 END, id FROM EMP"
        self.assertTrue(is_eq(sql1, sql2))

    def test_case_agg1(self):
        # once the case clause contains inner AGG, it maps many to one
        sql1 = "SELECT CASE WHEN age < 10 THEN MAX(age) ELSE MAX(age - 20) END FROM EMP"
        sql2 = "SELECT CASE WHEN age < 10 THEN MAX(age) ELSE MAX(age - 10 - 10) END FROM EMP"
        self.assertTrue(is_eq(sql1, sql2))

    def test_case_agg2(self):
        # once the case clause contains inner AGG, it maps many to one
        sql1 = "SELECT SUM(CASE WHEN age < 10 THEN age ELSE age-20 END) FROM EMP"
        sql2 = "SELECT SUM(CASE WHEN age < 10 THEN age ELSE age-10-10 END) FROM EMP"
        self.assertTrue(is_eq(sql1, sql2))

    def test_case_in_where(self):
        # once the case clause contains inner AGG, it maps many to one
        sql1 = "SELECT COUNT(*) FROM EMP AS EMP WHERE CASE WHEN EMP.DEPTNO = 20 THEN 2 WHEN EMP.DEPTNO = 10 THEN 1 ELSE 3 END = 1"
        sql2 = "SELECT COUNT(*) FROM EMP AS EMP0 WHERE EMP0.DEPTNO = 10"
        schema = {
            'ACCOUNT': {'ACCTNO': 'int', 'TYPE': 'varchar', 'BALANCE': 'varchar'},
            'BONUS': {'ENAME': 'int', 'JOB': 'varchar', 'SAL': 'varchar', 'COMM': 'varchar'},
            'DEPT': {'DEPTNO': 'int', 'NAME': 'varchar'},
            'EMP': {'EMPNO': 'int', 'ENAME': 'varchar', 'JOB': 'varchar', 'MGR': 'int', 'HIREDATE': 'int',
                    'COMM': 'int', 'SAL': 'int', 'DEPTNO': 'int', 'SLACKER': 'int'},
        }
        self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_case_in_groupby1(self):
        # once the case clause contains inner AGG, it maps many to one
        sql1 = "SELECT FROM_ID, TO_ID FROM CALLS GROUP BY CASE WHEN 1 THEN FROM_ID ELSE TO_ID END, CASE WHEN 0 THEN FROM_ID ELSE TO_ID END"
        sql2 = "SELECT FROM_ID, TO_ID FROM CALLS GROUP BY 1,2"
        schema = {"Calls": {"from_id": "int", "to_id": "int", "duration": "int"}}
        self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_case_in_groupby2(self):
        # once the case clause contains inner AGG, it maps many to one
        sql1 = "SELECT CASE WHEN FROM_ID < TO_ID THEN FROM_ID ELSE TO_ID END AS PERSON1, CASE WHEN TO_ID > FROM_ID THEN TO_ID ELSE FROM_ID END AS PERSON2, COUNT(*) AS CALL_COUNT, SUM(DURATION) AS TOTAL_DURATION FROM CALLS GROUP BY CASE WHEN FROM_ID < TO_ID THEN FROM_ID ELSE TO_ID END, CASE WHEN TO_ID > FROM_ID THEN TO_ID ELSE FROM_ID END"
        sql2 = "SELECT CASE WHEN FROM_ID < TO_ID THEN FROM_ID ELSE TO_ID END AS PERSON1, CASE WHEN FROM_ID < TO_ID THEN TO_ID ELSE FROM_ID END AS PERSON2, COUNT(*) AS CALL_COUNT, SUM(DURATION) AS TOTAL_DURATION FROM CALLS GROUP BY 1,2"
        schema = {"Calls": {"from_id": "int", "to_id": "int", "duration": "int"}}
        self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_case_in_having(self):
        # once the case clause contains inner AGG, it maps many to one
        sql1 = "SELECT BUSINESS_ID FROM ( SELECT EVENT_TYPE, AVG(OCCURENCES) AS AVERAGE_OCC FROM EVENTS GROUP BY EVENT_TYPE) AS CTE JOIN EVENTS E2 ON CTE.EVENT_TYPE = E2.EVENT_TYPE WHERE E2.OCCURENCES > CTE.AVERAGE_OCC GROUP BY BUSINESS_ID HAVING COUNT(DISTINCT CTE.EVENT_TYPE) > 1"
        sql2 = "SELECT E.BUSINESS_ID FROM EVENTS E LEFT JOIN (SELECT EVENT_TYPE, AVG(OCCURENCES) AS AVG_OCC FROM EVENTS GROUP BY 1) AS T ON E.EVENT_TYPE = T.EVENT_TYPE GROUP BY 1 HAVING SUM(CASE WHEN E.OCCURENCES > T.AVG_OCC THEN 1 ELSE 0 END) > 1"
        schema = {"Events": {"business_id": "int", "event_type": "varchar", "occurences": "int"}}
        self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_case2(self):
        sql1 = "SELECT customer_id , SUM(case when t.visit_id IS NULL then 1 ELSE 0 END) as count_no_trans FROM Visits v LEFT JOIN Transactions t on v.visit_id = t.visit_id GROUP BY customer_id HAVING count_no_trans > 0"
        sql2 = "SELECT customer_id AS customer_id, count(1) AS count_no_trans FROM Visits v LEFT JOIN Transactions t ON v.visit_id = t.visit_id WHERE t.transaction_id is null GROUP BY customer_id"
        schema = {
            'Visits': {'visit_id': 'int', 'customer_id': 'int'},
            'Transactions': {'transaction_id': 'int', 'visit_id': 'int', 'amount': 'int'},
        }
        # such schema cannot support
        self.assertFalse(is_eq(sql1, sql2, schema=schema))

    def test_between1(self):
        sql1 = "SELECT id, age FROM EMP WHERE age BETWEEN 10 AND 30"
        sql2 = "SELECT id, age FROM EMP WHERE 10 <= age AND age <= 30"
        self.assertTrue(is_eq(sql1, sql2))

    def test_union_all1(self):
        sql1 = "SELECT * FROM EMP WHERE age >= 10 UNION ALL SELECT * FROM EMP WHERE age <= 30"
        sql2 = "SELECT * FROM EMP WHERE age <= 30 UNION ALL SELECT * FROM EMP WHERE age >= 10"
        self.assertTrue(is_eq(sql1, sql2))

    def test_union1(self):
        sql1 = "SELECT age, dept_id FROM EMP UNION SELECT age, dept_id FROM EMP"
        sql2 = "SELECT age, dept_id FROM (SELECT dept_id, age FROM EMP UNION SELECT dept_id, age FROM EMP) AS T"
        self.assertTrue(is_eq(sql1, sql2))

    def test_round1(self):
        sql1 = "SELECT round(age, 2) FROM EMP WHERE age > 25"
        sql2 = "SELECT round(age, 2) FROM EMP WHERE NOT age <= 25"
        self.assertTrue(is_eq(sql1, sql2))

    def test_round2(self):
        sql1 = "SELECT round(age-1, 2) FROM EMP WHERE age > 25"
        sql2 = "SELECT round(age-2+1, 2) FROM EMP WHERE NOT age <= 25"
        self.assertTrue(is_eq(sql1, sql2))

    # def test_round3(self):
    #     # TODO: cannot solve this query, because we only encoding Round as an uninterpreted function
    #     sql1 = "SELECT round(age-1, 2)-1 FROM EMP WHERE age > 25"
    #     sql2 = "SELECT round(age-1, 2)-1 FROM EMP WHERE NOT age <= 25"
    #     self.assertTrue(is_eq(sql1, sql2))

    def test_COALESCE1(self):
        # if age is NULL but name is not NULL, this might be false
        sql1 = "SELECT COALESCE(NULL, age) FROM EMP"
        sql2 = "SELECT COALESCE(age, name) FROM EMP"
        self.assertFalse(is_eq(sql1, sql2))

    def test_COALESCE2(self):
        sql1 = "SELECT COALESCE(COUNT(*) - COUNT(age), name) FROM EMP"
        sql2 = "SELECT COALESCE(NULL, COUNT(*) - COUNT(age)) FROM EMP"
        self.assertTrue(is_eq(sql1, sql2))

    def test_COALESCE3(self):
        sql1 = "SELECT COALESCE(NULL, ROUND(COUNT(age) - AVG(age),2), 0) FROM EMP"
        sql2 = "SELECT COALESCE(ROUND(COUNT(age) - AVG(age),2), name) FROM EMP"
        self.assertTrue(is_eq(sql1, sql2))

    def test_EXCEPT1(self):
        sql1 = "SELECT age FROM EMP EXCEPT ALL SELECT name FROM EMP"
        sql2 = "SELECT age FROM EMP EXCEPT ALL SELECT name FROM EMP"
        self.assertTrue(is_eq(sql1, sql2))

    def test_EXCEPT2(self):
        sql1 = "SELECT age FROM EMP EXCEPT ALL SELECT age FROM EMP"
        sql2 = "SELECT age FROM EMP EXCEPT ALL SELECT age FROM EMP"
        self.assertTrue(is_eq(sql1, sql2))

    # we cannot handle correlated subquery
    # def test_correlated(self):
    #     sql1 = "SELECT * FROM EMP AS E WHERE (SELECT COUNT(id) FROM DEPT WHERE id == E.dept_id) > 0"
    #     sql2 = "WITH E AS (SELECT * FROM EMP) SELECT * FROM E WHERE (SELECT COUNT(id) FROM DEPT WHERE id == E.dept_id) > 0"
    #     self.assertTrue(is_eq(sql1, sql2))

    # def test_file0(self):
    #     sql1 = "SELECT A.extra AS report_reason, COUNT(DISTINCT(post_id)) AS report_count FROM Actions AS A WHERE action_date = \"2019-07-04\" AND A.action = \"report\" GROUP BY extra"
    #     sql2 = "SELECT a.extra AS report_reason, COUNT(DISTINCT post_id) AS report_count FROM Actions AS a WHERE action_date = \"2019-07-04\" AND action = 'report' GROUP BY report_reason"
    #     schema = {"Actions": {"user_id": "int", "post_id": "int", "action_date": "date",
    #                           "action": "enum,view,like,reaction,comment,report,share", "extra": "varchar"}}
    #     self.assertFalse(is_eq(sql1, sql2, schema=schema))
    #
    # def test_file1(self):
    #     sql1 = "SELECT P.project_id, E.employee_id FROM Project P JOIN Employee E ON P.employee_id = E.employee_id JOIN( SELECT P.project_id, MAX(E.experience_years) as exp FROM Project P, Employee E WHERE P.employee_id = E.employee_id GROUP BY P.project_id) AS T on E.experience_years = T.exp AND P.project_id = T.project_id"
    #     sql2 = "SELECT P.project_id, P.employee_id FROM Project P LEFT JOIN Employee E ON P.employee_id = E.employee_id WHERE (P.project_id, E.experience_years) IN (SELECT P.project_id, MAX(E.experience_years) max_exp FROM Project P LEFT JOIN Employee E ON P.employee_id = E.employee_id GROUP BY P.project_id)"
    #     schema = {"Project": {"project_id": "int", "employee_id": 'int'},
    #               "Employee": {"employee_id": "int", "name": "varchar", "experience_years": "int"}}
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    # def test_file2(self):
    #     sql1 = "SELECT FirstName, LastName, Address.City, Address.State FROM Person LEFT JOIN Address ON Address.PersonId=Person.PersonId"
    #     sql2 = "SELECT Person.FirstName AS \"FirstName\", Person.LastName AS \"LastName\", Address.City AS \"City\", Address.State AS \"State\" FROM Person LEFT JOIN Address ON Person.PersonId = Address.PersonId"
    #     schema = {"Person": {"PersonId": "int", "FirstName": "varchar", "LastName": "varchar"},
    #               "Address": {"AddressId": "int", "PersonId": 'int', "City": "varchar", "State": "varchar"}}
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    # def test_file3(self):
    #     sql1 = "SELECT DISTINCT AUTHOR_ID AS ID FROM VIEWS WHERE AUTHOR_ID=VIEWER_ID ORDER BY AUTHOR_ID"
    #     sql2 = "SELECT DISTINCT author_id AS id FROM Views AS v WHERE author_id = viewer_id ORDER BY id"
    #     schema = {"Views": {"article_id": "int", "author_id": "int", "viewer_id": "int", "view_date": "date"}}
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    # def test_file4(self):
    #     sql1 = "SELECT B.Name AS Department, A.Name AS Employee, A.Salary AS Salary FROM Employee A INNER JOIN Department B ON A.DepartmentId = B.Id WHERE 3 > ( SELECT count(DISTINCT(e2.Salary)) from Employee e2 Where e2.Salary > A.Salary AND A.DepartmentId = e2.DepartmentId )"
    #     sql2 = "SELECT D.Name AS Department , E.Name AS Employee , E.Salary as Salary FROM Employee AS E INNER JOIN Department AS D ON E.DepartmentId = D.Id WHERE 3 > (SELECT COUNT(DISTINCT E2.Salary) FROM Employee as E2 WHERE E2.Salary > E.Salary AND E.DepartmentId= E2.DepartmentId)"
    #     schema = {
    #         "Employee": {"Id": "int", "DepartmentId": None, "Name": "varchar", "Salary": "int"},
    #         "Department": {"Id": "int", "Name": "varchar"}
    #     }
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    # def test_file5(self):
    #     sql1 = "SELECT A.SALE_DATE, A.SOLD_NUM-B.SOLD_NUM AS DIFF FROM SALES A INNER JOIN SALES B ON A.SALE_DATE=B.SALE_DATE AND A.FRUIT='apples' AND B.FRUIT='oranges' ORDER BY A.SALE_DATE"
    #     sql2 = "SELECT A.SALE_DATE, A.SOLD_NUM-B.SOLD_NUM AS DIFF FROM SALES A INNER JOIN SALES B ON A.SALE_DATE=B.SALE_DATE WHERE A.FRUIT='apples' AND B.FRUIT='oranges' ORDER BY A.SALE_DATE"
    #     schema = {"Sales": {"sale_date": "date", "fruit": "enum,apples,oranges", "sold_num": "int"}}
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    def test_file6(self):
        sql1 = "SELECT P.name, IFNULL(SUM(I.rest),0) AS rest, IFNULL(SUM(I.paid),0) AS paid, IFNULL(SUM(I.canceled),0) AS canceled, IFNULL(SUM(I.refunded),0) AS refunded FROM Product P LEFT JOIN Invoice I ON P.product_id=I.product_id GROUP BY 1 ORDER BY 1"
        sql2 = "SELECT DISTINCT p.name, SUM(rest) AS rest, SUM(paid) AS paid, SUM(canceled) AS canceled, SUM(refunded) AS refunded FROM Product AS p JOIN Invoice AS i USING(product_id) GROUP BY p.product_id ORDER BY p.name"
        schema = {
            "Product": {"product_id": "int", "name": "varchar"},
            "Invoice": {"invoice_id": "int", "product_id": None, "rest": "int", "paid": "int", "canceled": "int",
                        "refunded": "int"}
        }
        self.assertTrue(is_eq(sql1, sql2, schema=schema))

    #
    # def test_file8(self):
    #     sql1 = "with temp1 as( SELECT event_type, AVG(occurences) as ave FROM Events GROUP BY event_type ) SELECT e.business_id FROM Events as e JOIN temp1 as t ON e.event_type = t.event_type GROUP BY e.business_id HAVING SUM(IF(e.occurences > t.ave, 1,0)) > 1"
    #     sql2 = "SELECT BUSINESS_ID FROM ( SELECT EVENT_TYPE, AVG(OCCURENCES) AS AVERAGE_OCC FROM EVENTS GROUP BY EVENT_TYPE) AS CTE JOIN EVENTS E2 ON CTE.EVENT_TYPE = E2.EVENT_TYPE WHERE E2.OCCURENCES > CTE.AVERAGE_OCC GROUP BY BUSINESS_ID HAVING COUNT(DISTINCT CTE.EVENT_TYPE) > 1"
    #     schema = {"Events": {"business_id": "int", "event_type": "varchar", "occurences": "int"}}
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    # def test_file13(self):
    #     sql1 = "SELECT IFNULL(ROUND((COUNT(DISTINCT d1.delivery_id) / COUNT(DISTINCT d.delivery_id)) * 100, 2), 0) AS immediate_percentage FROM delivery d, (SELECT delivery_id FROM delivery WHERE order_date = customer_pref_delivery_date) d1"
    #     sql2 = "SELECT ROUND( SUM( order_date = customer_pref_delivery_date )/COUNT(*)*100, 2) AS immediate_percentage FROM Delivery AS d1"
    #     schema = {"Delivery": {"delivery_id": "int", "customer_id": "int", "order_date": "date",
    #                            "customer_pref_delivery_date": "date"}}
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    # def test_file15(self):
    #     sql1 = "SELECT  product_id FROM Products WHERE low_fats = 'Y' AND recyclable = 'Y'"
    #     sql2 = "SELECT PRODUCT_ID FROM PRODUCTS WHERE LOW_FATS = 'Y' AND RECYCLABLE = 'Y'"
    #     schema = {"Products": {"product_id": "int", "low_fats": "enum,Y,N", "recyclable": "enum,Y,N"}}
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    # def test_file19(self):
    #     sql1 = "SELECT DISTINCT A.Num as ConsecutiveNums FROM Logs A LEFT JOIN Logs B on A.id = B.id-1 LEFT JOIN Logs C on A.id = C.id-2 WHERE A.Num = B.num And A.num = C.num"
    #     sql2 = "SELECT DISTINCT L1.Num AS ConsecutiveNums FROM Logs AS L1, Logs AS L2, Logs AS L3 WHERE L1.Id = L2.Id - 1 AND L2.Id = L3.Id - 1 AND L1.Num = L2.Num AND L2.Num = L3.Num"
    #     schema = {"Logs": {"Id": "int", "Num": "int"}}
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    # def test_file20(self):
    #     sql1 = "SELECT * , CASE WHEN x+y>z AND y+z>x AND z+x>y THEN 'Yes' ELSE 'No' END as triangle FROM triangle"
    #     sql2 = "SELECT *, (CASE WHEN (x + y > z) AND (x + z > y) AND (y + z > x) THEN 'Yes' ELSE 'No' END) AS triangle FROM triangle"
    #     schema = {"triangle": {"x": "int", "y": "int", "z": "int"}}
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    # def test_file23(self):
    #     sql1 = "SELECT DISTINCT customer_id FROM Customer GROUP BY 1 HAVING COUNT(DISTINCT product_key) = (SELECT COUNT(DISTINCT product_key) FROM Product)"
    #     sql2 = "SELECT DISTINCT customer_id FROM customer GROUP BY 1 HAVING COUNT(DISTINCT product_key) = (SELECT COUNT(*) FROM Product)"
    #     schema = {"Customer": {"customer_id": "int", "product_key": None}, "Product": {"product_key": "int"}}
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    # def test_file40(self):
    #     sql1 = "SELECT (CASE WHEN from_id < to_id THEN from_id ELSE to_id END) AS person1, (CASE WHEN from_id < to_id THEN to_id ELSE from_id END) AS person2, COUNT(*) AS call_count, SUM(duration) AS total_duration FROM Calls GROUP BY person1, person2"
    #     sql2 = "SELECT (CASE WHEN from_id < to_id THEN from_id ELSE to_id END) AS person1, (CASE WHEN from_id < to_id THEN to_id ELSE from_id END) AS person2, COUNT(duration) as call_count, SUM(duration) AS total_duration FROM Calls GROUP BY 1,2"
    #     schema = {"Calls": {"from_id": "int", "to_id": "int", "duration": "int"}}
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    # def test_file43(self):
    #     sql1 = "SELECT DISTINCT A.product_id, B.price AS store1, C.price AS store2, D.price AS store3 FROM Products AS A LEFT JOIN Products AS B ON A.product_id = B.product_id AND B.store = 'store1' LEFT JOIN Products AS C ON A.product_id = C.product_id AND C.store = 'store2' LEFT JOIN Products AS D ON A.product_id = D.product_id AND D.store = 'store3'"
    #     sql2 = "SELECT DISTINCT DISTINCT product_id, MAX(CASE WHEN store = 'store1' THEN price END) AS store1, MAX(CASE WHEN store = 'store2' THEN price END) AS store2, MAX(CASE WHEN store = 'store3' THEN price END) AS store3 FROM products GROUP BY 1"
    #     schema = {"Products": {"product_id": "int", "store": "enum,store1,store2,store3", "price": "int"}}
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    # def test_file47(self):
    #     sql1 = "SELECT A.student_id, A.student_name, B.subject_name, ( SELECT COUNT(*) FROM Examinations C WHERE A.student_id = C.student_id AND B.subject_name = C.subject_name ) AS attended_exams FROM Students A JOIN Subjects B ORDER BY A.student_id, B.subject_name"
    #     sql2 = "SELECT S.STUDENT_ID, S.STUDENT_NAME, SUB.SUBJECT_NAME, COUNT(EX.SUBJECT_NAME) AS ATTENDED_EXAMS FROM STUDENTS S CROSS JOIN SUBJECTS SUB LEFT JOIN EXAMINATIONS EX USING (STUDENT_ID, SUBJECT_NAME) GROUP BY S.STUDENT_ID, S.STUDENT_NAME, SUB.SUBJECT_NAME ORDER BY S.STUDENT_ID, S.STUDENT_NAME"
    #     schema = {"Students": {"student_id": "iznt", "student_name": "varchar"},
    #               "Subjects": {"subject_name": "varchar"},
    #               "Examinations": {"student_id": None, "subject_name": None}}
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    # def test_file52(self):
    #     sql1 = "SELECT A.machine_id, ROUND(AVG(B.timestamp - A.timestamp), 3) AS processing_time FROM Activity A JOIN Activity B ON A.machine_id = B.machine_id AND A.process_id = B.process_id AND A.activity_type = 'start' AND B.activity_type = 'end' GROUP BY A.machine_id"
    #     sql2 = "SELECT a.machine_id,ROUND(SUM(a.end_time-a.start_time)/COUNT(a.process_id),3) AS processing_time FROM (SELECT machine_id,process_id, MAX(CASE WHEN activity_type = 'start' THEN timestamp END) AS start_time, MAX(CASE WHEN activity_type = 'end' THEN timestamp END) AS end_time FROM Activity GROUP BY machine_id,process_id) a GROUP BY a.machine_id"
    #     schema = {"Activity": {"machine_id": "int", "process_id": "int", "activity_type": "enum,start,end",
    #                            "timestamp": "numeric"}}
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    # def test_file53(self):
    #     sql1 = "SELECT A.USER_ID AS buyer_id, A.JOIN_DATE, COUNT(ORDER_ID) AS orders_in_2019 FROM USERS AS A LEFT JOIN ( SELECT ORDER_ID, BUYER_ID FROM ORDERS WHERE order_date>'2018-12-31' AND order_date<'2020-01-01' ) AS B ON A.USER_ID = B.BUYER_ID GROUP BY A.USER_ID, A.JOIN_DATE"
    #     sql2 = "SELECT U.user_id AS buyer_id, U.join_date, COUNT(O.item_id) as orders_in_2019 FROM Users U LEFT JOIN Orders O ON U.user_id = O.buyer_id AND LEFT(O.order_date,4) = 2019 GROUP BY 1"
    #     schema = {"Users": {"user_id": "int", "join_date": "date"},
    #               "Orders": {"order_id": "int", "item_id": None, "buyer_id": None, "seller_id": None,
    #                          "order_date": "date"}, "Items": {"item_id": "int"}}
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))

    # calcite
    # def test_cast1(self):
    #     sql1 = "SELECT CAST(TIME '12:34:56' AS TIMESTAMP(0)) FROM EMP AS EMP"
    #     sql2 = "SELECT CAST(TIME '12:34:56' AS TIMESTAMP(0)) FROM EMP AS EMP0"
    #     schema = {
    #         'ACCOUNT': {'ACCTNO': 'int', 'TYPE': 'varchar', 'BALANCE': 'varchar'},
    #         'BONUS': {'ENAME': 'int', 'JOB': 'varchar', 'SAL': 'varchar', 'COMM': 'varchar'},
    #         'DEPT': {'DEPTNO': 'int', 'NAME': 'varchar'},
    #         'EMP': {'EMPNO': 'int', 'ENAME': 'varchar', 'JOB': 'varchar', 'MGR': 'int', 'HIREDATE': 'int',
    #                 'COMM': 'int', 'SAL': 'int', 'DEPTNO': 'int', 'SLACKER': 'int'},
    #     }
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    # def test_cast2(self):
    #     sql1 = "SELECT DEPT.DEPTNO, CAST(DEPT.DEPTNO AS INTEGER) FROM DEPT AS DEPT ORDER BY CAST(DEPT.DEPTNO AS INTEGER) OFFSET 1 ROWS"
    #     sql2 = "SELECT t3.DEPTNO, CAST(t3.DEPTNO AS INTEGER) FROM (SELECT * FROM DEPT AS DEPT0 ORDER BY DEPT0.DEPTNO OFFSET 1 ROWS) AS t3"
    #     schema = {
    #         'ACCOUNT': {'ACCTNO': 'int', 'TYPE': 'varchar', 'BALANCE': 'varchar'},
    #         'BONUS': {'ENAME': 'int', 'JOB': 'varchar', 'SAL': 'varchar', 'COMM': 'varchar'},
    #         'DEPT': {'DEPTNO': 'int', 'NAME': 'varchar'},
    #         'EMP': {'EMPNO': 'int', 'ENAME': 'varchar', 'JOB': 'varchar', 'MGR': 'int', 'HIREDATE': 'int',
    #                 'COMM': 'int', 'SAL': 'int', 'DEPTNO': 'int', 'SLACKER': 'int'},
    #     }
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    # def test_cast3(self):
    #     sql1 = "SELECT DEPT.DEPTNO, CAST(DEPT.DEPTNO AS DOUBLE) FROM DEPT AS DEPT ORDER BY CAST(DEPT.DEPTNO AS DOUBLE) OFFSET 1 ROWS"
    #     sql2 = "SELECT t3.DEPTNO, CAST(t3.DEPTNO AS DOUBLE) FROM (SELECT * FROM DEPT AS DEPT0 ORDER BY DEPT0.DEPTNO OFFSET 1 ROWS) AS t3"
    #     schema = {
    #         'ACCOUNT': {'ACCTNO': 'int', 'TYPE': 'varchar', 'BALANCE': 'varchar'},
    #         'BONUS': {'ENAME': 'int', 'JOB': 'varchar', 'SAL': 'varchar', 'COMM': 'varchar'},
    #         'DEPT': {'DEPTNO': 'int', 'NAME': 'varchar'},
    #         'EMP': {'EMPNO': 'int', 'ENAME': 'varchar', 'JOB': 'varchar', 'MGR': 'int', 'HIREDATE': 'int',
    #                 'COMM': 'int', 'SAL': 'int', 'DEPTNO': 'int', 'SLACKER': 'int'},
    #     }
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))
    #
    # def test_cast4(self):
    #     sql1 = "SELECT DEPT.DEPTNO, CAST(DEPT.DEPTNO AS VARCHAR(10)) FROM DEPT AS DEPT ORDER BY CAST(DEPT.DEPTNO AS VARCHAR(10)) OFFSET 1 ROWS"
    #     sql2 = "SELECT DEPT0.DEPTNO, CAST(DEPT0.DEPTNO AS VARCHAR(10)) FROM DEPT AS DEPT0 ORDER BY CAST(DEPT0.DEPTNO AS VARCHAR(10)) OFFSET 1 ROWS"
    #     schema = {
    #         'ACCOUNT': {'ACCTNO': 'int', 'TYPE': 'varchar', 'BALANCE': 'varchar'},
    #         'BONUS': {'ENAME': 'int', 'JOB': 'varchar', 'SAL': 'varchar', 'COMM': 'varchar'},
    #         'DEPT': {'DEPTNO': 'int', 'NAME': 'varchar'},
    #         'EMP': {'EMPNO': 'int', 'ENAME': 'varchar', 'JOB': 'varchar', 'MGR': 'int', 'HIREDATE': 'int',
    #                 'COMM': 'int', 'SAL': 'int', 'DEPTNO': 'int', 'SLACKER': 'int'},
    #     }
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_values1(self):
        sql1 = "SELECT t.EXPR$0 + t.EXPR$1 + t.EXPR$0 FROM (VALUES  (10, 1),  (30, 3)) AS t WHERE t.EXPR$0 + t.EXPR$1 > 50"
        sql2 = "SELECT * FROM (VALUES) AS t3"
        schema = {
            'ACCOUNT': {'ACCTNO': 'int', 'TYPE': 'varchar', 'BALANCE': 'varchar'},
            'BONUS': {'ENAME': 'int', 'JOB': 'varchar', 'SAL': 'varchar', 'COMM': 'varchar'},
            'DEPT': {'DEPTNO': 'int', 'NAME': 'varchar'},
            'EMP': {'EMPNO': 'int', 'ENAME': 'varchar', 'JOB': 'varchar', 'MGR': 'int', 'HIREDATE': 'int',
                    'COMM': 'int', 'SAL': 'int', 'DEPTNO': 'int', 'SLACKER': 'int'},
        }
        self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_values2(self):
        sql1 = "SELECT * FROM (SELECT * FROM (VALUES  (10, 1),  (30, 3)) AS t UNION ALL SELECT * FROM (VALUES  (20, 2)) AS t0) AS t1 WHERE t1.X + t1.Y > 30"
        sql2 = "SELECT * FROM (VALUES  (30, 3)) AS t3"
        schema = {
            'ACCOUNT': {'ACCTNO': 'int', 'TYPE': 'varchar', 'BALANCE': 'varchar'},
            'BONUS': {'ENAME': 'int', 'JOB': 'varchar', 'SAL': 'varchar', 'COMM': 'varchar'},
            'DEPT': {'DEPTNO': 'int', 'NAME': 'varchar'},
            'EMP': {'EMPNO': 'int', 'ENAME': 'varchar', 'JOB': 'varchar', 'MGR': 'int', 'HIREDATE': 'int',
                    'COMM': 'int', 'SAL': 'int', 'DEPTNO': 'int', 'SLACKER': 'int'},
        }
        self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_values3(self):
        sql1 = "SELECT t.EXPR$0 + t.EXPR$1 AS X, t.EXPR$1 AS B, t.EXPR$0 AS A FROM (VALUES  (10, 1),  (30, 7),  (20, 3)) AS t WHERE t.EXPR$0 - t.EXPR$1 < 21"
        sql2 = "SELECT * FROM (VALUES  (11, 1, 10),  (23, 3, 20)) AS t2"
        schema = {
            'ACCOUNT': {'ACCTNO': 'int', 'TYPE': 'varchar', 'BALANCE': 'varchar'},
            'BONUS': {'ENAME': 'int', 'JOB': 'varchar', 'SAL': 'varchar', 'COMM': 'varchar'},
            'DEPT': {'DEPTNO': 'int', 'NAME': 'varchar'},
            'EMP': {'EMPNO': 'int', 'ENAME': 'varchar', 'JOB': 'varchar', 'MGR': 'int', 'HIREDATE': 'int',
                    'COMM': 'int', 'SAL': 'int', 'DEPTNO': 'int', 'SLACKER': 'int'},
        }
        self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_intersect(self):
        sql1 = "SELECT * FROM (SELECT * FROM EMP AS EMP WHERE EMP.DEPTNO = 10 INTERSECT SELECT * FROM EMP AS EMP0 WHERE EMP0.DEPTNO = 20) AS t1 INTERSECT SELECT * FROM EMP AS EMP1 WHERE EMP1.DEPTNO = 30"
        sql2 = "SELECT * FROM EMP AS EMP2 WHERE EMP2.DEPTNO = 10 INTERSECT SELECT * FROM EMP AS EMP3 WHERE EMP3.DEPTNO = 20 INTERSECT SELECT * FROM EMP AS EMP4 WHERE EMP4.DEPTNO = 30"
        schema = {
            'ACCOUNT': {'ACCTNO': 'int', 'TYPE': 'varchar', 'BALANCE': 'varchar'},
            'BONUS': {'ENAME': 'int', 'JOB': 'varchar', 'SAL': 'varchar', 'COMM': 'varchar'},
            'DEPT': {'DEPTNO': 'int', 'NAME': 'varchar'},
            'EMP': {'EMPNO': 'int', 'ENAME': 'varchar', 'JOB': 'varchar', 'MGR': 'int', 'HIREDATE': 'int',
                    'COMM': 'int', 'SAL': 'int', 'DEPTNO': 'int', 'SLACKER': 'int'},
        }
        self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_if1(self):
        sql1 = "SELECT IF(500<1000, 'YES', 'NO') FROM EMP"
        sql2 = "SELECT IF(500>=1000, 'NO', 'YES') FROM EMP"
        self.assertTrue(is_eq(sql1, sql2))

    def test_if2(self):
        sql1 = "SELECT IF(0, COUNT(*), 1+1) FROM EMP"
        sql2 = "SELECT IF(0, COUNT(*), 2) FROM EMP"
        self.assertTrue(is_eq(sql1, sql2))

    def test_ifnull1(self):
        sql1 = "SELECT IFNULL(NULL, 'NO') FROM EMP"
        sql2 = "SELECT IFNULL('NO', 'YES') FROM EMP"
        self.assertTrue(is_eq(sql1, sql2))

    # def test_unsupported1(self):
    #     sql1 = "SELECT FIRSTNAME, LASTNAME, CITY, STATE FROM PERSON LEFT JOIN ADDRESS ON PERSON.PERSONID = ADDRESS.PERSONID"
    #     sql2 = "SELECT FIRSTNAME,LASTNAME, (SELECT CITY FROM ADDRESS WHERE PERSON.PERSONID=ADDRESS.PERSONID) AS CITY, (SELECT STATE FROM ADDRESS WHERE PERSON.PERSONID=ADDRESS.PERSONID) AS STATE FROM PERSON"
    #     schema = {
    #         "Person": {"PKeys": ["PersonId"], "PersonId": "int", "FirstName": "varchar", "LastName": "varchar"},
    #         "Address": {"PKeys": ["AddressId"], "AddressId": "int", "PersonId": None, "City": "varchar",
    #                     "State": "varchar"}
    #     }
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))

    # def test_unsupported2(self):
    #     sql1 = "SELECT CUSTOMER_ID FROM CUSTOMER GROUP BY CUSTOMER_ID HAVING COUNT(DISTINCT PRODUCT_KEY) = (SELECT COUNT(DISTINCT PRODUCT_KEY) FROM PRODUCT)"
    #     sql2 = "SELECT CUSTOMER_ID FROM CUSTOMER GROUP BY CUSTOMER_ID HAVING COUNT(DISTINCT PRODUCT_KEY) = (SELECT COUNT(PRODUCT_KEY) FROM PRODUCT)"
    #     schema = {
    #         "Customer": {"PKeys": ["customer_id"], "customer_id": "int", "product_key": None},
    #         "Product": {"PKeys": ["product_key"], "product_key": "int"}
    #     }
    #     self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_unsupported3(self):
        sql1 = "WITH DAILYAPPLE AS( SELECT SALE_DATE AS DATE, SUM(SOLD_NUM) AS NUM1 FROM SALES WHERE FRUIT = 'APPLES' GROUP BY SALE_DATE ), DAILYORANGES AS( SELECT SALE_DATE AS DATE, SUM(SOLD_NUM) AS NUM2 FROM SALES WHERE FRUIT = 'ORANGES' GROUP BY SALE_DATE ) SELECT DAILYAPPLE.DATE AS SALE_DATE, COALESCE(DAILYAPPLE.NUM1,0) - COALESCE(DAILYORANGES.NUM2,0) AS DIFF FROM DAILYAPPLE JOIN DAILYORANGES ON DAILYAPPLE.DATE = DAILYORANGES.DATE"
        sql2 = "SELECT SALE_DATE, SUM(CASE WHEN FRUIT = 'APPLES' THEN SOLD_NUM ELSE -SOLD_NUM END) AS DIFF FROM SALES GROUP BY SALE_DATE"
        schema = {
            "Sales": {"PKeys": ["sale_date", "fruit"],
                      "sale_date": "date", "fruit": "enum,apples,oranges", "sold_num": "int"}
        }
        self.assertTrue(is_eq(sql1, sql2, schema=schema))

    def test_unsupported4(self):
        sql1 = 'SELECT P.NAME, COALESCE(SUM(I.REST),0) AS REST, COALESCE(SUM(I.PAID),0) AS PAID, COALESCE(SUM(I.CANCELED),0) AS CANCELED, COALESCE(SUM(I.REFUNDED),0) AS REFUNDED FROM PRODUCT P LEFT JOIN INVOICE I ON P.PRODUCT_ID = I.PRODUCT_ID GROUP BY P.NAME ORDER BY P.NAME'
        sql2 = 'SELECT NAME, SUM(REST) AS REST, SUM(PAID) AS PAID, SUM(CANCELED) AS CANCELED, SUM(REFUNDED) AS REFUNDED FROM PRODUCT AS P JOIN INVOICE AS I ON P.PRODUCT_ID = I.PRODUCT_ID GROUP BY P.PRODUCT_ID, NAME ORDER BY NAME'
        schema = {
            "Product": {"PKeys": ["product_id"], "product_id": "int", "name": "varchar"},
            "Invoice": {"PKeys": ["invoice_id"], "invoice_id": "int", "product_id": None, "rest": "int", "paid": "int",
                        "canceled": "int", "refunded": "int"}
        }
        self.assertTrue(is_eq(sql1, sql2, schema=schema))
