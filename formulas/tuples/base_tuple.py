# and -*- coding:utf-8 -*-

from typing import (
    Sequence,
)

from formulas import register_formula
from formulas.base_formula import BaseFormula
from formulas.tuples._field import FField


@register_formula('base_tuple')
class FBaseTuple(BaseFormula):
    """
    To store values of a tuple
    """

    def __init__(self,
                 fields: Sequence[FField],
                 name: str,
                 ):
        self.fields = fields
        self.name = name
        # attributes are shown in SELECT clause
        self.attributes = [field.attribute for field in self.fields]
        self.SORT = None

    def __str__(self):
        return f"{self.name} := {super(FBaseTuple, self).__str__()}{self.fields}"

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return len(self.fields)

    def __getitem__(self, idx):
        return self.fields[idx]

    def add_attributes(self, attributes: Sequence):
        self.attributes.extend(attributes)
