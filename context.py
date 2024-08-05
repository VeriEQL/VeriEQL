# -*- coding: utf-8 -*-

from collections import OrderedDict as _OrderedDict

from ordered_set import OrderedSet

from formulas.tables.base_table import FBaseTable


class OrderedDict(_OrderedDict):
    def __init__(self, *args, **kwargs):
        super(OrderedDict, self).__init__(*args, **kwargs)

    def __getitem__(self, key: str | int):
        if isinstance(key, int):
            key = list(self.keys())[key]
        return super(OrderedDict, self).__getitem__(key)


class GroupbyContext(object):
    """
    This context works for HAVING/ORDER/SELECT
    """

    def __init__(self, groupby_table):
        self.attributes = groupby_table.out_attributes
        self.tuples = [t.SORT for t in groupby_table.fathers[0].fathers[0].tuples]
        self.function = groupby_table.fathers[0].group_function

    def __str__(self):
        return f"{self.__class__.__name__}(attrs={self.attributes})"

    def __repr__(self):
        return self.__str__()


class Context(object):
    def __init__(self, databases={}, context=None):
        self.databases = OrderedDict(databases)
        self.base_databases = OrderedSet(databases.keys())
        self.prev_database = self.attributes = None
        self.outer_ctx = context
        self.groupby_ctx = None
        self.clear_clauses()
        self.right_outer_table = False
        self.is_correlated_subquery = False

    def clear_clauses(self):
        self.with_clause = None
        self.select_clause = None
        self.from_clause = None
        self.groupby_clause = None
        self.having_clause = None
        self.orderby_clause = None
        self.slice_clause = None

    @classmethod
    def from_context(cls, context):
        databases = list(context.base_databases)
        if context.with_clause is not None:
            databases += list(context.with_clause)
        databases = {key: context[key] for key in databases}
        ctx = Context(databases=databases, context=context)
        return ctx

    def __str__(self):
        if self.prev_database is None:
            return f'{self.__class__.__name__}({list(self.databases.keys())})'
        else:
            return f'{self.__class__.__name__}({list(self.databases.keys())}, prev={self.prev_database.name})'

    def __repr__(self):
        return self.__str__()

    @property
    def with_databases(self):
        if self.with_clause is None:
            return None
        else:
            return {name: self.databases[name] for name in self.with_clause}

    def update_with_clause(self, tables):
        if self.with_clause is None:
            self.with_clause = OrderedSet()
        for table in tables:
            self.databases[table.name] = table
            # self.base_databases.add(table.name)
            self.with_clause.add(table.name)
            self.prev_database = None

    def update_select_clause(self, table):
        if self.prev_database is not None and isinstance(self.prev_database, FBaseTable):
            self.pop(self.prev_database.name)
        self.databases[table.name] = table
        self.prev_database = self.select_clause = table
        self.attributes = table.attributes

    def update_from_clause(self, table):
        if self.prev_database is not None and isinstance(self.prev_database, FBaseTable):
            self.pop(self.prev_database.name)
        self.databases[table.name] = table
        self.prev_database = self.from_clause = table
        self.attributes = table.attributes

    def update_where_clause(self, table):
        if self.prev_database is not None and isinstance(self.prev_database, FBaseTable):
            self.pop(self.prev_database.name)
        self.databases[table.name] = table
        self.prev_database = self.where_clause = table
        self.attributes = table.attributes

    def update_groupby_clause(self, table):
        if self.prev_database is not None and isinstance(self.prev_database, FBaseTable):
            self.pop(self.prev_database.name)
        self.databases[table.name] = table
        self.prev_database = self.groupby_clause = table
        self.attributes = table.attributes
        self.groupby_ctx = GroupbyContext(table)

    def update_having_clause(self, table):
        self.databases[table.name] = table
        self.prev_database = self.having_clause = table

    def update_orderby_clause(self, table):
        if self.prev_database is not None and isinstance(self.prev_database, FBaseTable):
            self.pop(self.prev_database.name)
        self.databases[table.name] = table
        self.prev_database = self.orderby_clause = table

    def update_slice_clause(self, table):
        if self.prev_database is not None and isinstance(self.prev_database, FBaseTable):
            self.pop(self.prev_database.name)
        self.databases[table.name] = table
        self.prev_database = self.offset_clause = table

    def set_select_clause(self, select_clause):
        self.select_clause = select_clause

    def pop_select_clause(self):
        select_clause = self.select_clause
        self.select_clause = None
        return select_clause

    def update_attributes(self, attributes):
        if self.attributes is None:
            self.attributes = {}
        self.attributes.update(**attributes)

    def __getitem__(self, index):
        return self.databases[index]

    def pop(self, index):
        # 1) do not remove base tables, 2) unsaved table, 3) with tables (del with tables in clear_with function)
        if index not in self.base_databases and index in self.databases and \
                not (self.with_clause is not None and index in self.with_clause):
            return self.databases.pop(index)

    def clear_with(self):
        for clause in self.with_clause:
            if clause in self.databases:
                self.databases.pop(clause)
        self.with_clause = None
