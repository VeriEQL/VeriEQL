# -*- coding: utf-8 -*-

from typing import (
    Sequence,
    Callable,
)

from ordered_set import OrderedSet
from z3 import Function

from formulas import register_formula
from formulas.expressions.expression import FExpression
from formulas.expressions.operator import FOperator
from formulas.tables.base_table import FBaseTable
from formulas.tables.filter_table import FFilterTable
from formulas.tables.groupby_tables.groupby_map_table import FGroupByMapTable
from formulas.tables.union_all_table import FUnionAllTable
from writers.code_writer import CodeSnippet


@register_formula('group_by_table')
class FGroupByTable(FBaseTable):
    def __init__(self,
                 scope,
                 table: FBaseTable,
                 groupby_clause: Sequence,
                 groupby_func: Callable,
                 select_clause: Sequence = None,
                 is_vanilla_grouby_keys: bool = False,
                 groupby_fuzzy: bool = False,
                 name: str = None,
                 ):
        """
        GROUP BY is quite complicated, we better incorporate FGroupReduce, filter and projection together.
        We only consider `GROUP BY [EXPR | CASE]+`
        """

        self.groupby_keys = groupby_clause
        # self._attributes is for vanilla attributes in HAVING and ORDER-BY
        if is_vanilla_grouby_keys is None:
            self._attributes = None
        else:
            self._attributes = groupby_clause[0]
        # self._attributes is for aggregation attributes in HAVING and ORDER-BY
        self.out_attributes = OrderedSet(select_clause)
        _out_attributes_string = [str(column) for column in self.out_attributes]
        for attr in table[0].attributes:
            if attr in self.out_attributes or str(attr) in _out_attributes_string:
                pass
            else:
                self.out_attributes.add(attr)
                _out_attributes_string.append(str(attr))
        del _out_attributes_string

        # # A (NOT) IN (SELECT A FROM XX GROUP BY B)
        # if groupby_fuzzy:
        #     self.fuzzy_attributes = select_clause
        # else:
        #     self.fuzzy_attributes = None

        new_table = FGroupByMapTable(
            scope, table, groupby_clause,
            group_function=groupby_func,
            attributes=self.attributes,
            out_attributes=self.out_attributes,
        )

        name = name or scope._get_new_databases_name()
        super(FGroupByTable, self).__init__(new_table.tuples, name)
        scope.register_database(name, self)
        self.fathers = [new_table]
        self.root = new_table.root or new_table.name
        self.having_clause = None

    @classmethod
    def build(cls,
              scope,
              table: FBaseTable,
              groupby_clause: Sequence,
              select_clause: Sequence = None,
              groupby_fuzzy=False,
              name: str = None,
              ):
        if len(groupby_clause) == 1:
            groupby_keys = [key for _, key in groupby_clause[0]]
            groupby_keys = [groupby_keys for _ in range(len(table))]
            name = name or scope._get_new_databases_name()
            func = Function(f'{name}_GROUP_FUNC', scope.TupleSort, scope.VarSort, scope.BooleanSort)
            scope.register_function(name=str(func), function=func)
            if scope._script_writer is not None:
                scope._script_writer.function_declaration.append(
                    CodeSnippet(
                        code=f"{func} = Function('{func}', __TupleSort, __Int, __Boolean)",
                        docstring=f'define `{func}` function to partition tuples into groups',
                    )
                )
            table = cls(scope, table, groupby_keys, func, select_clause,
                        is_vanilla_grouby_keys=True, groupby_fuzzy=groupby_fuzzy, name=name)
        else:
            filter_tables = []
            groupby_keys = []
            for idx, paired_keys in enumerate(groupby_clause):
                conds, keys = zip(*paired_keys)
                conds = [cond for cond in conds if cond is not None]
                if len(conds) == 1:
                    cond = conds[0]
                else:
                    cond = FExpression(FOperator('and'), conds)
                filter_tables.append(FFilterTable(scope, table, cond))
                groupby_keys.extend([list(keys) for _ in range(len(table))])

            merged_table = FUnionAllTable(scope, filter_tables)
            name = name or scope._get_new_databases_name()
            func = Function(f'{name}_GROUP_FUNC', scope.TupleSort, scope.VarSort, scope.BooleanSort)
            scope.register_function(name=str(func), function=func)
            if scope._script_writer is not None:
                scope._script_writer.function_declaration.append(
                    CodeSnippet(
                        code=f"{func} = Function('{func}', __TupleSort, __Int, __Boolean)",
                        docstring=f'define `{func}` function to partition tuples into groups',
                    )
                )
            table = cls(scope, merged_table, groupby_keys, func, select_clause,
                        groupby_fuzzy=groupby_fuzzy, name=name)
        return table

    def __str__(self):
        map_tables = '\n'.join(['\t' + str(table) for table in self.fathers])
        out = f'{self.__class__.__name__}({self.name}) = [\n{map_tables}\n]'
        return out

    def __repr__(self):
        return self.__str__()

    @property
    def attributes(self):
        return self._attributes

    def set_attributes(self, attributes: Sequence):
        self._attributes = attributes

    def update_having_clause(self, having_clause):
        self.having_clause = having_clause
        self.fathers[0].update_having_clause(having_clause)
