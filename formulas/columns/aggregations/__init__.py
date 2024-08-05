# -*- coding:utf-8 -*-

from .aggregation import FAggregation
from .avg import FAggAvg
from .bool_and import FBoolAnd
from .bool_or import FBoolOr
from .count import FAggCount
from .max import FAggMax
from .min import FAggMin
from .stddev_pop import FStddevPop
from .stddev_samp import FStddevSamp
from .sum import FAggSum
from .var_pop import FVarPop
from .var_samp import FVarSamp


def find_aggregation(agg_func: str):
    match agg_func:
        case 'avg':
            return FAggAvg
        case 'count':
            return FAggCount
        case 'sum':
            return FAggSum
        case 'max':
            return FAggMax
        case 'min':
            return FAggMin
        case 'stddev_pop':
            return FStddevPop
        case 'var_pop':
            return FVarPop
        case 'stddev_samp':
            return FStddevSamp
        case 'var_samp':
            return FVarSamp
        case 'bool_and':
            return FBoolAnd
        case 'bool_or':
            return FBoolOr
        case _:
            raise NotImplementedError(agg_func)


AggregationType = FAggregation | \
                  FAggAvg | FAggCount | FAggMax | FAggMin | FAggSum | \
                  FStddevPop | FVarPop | FStddevSamp | FVarSamp

__all__ = [
    'AggregationType',
    'FAggregation',
    'FAggAvg',
    'FAggCount',
    'FAggSum',
    'FAggMax',
    'FAggMin',
    'FStddevPop',
    'FVarPop',
    'FStddevSamp',
    'FVarSamp',
    'FBoolAnd',
    'FBoolOr',
    'find_aggregation',
]
