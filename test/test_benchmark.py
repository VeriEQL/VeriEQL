import csv
import itertools
import os

from mo_parsing import ParseException
from mo_sql_parsing import parse

from environment import Environment

database = [
]


def is_eq(q1, q2, db):
    with Environment() as env:
        env.database_preprocess(db)

        query1 = env.parse_sql_query(q1)
        query2 = env.parse_sql_query(q2)

        formula1 = env.analyze(query1)
        formula2 = env.analyze(query2)

        return env.compare(formula1, formula2)


def keys(data, acc=None):
    if acc is None:
        acc = []

    if isinstance(data, dict):
        for k, v in data.items():
            acc.append(k)
            acc = keys(v, acc)
    elif isinstance(data, list):
        for x in data:
            if isinstance(x, dict):
                acc = keys(x, acc)
    return acc


def filter_benchmark(query: str) -> bool:
    try:
        query_ast = parse(query)
    except ParseException:
        return False

    supported_ops = ['select', 'from', 'value', 'name', 'where', 'select_distinct',
                     'gt', 'lt', 'gte', 'lte', 'eq', 'neq', 'and', 'or', 'not',
                     'inner join', 'join', 'cross join', 'natural join',
                     'left join', 'right join', 'left outer join', 'right outer join', 'on',
                     'count', 'sum', 'max', 'min', 'avg',
                     'groupby', 'orderby']
    benchmark_ops = keys(query_ast)
    return all(op in supported_ops for op in benchmark_ops)


def run_benchmark():
    benchmark_dir = os.path.join(os.path.dirname(__file__), '..', 'benchmark', 'labeled_queries')
    total = 0
    success = 0
    for filename in os.listdir(benchmark_dir):
        fpath = os.path.join(benchmark_dir, filename)
        if os.path.isfile(fpath):
            f = open(fpath)
            data = csv.reader(f, delimiter=',')
            queries = []
            for row in data:
                if row[1] == 'Y':
                    queries.append(row[5])
            queries = list(filter(filter_benchmark, queries))

            if len(queries) >= 2:
                for sql in itertools.combinations(queries, 2):
                    total += 1
                    try:
                        if is_eq(sql[0], sql[1], database):
                            success += 1
                    except:
                        pass
            break  # break here to only test queries in the first problem

    print(f"Total: {total}")
    print(f"Success: {success}")
    print(f"%: {(success / total) * 100}")


if __name__ == '__main__':
    run_benchmark()
