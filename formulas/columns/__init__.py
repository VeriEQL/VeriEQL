# -*- coding: utf-8 -*-


from .aggregations import (
    FAggregation,
    FAggAvg,
    FAggCount,
    FAggMax,
    FAggMin,
    FAggSum,
    FStddevPop,
    FVarPop,
    FStddevSamp,
    FVarSamp,
    FBoolAnd,
    FBoolOr,
)
from .attribute import FAttribute
from .base_column import FBaseColumn

AggregationType = FAggregation | FAggAvg | FAggCount | FAggMax | FAggMin | FAggSum | \
                  FStddevPop | FVarPop | FStddevSamp | FVarSamp | \
                  FBoolAnd | FBoolOr

__all__ = [
    'FAttribute',

    'FAggregation',
    'FAggAvg',
    'FAggCount',
    'FAggMax',
    'FAggMin',
    'FAggSum',
    'FStddevPop',
    'FVarPop',
    'FStddevSamp',
    'FVarSamp',
    'FBoolAnd',
    'FBoolOr',
    'FAttribute',

    'AggregationType',
]
