import os

import pandas as pd
from mo_parsing import ParseException
from mo_sql_parsing import parse


def main():
    directory = 'parser_test_mysql'
    total_count = 0
    error_count = 0
    for filename in os.listdir(directory):
        fpath = os.path.join(directory, filename)
        if os.path.isfile(fpath):
            f = open(fpath)
            df = pd.read_csv(f, usecols=['id', 'query'])

            for query in df['query']:
                total_count += 1
                try:
                    parse(query)
                except ParseException as e:
                    print(fpath, e)
                    error_count += 1

    print(total_count, error_count, total_count / error_count)


if __name__ == '__main__':
    # main()
    print(parse("SELECT *, a FROM EMP WHERE a > 1 AND b > 2 AND c > 3"))
