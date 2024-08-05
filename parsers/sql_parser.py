# -*- coding:utf-8 -*-

import re
from typing import (
    Dict,
    Union,
)

from mo_parsing import ParseException
from mo_sql_parsing import parse

from constants import (
    SQL_NULL,
    IS_TRUE,
    IS_FALSE,
    SPACE_STRING,
    DIALECT,
)
from errors import (
    ParserSyntaxError,
)
from logger import LOGGER
from utils import (
    is_date_format,
    ValuesTable,
)

TMP_PLACEHOLDER = "TEMPORARY_PLACEHOLDER"
NULL_REGEX = r'([a-zA-Z_\.\$]+\s+(<>|=|!=)\s+NULL)|(NULL\s+(<>|=|!=)\s+[a-zA-Z_\.\$]+)'
FROM_REGEX = r'FROM \([a-zA-Z0-9]+\)'
VALUES_REGEX = r'\(VALUES\s*\(\S+\s*\S*(\s*,\s*\S+\s*\S*)*\)(\s*,\s*\(\S+\s*\S*(\s*,\s*\S+\s*\S*)*\))*\)'
LIMIT_REGEX = r'LIMIT\s+\d+,\s*\d+'


def is_VALUES(value):
    # {'value': 'VALUES', 'name': XX}
    return isinstance(value, Dict) and value.get('value', False) == 'VALUES' and value.get('name', False)


def is_NULL(value):
    return value == {'value': TMP_PLACEHOLDER}


def parse_from_values(values, VALUE_TABLES):
    # FROM (VALUES (XX)) AS T
    if isinstance(values['name'], Dict):
        table_name = list(values['name'])[0]
        columns = values['name'][table_name]
        if isinstance(columns, str):
            columns = [columns]
        lines = []
        for row in VALUE_TABLES[0]:
            # use parse to help us to identify value types
            parsed_query = parse(
                f"INSERT INTO {table_name}({', '.join(columns)}) VALUES {row}",
                null=SQL_NULL,
            )
            if isinstance(parsed_query['query']['select'], Dict):
                lines.append([parsed_query['query']['select']])
            else:
                lines.append(parsed_query['query']['select'])
        values_table = ValuesTable(name=table_name, rows=lines, attributes=columns)
    else:
        table_name = values['name']
        lines = []
        for row in VALUE_TABLES[0]:
            # use parse to help us to identify value types
            parsed_query = parse(f"INSERT INTO {table_name} VALUES {row}",
                                 null=SQL_NULL)
            if isinstance(parsed_query['query']['select'], Dict):
                lines.append([parsed_query['query']['select']])
            else:
                lines.append(parsed_query['query']['select'])
        values_table = ValuesTable(name=table_name, rows=lines)
    del VALUE_TABLES[0]
    return values_table


class SQLParser:
    def __init__(self):
        " a + b -c"
        "GroupByTable: 10k"
        pass

    def parse(self, query: str, dialect=DIALECT.ALL):
        # preprocessing

        query = query.replace('$', '_DOLLAR_') \
            .replace('IS TRUE', F'IS {IS_TRUE}').replace('IS NOT TRUE', F'IS NOT {IS_TRUE}') \
            .replace('IS FALSE', F'IS {IS_FALSE}').replace('IS NOT FALSE', F'IS NOT {IS_FALSE}')
        # SELECT ALL -> SELECT
        query = query.replace('SELECT ALL ', 'SELECT ')

        # if query == 'SELECT t.ENAME FROM (SELECT EMP.ENAME, EMP.DEPTNO, EMP.SAL + 1 AS SALPLUS FROM EMP AS EMP) AS t WHERE t.DEPTNO IN (SELECT EMP0.DEPTNO FROM EMP AS EMP0 WHERE EMP0.SAL + 1 = EMP0.JOB)':
        #     raise ParserSyntaxError(f"`EMP0.SAL + 1 = EMP0.JOB` since EMP0.SAL is int while EMP0.JOB is string")
        # for uns_key in ['EXISTS', 'GROUPING', 'SUBSTRING', 'LATERAL', 'EXTRACT', 'ROLLUP', 'EXTRACT', 'LIKE', 'TRIM']:
        #     if uns_key in query:
        #         raise NotSupportedError(f"`{uns_key}` is not supported.")

        def _remove_dots(obj):
            if isinstance(obj, dict):
                if len(obj) == 1 and 'literal' in obj and isinstance(obj['literal'], str) and \
                        is_date_format(obj['literal']):
                    return {'date': obj['literal']}

                for k, v in obj.items():
                    obj[k] = _remove_dots(v)
                    if k == 'literal':
                        if isinstance(v, str) and len(v) > 0:
                            if str.isdigit(v[0]):
                                try:
                                    numeric_v = float(v)
                                    if numeric_v == int(v):
                                        numeric_v = int(v)
                                    v = numeric_v
                                except:
                                    if re.match(r'\d+ DAY', v):
                                        v = ''.join(char for char in v if str.isdigit(char))
                                        v = int(v)
                                    # else:
                                    #     v = re.sub(r'\s|-', '_', v)
                            # else:
                            #     v = re.sub(r'\s|-', '_', v)
                        elif isinstance(v, list):
                            new_vs = []
                            for s in v:
                                if len(s) > 0 and str.isdigit(s[0]):
                                    try:
                                        numeric_s = float(s)
                                        if numeric_s == int(s):
                                            numeric_s = int(s)
                                        s = numeric_s
                                    except:
                                        if re.match(r'\d+ DAY', v):
                                            v = ''.join(char for char in v if str.isdigit(char))
                                            v = int(v)
                                        # else:
                                        #     v = re.sub(r'\s|-', '_', v)
                                    new_vs.append(s)
                                elif len(s) == 0:
                                    new_vs.append(SPACE_STRING)
                                else:
                                    new_vs.append(s)
                            v = new_vs
                        obj[k] = v
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    obj[i] = _remove_dots(v)
            elif isinstance(obj, str):
                return obj.replace('.', '__')
            # {'literal': 1} -> 1
            # {'literal': [1,2,3]} -> [1,2,3]
            if isinstance(obj, dict) and len(obj) == 1 and 'literal' in obj:
                if isinstance(obj['literal'], Union[int, bool, float]) or \
                        (
                                isinstance(obj['literal'], list) and \
                                all(isinstance(o, Union[int, bool, float]) for o in obj['literal'])
                        ):
                    obj = obj['literal']
                # elif isinstance(obj['literal'], str) and re.match('String_\d+_DAY', obj['literal']):
                #     obj = int(re.findall('\d+', obj['literal'])[0])
                # elif isinstance(obj['literal'], str) and re.match('String_\d+_(YEAR|MONTH|HOUR|MINUTE|SECOND)', v):
                #     raise NotImplementedError("We only support \d+ day.")
            return obj

        try:
            query = str.upper(query)
            if re.search(VALUES_REGEX, query) is not None:
                if dialect not in {DIALECT.ALL, DIALECT.PSQL, DIALECT.POSTGRESQL}:
                    raise NotImplementedError(f"Only PostgreSQL supports VALUES, but your dialect is {dialect}")
                sub_queries, VALUE_TABLES = [], []
                re_outs = re.search(VALUES_REGEX, query)
                while re_outs is not None:
                    sub_queries.append(query[:re_outs.span()[0]])
                    VALUE_TABLES.append(query[re_outs.span()[0]:re_outs.span()[-1]])
                    query = query[re_outs.span()[-1]:]
                    re_outs = re.search(VALUES_REGEX, query)
                sub_queries.append(query)

                query = ' VALUES '.join(sub_queries)
                VALUE_TABLES = [
                    re.findall(r'\(.+?\)', values[1:-1].strip()[6:].strip())
                    for values in VALUE_TABLES
                ]
                parsed_query = parse(query, null=SQL_NULL)

                def _f(query):
                    if isinstance(query, list):
                        for idx, subquery in enumerate(query):
                            query[idx] = _f(subquery)
                    elif isinstance(query, Dict):
                        if is_VALUES(query):
                            return parse_from_values(query, VALUE_TABLES)
                        else:
                            for k, v in query.items():
                                query[k] = _f(v)
                    return query

                parsed_query = _f(parsed_query)
            elif 'TIMESTAMP' in query:
                # mo_sql_parsing cannot parse TIMESTAMP(*)
                TIMESTAMP_INDICES = [int(token[10:-1]) for token in re.findall(r'TIMESTAMP\(\d+\)', query)]
                query = re.sub(r'TIMESTAMP\(\d+\)', 'TIMESTAMP', query)
                parsed_query = parse(query, null=SQL_NULL)

                def _f(query):
                    if isinstance(query, list):
                        for subquery in query:
                            _f(subquery)
                    elif isinstance(query, Dict):
                        for k, v in query.items():
                            if k == 'timestamp':
                                query[k] = TIMESTAMP_INDICES[0]
                                del TIMESTAMP_INDICES[0]
                            else:
                                _f(v)

                _f(parsed_query)
            # elif re.search(IS_TRUE_FALSE_REGEX, query) is not None:
            #     sub_queries, IS_TRUE_FALSE_CLAUSES = [], []
            #     re_outs = re.search(IS_TRUE_FALSE_REGEX, query)
            #     while re_outs is not None:
            #         sub_queries.append(query[:re_outs.span()[0]])
            #         clause = query[re_outs.span()[0]:re_outs.span()[-1]]
            #         sub_queries.append(f'IS {TMP_PLACEHOLDER}')
            #         query = query[re_outs.span()[-1]:]
            #         re_outs = re.search(IS_TRUE_FALSE_REGEX, query)
            #     sub_queries.append(query)
            #     parsed_query = parse(''.join(sub_queries), null=SQL_NULL)
            elif re.search(LIMIT_REGEX, query) is not None:
                sub_queries, LIMIT_CLAUSES = [], []
                re_outs = re.search(LIMIT_REGEX, query)
                while re_outs is not None:
                    sub_queries.append(query[:re_outs.span()[0]])
                    clause = query[re_outs.span()[0]:re_outs.span()[-1]]
                    index = clause.find(',')
                    LIMIT_CLAUSES.append(int(clause[index + 1:]))
                    sub_queries.append(clause[:index])
                    query = query[re_outs.span()[-1]:]
                    re_outs = re.search(LIMIT_REGEX, query)
                sub_queries.append(query)
                parsed_query = parse(''.join(sub_queries), null=SQL_NULL)

                def _f(query):
                    if isinstance(query, list):
                        for idx, subquery in enumerate(query):
                            query[idx] = _f(subquery)
                    elif isinstance(query, Dict):
                        for k, v in query.items():
                            if k == 'limit' and isinstance(v, int):
                                index = LIMIT_CLAUSES.pop(0)
                                query[k] = [v, index]
                            else:
                                query[k] = _f(v)
                    return query

                parsed_query = _f(parsed_query)

            elif len(re.findall(FROM_REGEX, query)) > 0:
                from_clauses_with_parenthesis = re.findall(FROM_REGEX, query)
                for clause in from_clauses_with_parenthesis:
                    new_clause = clause.replace('(', '').replace(')', '')
                    query = query.replace(clause, new_clause, 1)
                parsed_query = parse(query, null=SQL_NULL)
            elif re.findall(NULL_REGEX, query) is not None:
                query = query.replace('!=', '<>')
                operations = [
                    match
                    for matches in re.findall(NULL_REGEX, query)
                    for match in matches
                    if len(match) > 2  # opd1 op opd2
                ]
                for operation in operations:
                    idx = str.find(query, operation)
                    query = query[:idx] + TMP_PLACEHOLDER + query[idx + len(operation):]
                for idx, operation in enumerate(operations):
                    if '<>' in operation:
                        operands = [opd.strip() for opd in operation.split('<>')]
                        operator = 'neq'
                    else:
                        operands = [opd.strip() for opd in operation.split('=')]
                        operator = 'eq'
                    if operands[0] == 'NULL':
                        null_idx, value_idx = 0, 1
                    else:
                        null_idx, value_idx = 1, 0
                    operands[null_idx] = SQL_NULL
                    if len(operands[value_idx]) > 2 and \
                            (operands[value_idx][0] == operands[value_idx][-1] == '\'' or \
                             operands[value_idx][0] == operands[value_idx][-1] == '\"'):
                        operands[value_idx] = operands[value_idx][1:-1]
                    try:
                        value = float(operands[value_idx])
                        if value == int(operands[value_idx]):
                            value = int(operands[value_idx])
                        operands[value_idx] = {'value': value}
                    except:
                        pass
                    operations[idx] = {operator: operands}
                parsed_query = parse(query, null=SQL_NULL)

                def _f(query):
                    if isinstance(query, list):
                        for idx, subquery in enumerate(query):
                            query[idx] = _f(subquery)
                    elif isinstance(query, Dict):
                        for k, v in query.items():
                            query[k] = _f(v)
                    elif query == TMP_PLACEHOLDER:
                        return operations.pop(0)
                    return query

                parsed_query = _f(parsed_query)
            else:
                parsed_query = parse(query, null=SQL_NULL)
            _remove_dots(parsed_query)
            LOGGER.debug(parsed_query)
            return parsed_query
        except ParseException as err:
            LOGGER.debug(query)
            LOGGER.debug(err)
            raise ParserSyntaxError(query)

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()


if __name__ == '__main__':
    parser = SQLParser()
    query = "select CLASS,STUDENT,sum(GRADES) from T_STUDENT_GRADES group by rollup(CLASS,STUDENT)"
    out1 = parser.parse(query)
    print(out1)
