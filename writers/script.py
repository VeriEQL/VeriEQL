# -*- coding:utf-8 -*-

from formulas.expressions.digits import FDigits
from utils import CodeSnippet
from writers.code_writer import CodeWriter


class Script:
    def __init__(self):
        self.head = CodeWriter(
            code=[
                CodeSnippet('# -*- coding:utf-8 -*-'),
                CodeSnippet('from z3 import *'),
                CodeSnippet('import itertools'),
                CodeSnippet('import functools'),
            ]
        )
        self.sort_declaration = CodeWriter(
            code=[
                CodeSnippet('__TupleSort = DeclareSort("TupleSort")', 'define `Tuple` sort'),
                CodeSnippet('__Int = IntSort()', 'define `Int` sort'),
                CodeSnippet('__String = StringSort()', 'define `String` sort'),
                CodeSnippet('__Boolean = BoolSort()', 'define `Boolean` sort'),
            ],
            docstring='define z3 Sorts'
        )
        self.tuples = []
        self.variable_declaration = CodeWriter(
            code=[
                CodeSnippet("NULL_VALUE = Const('NULL_VALUE', __Int)", 'define NULL variable'),
                CodeSnippet("POS_INF__Int = Const('POS_INF__Int', __Int)", 'define +INF variable'),
                CodeSnippet("NEG_INF__Int = Const('NEG_INF__Int', __Int)", 'define -INF variable'),
            ],
            docstring='Special Variables',
        )
        self.function_declaration = CodeWriter(
            code=[
                CodeSnippet('DELETED = Function("DELETED", __TupleSort, __Boolean)',
                            'define `DELETE` function to represent a tuple does not exist; Not(DELETE) means the existence of a tuple'),
                CodeSnippet('NULL = Function("NULL", __TupleSort, __String, __Boolean)',
                            'define `NULL` function'),
                CodeSnippet('COUNT = Function("COUNT", __TupleSort, __String, __Int)',
                            'define `COUNT` function'),
                CodeSnippet('MAX = Function("MAX", __TupleSort, __String, __Int)',
                            'define `MAX` function'),
                CodeSnippet('MIN = Function("MIN", __TupleSort, __String, __Int)',
                            'define `MIN` function'),
                CodeSnippet('AVG = Function("AVG", __TupleSort, __String, __Int)',
                            'define `AVG` function'),
                CodeSnippet('SUM = Function("SUM", __TupleSort, __String, __Int)',
                            'define `SUM` function'),
                CodeSnippet('ROUND = Function("ROUND", __Int, __Int, __Int, __Int)',
                            'define `ROUND` (uninterpreted) function'),
            ],
            docstring='Special functions',
        )
        self.query = None
        self.premise = CodeWriter()
        self.DBMS_facts = None
        self.bound_constraints = None
        self.equal_func = None
        self.final_tables = []
        self.checkpoints = {'tuples': 0, 'variable_declaration': 0, 'function_declaration': 0}

    def save_checkpoints(self):
        # save `tuples`, `variable_declaration`, `function_declaration`
        for key, value in self.checkpoints.items():
            attr = getattr(self, key)
            self.checkpoints[key] = len(attr)

    def reload_checkpoints(self):
        # reload `tuples`, `variable_declaration`, `function_declaration`
        self.tuples = self.tuples[:self.checkpoints['tuples']]
        self.variable_declaration.code = self.variable_declaration.code[:self.checkpoints['variable_declaration']]
        self.function_declaration.code = self.function_declaration.code[:self.checkpoints['function_declaration']]

    def eval(self, base_tables, tables):
        out = ''
        out += str(self.head) + '\n\n'
        out += '\n'.join(
            [f'sql{idx} = "{query}"' for idx, query in enumerate(self.query, start=1)]) + '\n\n'
        out += str(self.sort_declaration) + '\n\n'
        out += str(self.function_declaration) + '\n\n'
        out += str(self.variable_declaration) + '\n\n'
        out += """
def _MAX(*args):
    return functools.reduce(lambda x, y: If(x >= y, x, y), args)


def _MIN(*args):
    return functools.reduce(lambda x, y: If(x < y, x, y), args)
        """.strip() + '\n\n'

        # DBMS facts
        out += f'DBMS_facts = And(\n{self.DBMS_facts.__str__(comma=True)}\n)\n\n'
        #         out += """
        # DBMS_facts = And(
        # # Database tuples
        # Not(DELETED(t1)),
        # MYNUMBERS__NUM(t1) == x1__Int,
        # NULL(t1, MYNUMBERS__NUM__String),
        # Not(DELETED(t2)),
        # MYNUMBERS__NUM(t2) == x2__Int,
        # NULL(t2, MYNUMBERS__NUM__String),
        # Not(DELETED(t3)),
        # MYNUMBERS__NUM(t3) == x3__Int,
        # NULL(t3, MYNUMBERS__NUM__String),
        # )
        #
        #
        # """
        # premise
        assert len(self.premise) == 2
        for idx, premise in enumerate(self.premise, start=1):
            out += f'premise{idx} = And(\n{premise}\n)' + '\n\n'
        if self.bound_constraints is not None:
            bound_constraints = [f"\t{cons},\n" for cons in self.bound_constraints]
            out += f"bound_constraints = And(\n{''.join(bound_constraints)})\n\n"
            out += f'premise = And(DBMS_facts, bound_constraints, premise1, premise2)\n\n'
        else:
            out += f'premise = And(DBMS_facts, premise1, premise2)\n\n'

        out += str(self.equal_func) + '\n\n'

        # conclusion
        out += f'conclusion = equals(ltuples=[{self.final_tables[0]}], rtuples=[{self.final_tables[1]}])'

        out += '\n\nsolver = Solver()\n\n'
        out += f"solver.add(Not(Implies(premise, conclusion)))\n"
        out += "print(f'Symbolic Reasoning Output: ==> {solver.check()} <==')\n"
        tuples_str = str(self.tuples).replace('\'', '')
        out += f"model = solver.model()\n#print(model)\nfor t in {tuples_str}:\n\tprint(str(t), model.eval(DELETED(t)))"
        lhs_tuple = list(tables[0].values())[0]
        rhs_tuple = list(tables[1].values())[0]
        out += '''
def _f(null, value, out_str=False, data_preix=None, type=None):
    if not isinstance(null, bool):
        null = eval(str(model.eval(null, model_completion=True)))
    if null:
        value = 99999
    else:
        if not isinstance(value, int | float):
            value = eval(str(model.eval(value, model_completion=False)))
    
    if value == 99999:
        return 'NULL'
    else:
        if out_str:
            return f"\'{value}\'"
        else:
            value = value if data_preix is None else f"'{data_preix + str(value)}'"
            if type == 'boolean':
                return value != 0
            else:
                return value

'''
        for base_table in base_tables.values():
            for base_tuple in base_table:
                out += "print(\n"
                tuple = base_tuple.SORT
                for idx, attr in enumerate(base_tuple.attributes):
                    if isinstance(attr.EXPR, int | float | FDigits):
                        if attr.name in {'SLACKER'}:
                            out += f"\t_f({str(attr.NULL).replace('?', str(tuple))}, {attr.VALUE}, type='boolean'),\n"
                        else:
                            out += f"\t_f({str(attr.NULL).replace('?', str(tuple))}, {attr.VALUE}),\n"
                    else:
                        if attr.name in {'SLACKER'}:
                            out += f"\t_f({str(attr.NULL).replace('?', str(tuple))}, {attr.VALUE}({tuple}), type='boolean'),\n"
                        else:
                            out += f"\t_f({str(attr.NULL).replace('?', str(tuple))}, {attr.VALUE}({tuple})),\n"
                    if idx != len(base_tuple.attributes) - 1:
                        out += "',',\n"
                out += ')\n'

        out += "\nprint('--------sql1--------')\n"
        for tuple in self.final_tables[0].code.split(', '):
            out += f"if model.eval(Not(DELETED({tuple}))):\n\tprint(\n"
            for idx, attr in enumerate(lhs_tuple.attributes):
                if isinstance(attr.EXPR, int | float | FDigits):
                    if attr.name in {'SLACKER'}:
                        out += f"\t_f({str(attr.NULL).replace('?', tuple)}, {attr.VALUE}, type='boolean'),\n"
                    else:
                        out += f"\t_f({str(attr.NULL).replace('?', tuple)}, {attr.VALUE}),\n"
                else:
                    if attr.name in {'SLACKER'}:
                        out += f"\t_f({str(attr.NULL).replace('?', tuple)}, {attr.VALUE}({tuple}), type='boolean'),\n"
                    else:
                        out += f"\t_f({str(attr.NULL).replace('?', tuple)}, {attr.VALUE}({tuple})),\n"
                if idx != len(lhs_tuple.attributes) - 1:
                    out += "',',\n"
            out += '\t)\n'
        out += "print('--------sql2--------')\n"
        for tuple in self.final_tables[1].code.split(', '):
            out += f"if model.eval(Not(DELETED({tuple}))):\n\tprint(\n"
            for idx, attr in enumerate(rhs_tuple.attributes):
                if isinstance(attr.EXPR, int | float | FDigits):
                    if attr.name in {'SLACKER'}:
                        out += f"\t_f({str(attr.NULL).replace('?', tuple)}, {attr.VALUE}, type='boolean'),\n"
                    else:
                        out += f"\t_f({str(attr.NULL).replace('?', tuple)}, {attr.VALUE}),\n"
                else:
                    if attr.name in {'SLACKER'}:
                        out += f"\t_f({str(attr.NULL).replace('?', tuple)}, {attr.VALUE}({tuple}), type='boolean'),\n"
                    else:
                        out += f"\t_f({str(attr.NULL).replace('?', tuple)}, {attr.VALUE}({tuple})),\n"
                if idx != len(rhs_tuple.attributes) - 1:
                    out += "',',\n"
            out += '\t)\n'
        return out
