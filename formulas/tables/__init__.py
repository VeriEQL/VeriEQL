# -*- coding:utf-8 -*-


from .alias_table import FAliasTable
from .base_table import FBaseTable
from .distinct_table import FDistinctTable
from .empty_table import FEmptyTable
from .except_all_table import FExceptAllTable
from .except_table import FExceptTable
from .fake_projection_table import FFakeProjectionTable
from .fetch_table import FFetchTable
from .filter_table import FFilterTable
from .groupby_tables import (
    FGroupByMapTable,
    FGroupByTable,
)
from .intersect_all_table import FIntersectAllTable
from .intersect_table import FIntersectTable
from .join_tables import (
    FJoinBaseTable,
    FInnerJoinTable,
    FCrossJoinTable,
    FNaturalJoinTable,
    FOuterJoinBaseTable,
    FLeftOuterJoinTable,
    FRightOuterJoinTable,
    FFullOuterJoinTable,

    OuterJoinTableType,
    JoinTableType,
)
from .limit_table import FLimitTable
from .offset_table import FOffsetTable
from .order_by_table import FOrderByTable
from .product_table import FProductTable
from .projection_table import FProjectionTable
from .stack_table import FStackTable
from .union_all_table import FUnionAllTable
from .union_table import FUnionTable
from .value_table import FValueTable

TableType = JoinTableType | FGroupByMapTable | FGroupByTable | \
            FBaseTable | FAliasTable | FFilterTable | FProductTable | FProjectionTable | FDistinctTable | FOrderByTable | \
            FUnionTable | FUnionAllTable | FIntersectTable | FIntersectAllTable | FExceptTable | FExceptAllTable | \
            FEmptyTable | FOffsetTable | FFetchTable | FLimitTable | FStackTable | FFakeProjectionTable

__all__ = [
    'FBaseTable',
    'FAliasTable',
    'FFilterTable',
    'FProductTable',
    'FProjectionTable',
    'FFakeProjectionTable',

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
    'FDistinctTable',

    'FGroupByMapTable',
    'FGroupByTable',
    'FOrderByTable',
    'FLimitTable',
    'FStackTable',

    'FUnionAllTable',
    'FUnionTable',
    'FIntersectTable',
    'FIntersectAllTable',
    'FExceptTable',
    'FExceptAllTable',

    'FValueTable',

    'TableType',
    'FEmptyTable',

    'FOffsetTable',
    'FFetchTable',
]
