# -*- coding:utf-8 -*-

import pprint

from context import Context
from encoder import Encoder
from logger import LOGGER
from visitors.dump_tuple import DumpTuple
from visitors.visitor import Visitor


class Scope:
    def __init__(self, environment, name: str = None):
        self.environment = environment
        self.name = name

        # property
        self.attributes = self.environment.attributes
        self.variables = self.environment.variables
        self.functions = self.environment.functions
        self.tuples = self.environment.tuples
        self.tuple_sorts = self.environment.tuple_sorts
        self.databases = self.environment.databases
        self.base_databases = self.environment.base_databases
        self.bound_constraints = self.environment.bound_constraints
        self._display_datasets = set(self.databases.keys())

        # function
        self.DELETED_FUNCTION = self.environment.DELETED_FUNCTION
        self.NULL = self.environment.NULL
        self.COUNT_FUNCTION = self.environment.COUNT_FUNCTION
        self.COUNT_ALL_FUNCTION = self.environment.COUNT_ALL_FUNCTION
        self.COUNT_ALL_NULL_FUNCTION = self.environment.COUNT_ALL_NULL_FUNCTION
        self.MAX_FUNCTION = self.environment.MAX_FUNCTION
        self.MIN_FUNCTION = self.environment.MIN_FUNCTION
        self.AVG_FUNCTION = self.environment.AVG_FUNCTION
        self.SUM_FUNCTION = self.environment.SUM_FUNCTION

        self._get_function = self.environment._get_function
        self.register_function = self.environment.register_function
        self._get_attribute = self.environment._get_attribute
        self.declare_attribute = self.environment.declare_attribute
        self._declare_value = self.environment._declare_value
        self._get_variable = self.environment._get_variable
        self._get_tuple_sort = self.environment._get_tuple_sort
        self._declare_tuple = self.environment._declare_tuple
        self._declare_tuple_sort = self.environment._declare_tuple_sort
        self.register_tuple = self.environment.register_tuple
        self.register_tuple_sort = self.environment.register_tuple_sort
        self.register_database = self.environment.register_database
        self._get_new_tuple_name = self.environment._get_new_tuple_name
        self._get_new_tuple_sort = self.environment._get_new_tuple_sort
        self._get_new_databases_name = self.environment._get_new_databases_name
        self._script_writer = self.environment._script_writer
        # self._declare_lb_attribute = self.environment._declare_lb_attribute
        # self._declare_ub_attribute = self.environment._declare_ub_attribute
        self.orderby_constraints = None

        # type
        self.TupleSort = self.environment.TupleSort
        self.VarSort = self.environment.VarSort
        self.BooleanSort = self.environment.BooleanSort
        self.StringSort = self.environment.StringSort

        self.out_formulas = []
        self.alias_constraints = []
        self.dump_tuples = {}
        # self._father_caches = {}  # only works for intermediate attributes
        # self._self_caches = {}  # only works for intermediate attributes
        # self._caches = {}
        # self.uninterpreted_functions = self.environment.uninterpreted_functions

        self.visitor = Visitor(self)
        self.encoder = Encoder(self)

    def _get_databases(self, name: str = None):
        if name is not None:
            return self.environment.databases[name]
        else:
            return self.environment.databases

    ############################ Register ############################

    def register_formulas(self, formulas):
        self.out_formulas.append(formulas)

    def register_dump_tuple(self, key, formulas: DumpTuple):
        self.dump_tuples[key] = formulas

    def get_dump_tuple(self, key) -> DumpTuple:
        return self.dump_tuples[key]

    def is_register_dump_tuple(self, key) -> bool:
        return key in self.dump_tuples

    ############################ Display ############################

    def __str__(self):
        return f'{self.name}[\n\t{pprint.pformat(self.databases, sort_dicts=False)}\n]'

    def __repr__(self):
        return self.__str__()

    ############################ with construction ############################

    def __enter__(self):
        LOGGER.debug(f'############################ CREATING SCOPE-{self.name} ############################')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.visitor
        # remove partial info from the current query in environment
        self.environment.reload_checkpoints(keys=['variables', 'attributes', 'functions', 'databases'])
        LOGGER.debug(f'############################ SCOPE-{self.name} Cleared ############################\n\n')

    ############################ Analyze SQL AST ############################

    def analyze(self, query) -> Context:
        ctx = self.encoder.analyze(query)
        return ctx

    def visit(self, ctx: Context):
        table = self.visitor.visit(ctx.prev_database)
        return table, self.out_formulas
