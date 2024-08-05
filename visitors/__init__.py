# -*- coding:utf-8 -*-

import functools


@functools.lru_cache()
def _qualname(obj):
    """Get the fully-qualified name of an object (including module)."""
    return ''.join([obj.__module__, '.', obj.__qualname__])


@functools.lru_cache()
def _declaring_class(obj):
    """Get the name of the class that declared an object."""
    name = _qualname(obj)
    return name[:name.rfind('.')]


# Stores the actual visitor methods
_methods = {}


# Delegating visitor implementation
def _visitor_impl(self, arg, **kwargs):
    """Actual visitor method implementation."""
    # if is_uninterpreted_func(arg) and isinstance(arg.uninterpreted_func, Union[FCast, FRound]):
    #     raise NotImplementedError(f'Do not support Uninterpreted Function `{arg}` in clause which is not projection.')
    method = _methods[(_qualname(type(self)), type(arg))]
    return method(self, arg, **kwargs)


# The actual @visitor decorator
def visitor(arg_type):
    """Decorator that creates a visitor method."""

    def decorator(fn):
        declaring_class = _declaring_class(fn)
        _methods[(declaring_class, arg_type)] = fn

        # Replace all decorated methods with _visitor_impl
        return _visitor_impl

    return decorator


__all__ = [
    'visitor'
]
