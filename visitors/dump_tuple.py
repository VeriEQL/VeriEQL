# -*- coding:utf-8 -*-

from ordered_set import OrderedSet


class DumpTuple:
    """
    Only used in Visiting Pattern
    """

    def __init__(self, name: str, sort, attributes: OrderedSet, **kwargs):
        self.name = name
        self.SORT = sort
        self.attributes = attributes
        self._mutex = None
        self.kwargs = kwargs

    def __str__(self):
        return f'{self.SORT} := {list(self.attributes)}'

    def __repr__(self):
        return self.__str__()
