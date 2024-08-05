# -*- coding:utf-8 -*-


from .cross_join_table import FCrossJoinTable
from .inner_join_table import FInnerJoinTable
from .join_base_table import FJoinBaseTable
from .natural_join_table import FNaturalJoinTable
from .outer_join_tables import (
    FOuterJoinBaseTable,
    FLeftOuterJoinTable,
    FRightOuterJoinTable,
    FFullOuterJoinTable,
    OuterJoinTableType,
)

JoinTableType = OuterJoinTableType | FJoinBaseTable | FInnerJoinTable | FCrossJoinTable | FNaturalJoinTable

__all__ = [
    'FJoinBaseTable',
    'FInnerJoinTable',
    'FCrossJoinTable',
    'FNaturalJoinTable',

    'FOuterJoinBaseTable',
    'FLeftOuterJoinTable',
    'FRightOuterJoinTable',
    'FFullOuterJoinTable',

    'OuterJoinTableType',
    'JoinTableType',
]
