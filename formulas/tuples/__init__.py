# -*- coding:utf-8 -*-


from ._field import FField
from .base_tuple import FBaseTuple
from .tuple import FTuple

FBaseTupleType = FField | FTuple | FBaseTuple

from .alias_tuple import FAliasTuple
from .concate_tuple import FConcateTuple
from .filter_tuple import FFilterTuple
from .null_tuple import FNullTuple
from .projection_tuple import FProjectionTuple
from .projection_pity_tuple import FProjectionPityTuple
from .fake_projection_tuple import FFakeProjectionTuple
from .distinct_tuple import FDistinctTuple

from .inner_join_tuple import FInnerJoinTuple
from .natural_join_tuple import FNaturalJoinTuple
from .group_by_tuple import FGroupByTuple
from .deleted_tuple import FDeletedTuple
from .limit_tuple import FLimitTuple

TupleType = FBaseTupleType | \
            FNullTuple | FAliasTuple | FFilterTuple | \
            FProjectionTuple | FProjectionPityTuple | FFakeProjectionTuple | \
            FConcateTuple | FInnerJoinTuple | FNaturalJoinTuple | FDistinctTuple | \
            FGroupByTuple | FDeletedTuple | FLimitTuple

__all__ = [
    'FBaseTuple',
    'FField',
    'FTuple',

    'FNullTuple',
    'FAliasTuple',
    'FConcateTuple',
    'FFilterTuple',
    'FProjectionTuple',
    'FFakeProjectionTuple',
    'FProjectionPityTuple',
    'FInnerJoinTuple',
    'FNaturalJoinTuple',
    'FDistinctTuple',
    'FGroupByTuple',
    'FDeletedTuple',
    'FLimitTuple',

    'FBaseTupleType',
    'TupleType',
]
