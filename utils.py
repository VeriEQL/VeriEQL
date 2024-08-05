# -*- coding: utf-8 -*-

import ctypes
import datetime
import functools
import math
import os
import re
import time
import uuid

import ujson

from constants import (
    If,
    Or,
    And,
    Not,
    MIN_DATE,
    Z3_TRUE,
    Z3_FALSE,
)


def is_uninterpreted_func(func):
    # this function must be ahead of attributes
    from formulas.columns.base_column import FBaseColumn
    return isinstance(func, FBaseColumn) and func.uninterpreted_func is not None


def _MAX(*args):
    return functools.reduce(lambda x, y: If(x >= y, x, y), args)


def _MIN(*args):
    return functools.reduce(lambda x, y: If(x < y, x, y), args)


encode_same = lambda null1, null2, value1, value2: \
    Or(And(null1, null2), And(Not(null1), Not(null2), value1 == value2))

encode_equality = lambda null1, null2, value1, value2: \
    And(Not(null1), Not(null2), value1 == value2)

encode_inequality = lambda null1, null2, value1, value2: \
    And(Not(null1), Not(null2), value1 != value2)

encode_is_distinct_from = lambda null1, null2, value1, value2: \
    And(Or(null1, null2, value1 != value2), Or(Not(null1), Not(null2)))

encode_is_not_distinct_from = lambda null1, null2, value1, value2: \
    Or(Not(Or(value1 != value2, null1, null2)), And(null1, null2))


def simplify(formulas, operator, add_not: bool = False):
    if add_not:
        formulas = [Not(opd) for opd in formulas]
    return operator(*formulas)


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def uuid_hash():
    return __pos_hash__(uuid.uuid1().__str__().replace('-', ''))


def excutize_string(string):
    if isinstance(string, str):
        return string.strip().replace(' ', '_').replace(':', '_').replace('-', '_')
    else:
        return string


def read_schema_file(file):
    def _foreign_key_type(name, foreign_table):
        for pair in foreign_table['PKeys'] + foreign_table['FKeys'] + foreign_table['Others']:
            if str.upper(pair['Name']) == name:
                return pair['Type']

    schema = {}
    constraints = []
    with open(file, 'r') as reader:
        database = ujson.loads(reader.read())
        for db in database['Tables']:
            db['TableName'] = str.upper(db['TableName'])
            schema[db['TableName']] = {}
            if len(db['PKeys']) > 0:
                for keywords in db['PKeys']:
                    name = str.upper(keywords.get('Name', keywords.get('FName', None)))
                    schema[db['TableName']][name] = str.upper(keywords.get('Type', None))
                pkeys = [f"{db['TableName']}__{key}" for key in schema[db['TableName']].keys()]
                constraints.append({'primary': [{'value': key} for key in pkeys]})
            if len(db['FKeys']) > 0:
                for keywords in db['FKeys']:
                    name = str.upper(keywords.get('Name', keywords.get('FName', None)))
                    foreign_table = database['Tables'][int(keywords['PTable'])]
                    foreign_table['TableName'] = str.upper(foreign_table['TableName'])
                    constraints.append(
                        {'foreign': [
                            {'value': f"{db['TableName']}__{name}"},
                            {'value': f"{foreign_table['TableName']}__{str.upper(keywords['PName'])}"},
                        ]})
                    schema[db['TableName']][name] = _foreign_key_type(name, foreign_table)
            if len(db['Others']) > 0:
                for keywords in db['Others']:
                    name = str.upper(keywords.get('Name', keywords.get('FName', None)))
                    schema[db['TableName']][name] = str.upper(keywords.get('Type', None))
    return schema, constraints


def dedup_constraints(constraints):
    if len(constraints) == 0:
        return None
    outs = []
    for cons in constraints:
        if cons not in outs:
            outs.append(cons)
    return outs


def _line_num(reader):
    num = sum(1 for _ in reader)
    reader.seek(0)
    return num


def divide(lst, partitions):
    chunck_size = math.ceil(len(lst) / partitions)
    for i in range(0, len(lst), chunck_size):
        yield lst[i:i + chunck_size]


def safe_readline(f):
    pos = f.tell()
    while True:
        try:
            return f.readline()
        except UnicodeDecodeError:
            pos -= 1
            f.seek(pos)  # search where this character begins


def find_offsets(filename, num_chunks):
    with open(filename, "r", encoding="utf-8") as f:
        size = os.fstat(f.fileno()).st_size
        chunk_size = size // num_chunks
        offsets = [0 for _ in range(num_chunks + 1)]
        for i in range(1, num_chunks):
            f.seek(chunk_size * i)
            safe_readline(f)
            offsets[i] = f.tell()
        return offsets


def encode_concate_by_and(nulls, values):
    # NULL and false <=> false
    from formulas.expressions.expression_tuple import FExpressionTuple
    premise = And(
        Or(*nulls),  # contain NULL?
        # if(is_null?, no(not false, its true), not(v) = is false)
        Or(*[If(n, Z3_FALSE, Not(v)) for n, v in zip(nulls, values)])
    )
    return FExpressionTuple(
        NULL=If(premise, Z3_FALSE, simplify(nulls, operator=Or)),
        VALUE=If(premise, Z3_FALSE, And(*values)),
    )


def encode_concate_by_or(nulls, values):
    # NULL or true <=> true
    from formulas.expressions.expression_tuple import FExpressionTuple
    premise = And(
        Or(*nulls),  # contain NULL?
        # if(is_null?, no(not false, its true), v = is true)
        Or(*[If(n, Z3_FALSE, v) for n, v in zip(nulls, values)])
    )
    return FExpressionTuple(
        NULL=If(premise, Z3_FALSE, simplify(nulls, operator=Or)),
        VALUE=If(premise, Z3_TRUE, Or(*values)),
    )


class CodeSnippet(object):
    def __init__(self, code: str, docstring: str = None, docstring_first=False, code_string=None):
        self.code = code  # str or CodeSnippet itself
        self.docstring = '# ' + (docstring or '')
        self.docstring_first = docstring_first
        self._code_string = code_string if code_string is None else code_string.strip(
            '\n')  # only store codes which are TOOOOO LONG

    def __str__(self):
        code_string = str(self.code) if self._code_string is None else self._code_string
        if len(self.docstring) > 2:
            if self.docstring_first:
                return f'{self.docstring}\n{code_string}'
            else:
                return f'{code_string}  {self.docstring}'
        else:
            return f'{code_string}'

    def __repr__(self):
        return self.docstring


class ValuesTable():
    def __init__(self, name, rows, attributes=['X', 'Y', 'Z']):
        # why set X, Y, Z cuz for calcite dataset
        # only works for VALUES (XXX) in SQL query parsing
        self.name = name
        self.rows = rows
        self.attributes = attributes[:len(rows[0])]

    def __str__(self):
        return f'{self.name}=({self.attributes}, #{len(self.rows)}: {[[list(col.values())[0] for col in row] for row in self.rows]})'

    def __repr__(self):
        return self.__str__()


def is_date_format(date: str):
    return re.match(r'^[0-9]{2,4}[-|_|:|/][0-9]{1,2}[-|_|:|/][0-9]{1,2}(\s+[0-9]{1,2}:[0-9]{1,2}:[0-9]{1,2})?$',
                    date.strip()) is not None


def strptime_to_int(date: str):
    date = [unit for unit in re.split(r'-|_|:|/|\s+', date.strip())]
    if len(date) > 3:
        # print("We only consider date in the YYYY-MM-dd, and drop timestamp in hour/min/sec.")
        date = date[:3]
    year, month, day = date
    if len(year) < 4:
        year = '20'[:4 - len(year)] + year
    try:
        time = datetime.datetime(int(year), int(month), int(day))
    except Exception as err:
        from errors import NotSupportedError
        raise NotSupportedError(err)
    interval = time - MIN_DATE
    return interval.days + 1  # avoid bool('1970-01-01') == 0


def int_to_strptime(date: int):
    date = MIN_DATE + datetime.timedelta(days=date - 1)
    return str(date)[:10]


def __pos_hash__(var):
    if isinstance(var, str):
        # positive hash code
        return ctypes.c_size_t(hash(var)).value
    else:
        return hash(var)


def sort_key(file):
    base_file = os.path.basename(file)
    base_file = base_file[:base_file.index('.')]
    base_file = ''.join(char for char in base_file if str.isdigit(char))
    return int(base_file)


if __name__ == '__main__':
    print(int_to_strptime(1))
    # print(strptime_to_int('1970-01-01'))
    # print(is_date_format('17987'))
