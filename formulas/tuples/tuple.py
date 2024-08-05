# -*- coding:utf-8 -*-

import abc
from typing import (
    Any,
    Sequence,
)

from ordered_set import OrderedSet

from formulas import register_formula
from formulas.base_formula import BaseFormula


@register_formula('tuple')
class FTuple(BaseFormula):
    """
    Only used as the tuple reference
    """

    def __init__(self,
                 tuples: Sequence[BaseFormula] = None,
                 condition: Any = None,
                 name: str = None,
                 *args, **kwargs,
                 ):
        self.tuples = tuples if isinstance(tuples, Sequence) else [tuples]
        self.name = name
        self.condition = condition
        super(FTuple, self).__init__()
        self.SORT = None
        self._mutex = None

    @abc.abstractmethod
    def __str__(self) -> str:
        pass

    def add_mutex(self, tuple):
        # for OUTER JOIN
        if not getattr(self, '_mutex', False):
            self._mutex = OrderedSet()
        if isinstance(tuple, OrderedSet):
            self._mutex.update(tuple)
        elif isinstance(tuple, list):
            self._mutex.update(OrderedSet(tuple))
        else:
            self._mutex.add(tuple)

    @property
    def fathers(self) -> Sequence:
        return [t.name for t in self.tuples]

    def add_attributes(self, attributes: Sequence):
        self.attributes.extend(attributes)
