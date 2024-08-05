# -*- coding:utf-8 -*-


from .full_outer_join_table import FFullOuterJoinTable
from .left_outer_join_table import FLeftOuterJoinTable
from .outer_join_base_table import FOuterJoinBaseTable
from .right_outer_join_table import FRightOuterJoinTable

OuterJoinTableType = FOuterJoinBaseTable | FLeftOuterJoinTable | FRightOuterJoinTable | FFullOuterJoinTable

__all__ = [
    'FOuterJoinBaseTable',
    'FLeftOuterJoinTable',
    'FRightOuterJoinTable',
    'FFullOuterJoinTable',

    'OuterJoinTableType',
]
