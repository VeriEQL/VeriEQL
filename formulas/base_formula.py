# -*- coding:utf-8 -*-


import abc
import ctypes


############################# Formula #############################

class BaseFormula:

    def __str__(self) -> str:
        # show in interminal
        return self.__class__.__name__

    def __repr__(self) -> str:
        return self.__str__()

    @abc.abstractmethod
    def __eq__(self, other):
        pass

    def __uuid__(self):
        return ctypes.c_size_t(hash(self.__str__())).value


# alias FormulaType = string or Formula
FormulaType = str | BaseFormula
