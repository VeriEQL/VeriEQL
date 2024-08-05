# -*- coding: utf-8 -*-

import datetime
import itertools
import operator
import os.path
from collections import Counter

import mysql.connector
import ujson
import utils
import yaml
from tqdm import tqdm


class CounterexampleChecker:
    operator_map = {
        'gt': operator.gt,
        'gte': operator.ge,
        'lt': operator.lt,
        'lte': operator.le,
        'neq': operator.ne,
        'eq': operator.eq,
    }

    def __init__(self, config):
        self.config = config
        self.cnx = mysql.connector.connect(
            host=self.config['host'],
            user=self.config['user'],
            password=self.config['password']
        )
        cursor = self.cnx.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS {self.config['database']}")
        cursor.execute(f"CREATE DATABASE {self.config['database']}")
        cursor.close()
        self.cnx.close()

        self.cnx = mysql.connector.connect(
            host=self.config['host'],
            user=self.config['user'],
            password=self.config['password'],
            database=self.config['database']
        )
        self.cursor = self.cnx.cursor(buffered=True)
        # self.cursor.execute("SET GLOBAL sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));")

    def __enter__(self):
        return self

    def create_tables(self, statements):
        if isinstance(statements, dict):
            statements = statements['tables']
            for table, statement in statements.items():
                self.cursor.execute(statement)
        else:
            for statement in statements.split(';')[:-1]:
                self.cursor.execute(statement)
        self.cnx.commit()

    def run_query(self, query: str) -> list:
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def compare_query_results(self, q1: str, q2: str) -> bool:
        if 'ORDER BY' in q1 or 'ORDER BY' in q2:
            # list semantics
            return self.run_query(q1) == self.run_query(q2)
        else:
            # bag semantics
            return Counter(self.run_query(q1)) == Counter(self.run_query(q2))

    def check_database_integrity(self, constraints: list[dict]) -> bool:
        if constraints is None:
            return True

        for c in constraints:
            key = next(iter(c))
            match key:
                case 'primary':
                    columns = c[key]
                    if not isinstance(columns, list):
                        columns = [columns]
                    table = columns[0]['value'].split('__')[0]
                    columns = [col['value'].split('__')[1] for col in columns]

                    self.cursor.execute(f"SELECT * FROM {table}")
                    header = [a[0] for a in self.cursor.description]
                    rows = self.cursor.fetchall()
                    pk_indices = [header.index(col) for col in columns]
                    visited = []
                    for row in rows:
                        row_values = [row[index] for index in pk_indices]
                        if row_values in visited:
                            return False
                        visited.append(row_values)
                case 'foreign':
                    table = c[key][0]['value'].split('__')[0]
                    column = c[key][0]['value'].split('__')[1]
                    references_table = c[key][1]['value'].split('__')[0]
                    references_column = c[key][1]['value'].split('__')[1]

                    self.cursor.execute(f"SELECT * FROM {references_table}")
                    header = [a[0] for a in self.cursor.description]
                    fk_references_index = header.index(references_column)
                    rows = self.cursor.fetchall()
                    foreign_values = [row[fk_references_index] for row in rows]

                    self.cursor.execute(f"SELECT * FROM {table}")
                    header = [a[0] for a in self.cursor.description]
                    fk_index = header.index(column)
                    rows = self.cursor.fetchall()
                    for row in rows:
                        if row[fk_index] not in foreign_values:
                            return False
                case 'between':
                    table = c[key][0]['value'].split('__')[0]
                    column = c[key][0]['value'].split('__')[1]
                    lower_bound = c[key][1]
                    upper_bound = c[key][2]

                    self.cursor.execute(f"SELECT * FROM {table}")
                    header = [a[0] for a in self.cursor.description]
                    index = header.index(column)
                    rows = self.cursor.fetchall()
                    for row in rows:
                        if row[index] is None or not (lower_bound <= row[index] <= upper_bound):
                            return False
                case 'in':
                    table = c[key][0]['value'].split('__')[0]
                    column = c[key][0]['value'].split('__')[1]
                    subset = []
                    for val in c[key][1]:
                        if isinstance(val, dict):
                            subset.append(val['literal'])
                        else:
                            subset.append(val)

                    self.cursor.execute(f"SELECT * FROM {table}")
                    header = [a[0] for a in self.cursor.description]
                    index = header.index(column)
                    rows = self.cursor.fetchall()
                    for row in rows:
                        if not row[index] in subset:
                            return False
                case 'not_null':
                    table = c[key]['value'].split('__')[0]
                    column = c[key]['value'].split('__')[1]

                    self.cursor.execute(f"SELECT * FROM {table}")
                    header = [a[0] for a in self.cursor.description]
                    rows = self.cursor.fetchall()
                    not_null_index = header.index(column)
                    for row in rows:
                        if row[not_null_index] is None:
                            return False
                case 'gt' | 'gte' | 'lt' | 'lte' | 'neq' | 'eq':
                    table = c[key][0]['value'].split('__')[0]
                    column = c[key][0]['value'].split('__')[1]
                    compare_to = c[key][1]
                    if isinstance(compare_to, dict) and 'date' in compare_to:
                        compare_to = datetime.date(*map(int, compare_to['date'].split('-')))

                    self.cursor.execute(f"SELECT * FROM {table}")
                    header = [a[0] for a in self.cursor.description]
                    rows = self.cursor.fetchall()
                    index = header.index(column)
                    for row in rows:
                        if isinstance(compare_to, dict) and 'value' in c[key][1]:
                            compare_to = c[key][1]['value'].split('__')[1]
                            compare_to = row[header.index(compare_to)]

                        if key in {'neq', 'eq'}:
                            if all(value is not None for value in [row[index], compare_to]) and \
                                    not CounterexampleChecker.operator_map[key](row[index], compare_to):
                                return False
                        else:
                            if row[index] is None or \
                                    not CounterexampleChecker.operator_map[key](row[index], compare_to):
                                return False
                case 'inc':
                    table = c[key]['value'].split('__')[0]
                    column = c[key]['value'].split('__')[1]

                    self.cursor.execute(f"SELECT * FROM {table}")
                    header = [a[0] for a in self.cursor.description]
                    rows = self.cursor.fetchall()
                    index = header.index(column)
                    for row in rows:
                        if isinstance(compare_to, dict) and 'value' in c[key][1]:
                            compare_to = c[key][1]['value'].split('__')[1]
                            compare_to = row[header.index(compare_to)]

                        if key in {'neq', 'eq'}:
                            if all(value is not None for value in [row[index], compare_to]) and \
                                    not CounterexampleChecker.operator_map[key](row[index], compare_to):
                                return False
                        else:
                            if row[index] is None or not CounterexampleChecker.operator_map[key](row[index],
                                                                                                 compare_to):
                                return False
                case 'inc':
                    table = c[key]['value'].split('__')[0]
                    column = c[key]['value'].split('__')[1]
                    inc_index = header.index(column)
                    inc_values = [row[inc_index] for row in rows]
                    if not all(
                            i is not None and j is not None and j == i + 1 for i, j in zip(inc_values, inc_values[1:])):
                        return False
                case _:
                    raise Exception(f'Unknown integrity constraint type: {key}')
        return True

    def reset(self):
        self.__exit__()
        self.__init__(self.config)

    def __exit__(self, *args):
        self.cursor.execute(f"DROP DATABASE {self.config['database']}")
        self.cursor.close()
        self.cnx.close()


def check(config, lines, out_file, idx):
    writer = open(out_file, 'w')
    with CounterexampleChecker(config) as checker:
        total = 0
        spurious_same_result = []
        spurious_not_meet_ic = []
        for idx, line in tqdm(enumerate(lines), total=len(lines), desc=f"Process {idx:02d}"):
            if line['counterexample'] is not None:
                total += 1
                try:
                    counterexample = line['counterexample']
                    counterexample = '\n'.join(counterexample.split('\n')[:-3])
                    line['pair'][0], line['pair'][1] = map(
                        lambda query: query.replace("%Y", "%y").replace("%M", "%m").replace("%D", "%d"),
                        (line['pair'][0], line['pair'][1])
                    )

                    checker.create_tables(counterexample)
                    constraint = line['constraint']

                    if checker.compare_query_results(line['pair'][0], line['pair'][1]):
                        spurious_same_result.append(idx)
                        line['spurious_info'] = 'results are same'
                        print(ujson.dumps(line, ensure_ascii=False), file=writer)
                        # print('--------------------')
                        # print(line['counterexample'])
                        # print('--------------------')
                        # exit()
                    elif not checker.check_database_integrity(constraint):
                        spurious_not_meet_ic.append(idx)
                        line['spurious_info'] = 'I.C. error'
                        print(ujson.dumps(line, ensure_ascii=False), file=writer)
                except mysql.connector.errors.ProgrammingError as e:
                    # print(idx, e)
                    # print('--------------------')
                    # print(line['counterexample'])
                    # print('--------------------')
                    # exit()
                    line['spurious_info'] = str(e)
                    print(ujson.dumps(line, ensure_ascii=False), file=writer)
                except mysql.connector.errors.DataError as e:
                    # print(idx, e)
                    # print('--------------------')
                    # print(line['counterexample'])
                    # print('--------------------')
                    # exit()
                    line['spurious_info'] = str(e)
                    print(ujson.dumps(line, ensure_ascii=False), file=writer)
                except Exception as err:
                    # print('--------------------')
                    # print(line['counterexample'])
                    # print('--------------------')
                    line['spurious_info'] = str(err)
                    print(ujson.dumps(line, ensure_ascii=False), file=writer)
            checker.reset()
    writer.close()
    return total, spurious_same_result, spurious_not_meet_ic


def main(DIR, in_file):
    with open(os.path.join(os.path.dirname(__file__), 'mysql_config.yml'), 'r') as f:
        config = yaml.safe_load(f)

    from multiprocessing import Pool, cpu_count

    CORE_NUM = cpu_count()

    import shutil

    with open(in_file, 'r') as reader:
        lines = []
        for line in reader:
            line = ujson.loads(line)
            if line['counterexample'] is not None:
                lines.append(line)
    lines = list(utils.divide(lines, CORE_NUM))

    out_file_template = in_file[:in_file.rfind('.')] + '.badcase'
    print(out_file_template)
    out_files = [f'{out_file_template}{idx}' for idx in range(len(lines))]
    with Pool(CORE_NUM) as mpool:
        results = [
            mpool.apply_async(
                check,
                (
                    {
                        'host': config['host'],
                        'user': f"{config['user']}{idx}",
                        'password': config['password'],
                        'database': f"{config['database']}{idx}",
                    },
                    # config,
                    lines[idx], out_files[idx],
                    idx,
                )
            )
            for idx in range(len(lines))
        ]
        results = [res.get() for res in results]
        total, spurious_same_result, spurious_not_meet_ic = zip(*results)
        total = sum(total)
        spurious_same_result = list(itertools.chain(*spurious_same_result))
        spurious_not_meet_ic = list(itertools.chain(*spurious_not_meet_ic))

    with open(out_file_template, 'w') as writer:
        for file in out_files:
            with open(file, 'r') as reader:
                shutil.copyfileobj(reader, writer)
            os.remove(file)

    print(f'Total #counter-examples: {total}')
    print(f'Spurious (two queries have the same output) : #{len(spurious_same_result)}')
    print(f'Spurious (integrity constraints not met) : #{len(spurious_not_meet_ic)}')


if __name__ == '__main__':
    DIR = "experiments/2023_03_27/"
    in_file = f'{DIR}/calcite.out'
    main(DIR, in_file)
