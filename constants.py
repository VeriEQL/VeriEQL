# -*- coding: utf-8 -*-

import datetime
import os

from z3 import (
    Context,
    ArithRef,
    Int as Z3_Int,
    BoolVal as Z3_BoolVal,
    IntVal as Z3_IntVal,
    RealVal as Z3_RealVal,
    And as Z3_And,
    Or as Z3_Or,
    Not as Z3_Not,
    If as Z3_If,
    Sum as Z3_Sum,
    Implies as Z3_Implies,
)

################################################################
# z3 wrapper
################################################################

Z3_CONTEXT = Context()
IntVal = lambda arg: Z3_IntVal(arg, ctx=Z3_CONTEXT)
RealVal = lambda arg: Z3_RealVal(arg, ctx=Z3_CONTEXT)
BoolVal = lambda arg: Z3_BoolVal(arg, ctx=Z3_CONTEXT)
Int = lambda arg: Z3_Int(arg, ctx=Z3_CONTEXT)
Not = lambda *args: Z3_Not(*args, ctx=Z3_CONTEXT)
If = lambda a, b, c: Z3_If(a, b, c, ctx=Z3_CONTEXT)
Sum = lambda *args: Z3_Sum(*args, ctx=Z3_CONTEXT)
And = lambda *args: Z3_And(*args, ctx=Z3_CONTEXT)
Or = lambda *args: Z3_Or(*args, ctx=Z3_CONTEXT)
Implies = lambda a, b: Z3_Implies(a, b, ctx=Z3_CONTEXT)

POS_INF__Int = Int('POS_INF__Int')
NEG_INF__Int = Int('NEG_INF__Int')
Z3_TRUE = BoolVal(True)
Z3_FALSE = BoolVal(False)
Z3_1 = IntVal('1')
Z3_0 = IntVal('0')
Z3_NULL_VALUE = IntVal('-10')

################################################################
# constants
################################################################

# big INT
INT_LOWER_BOUND = IntVal('-2147483648')
INT_UPPER_BOUND = IntVal('2147483647')

PROJ_PATH = os.path.dirname(__file__)
MIN_DATE = datetime.datetime(1970, 1, 1)
DATE_LOWER_BOUND = IntVal('1')
MAX_DATE = datetime.datetime(9999, 12, 31)
DATE_UPPER_BOUND = IntVal(f'{(MAX_DATE - MIN_DATE).days + 1}')  # avoid bool('1970-01-01') == 0
SQL_NULL = {"null": None}
NumericType = int | float | ArithRef
BACKUP_SUFFIX = '__BACKUP__'
SPACE_STRING = "__SPACE_STRING__"
# note that the hash code of string in python is out of the range int32
IS_FALSE = "__IS_FALSE__"
IS_TRUE = "__IS_TRUE__"

TIMEOUT = 600  # 10 min


class DIALECT:
    ALL = "all"
    MYSQL = "mysql"
    MARIADB = "mariadb"
    PSQL = "psql"
    POSTGRESQL = "postgresql"
    ORACLE = "oracle"


class STATE:
    EQUIV = "EQU"
    NON_EQUIV = "NEQ"
    UNKNOWN = 'UNK'
    TIMEOUT = "TMO"
    SYN_ERR = "SYN"
    NOT_IMPL_ERR = "NIE"
    NOT_SUP_ERR = "NSE"
    OOM = "OOM"
    OTHER_ERR = "OTE"
