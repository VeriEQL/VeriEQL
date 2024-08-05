# -*- coding:utf-8 -*-

import importlib
import os

from .base_formula import BaseFormula

FORMULA_REGISTRY = {}


def build_fomula(*args):
    return FORMULA_REGISTRY


# a @register_formula decorator
def register_formula(name):
    def register_formula_cls(cls):
        if name in FORMULA_REGISTRY:
            raise ValueError(f'Cannot register duplicate model {name}')
        if not issubclass(cls, BaseFormula):
            raise ValueError(F'Formula ({name}: {cls.__name__}) muse extend BaseFormula')
        FORMULA_REGISTRY[name] = cls
        return cls

    return register_formula_cls


__all__ = [
    'register_formula'
]

models_dir = os.path.dirname(__file__)
for file in os.listdir(models_dir):
    path = os.path.join(models_dir, file)
    if (
            not file.startswith('_')
            and not file.startswith('.')
            and (file.endswith('.py') or os.path.isdir(path))
    ):
        model_name = file[:file.find('.py')] if file.endswith('.py') else file
        module = importlib.import_module('formulas.' + model_name)
