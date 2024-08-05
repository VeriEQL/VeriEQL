# -*- coding: utf-8 -*-

from abc import abstractmethod
from typing import Sequence

from constants import (
    And,
    Not,
    Z3_NULL_VALUE,
)
from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.expression_tuple import FExpressionTuple
from formulas.expressions.null import FNull


@register_formula('base_column')
class FBaseColumn(FBaseExpression):
    def __init__(
            self,
            DELETED_FUNCTION,
            Z3_NULL_VALUE=Z3_NULL_VALUE,
            uuid: int = None,
    ):
        super(FBaseColumn, self).__init__()
        self.VALUE = None
        self.NULL = None
        self.DELETED_FUNCTION = DELETED_FUNCTION
        self._uuid = uuid or self.__uuid__()
        self._NULL_VALUE = Z3_NULL_VALUE
        self.require_tuples = False

    def __call__(self, *args, **kwargs):
        return self.VALUE(*args, **kwargs)

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def __str__(self):
        pass

    def __repr__(self):
        return self.__str__()

    @abstractmethod
    def update_alias(self, *args, **kwargs):
        pass

    def one_to_one_mapping(self, src_tuple, dst_tuple):
        # for attributes
        # res = self(src_tuple)
        # if isinstance(res, FNull):
        #     return self.NULL(dst_tuple)
        # else:
        #     return self(dst_tuple) == res
        return self(dst_tuple) == self(src_tuple)

    def __expr__(self, src_tuples: Sequence):
        pass

    def many_to_one_mapping(self, src_tuples, dst_tuple, **kwargs):
        # for aggregation
        res = self.__expr__(src_tuples, **kwargs)
        if isinstance(res, FExpressionTuple):
            return self(dst_tuple) == res
        elif isinstance(res, FNull):
            return self.NULL(dst_tuple)
        else:
            out = self(dst_tuple)
            return And(
                Not(self.NULL(dst_tuple)),
                out.VALUE == res,
            )
