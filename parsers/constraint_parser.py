# -*- coding: utf-8 -*-

import itertools

import yaml
from lark import (
    Lark,
    Transformer,
)


class ConstraintVisitor(Transformer):
    def membership(self, tree):
        # column dependence
        # Employee.departmentId <- Department.id
        if isinstance(tree[1], dict) and 'value' in tree[1]:
            # {'foreign': [key, foreign key]}
            return {'foreign': tree}
        # column value membership
        # X.Y <- [0,10]
        elif isinstance(tree[1], tuple):
            # {'and': [{'lte': [10, 'AGE']}, {'lte': ['AGE', 20]}]}
            lower_bound = tree[1][0]
            upper_bound = tree[1][1]
            return {'between': [tree[0], lower_bound, upper_bound]}
        # column value membership
        # SurveyLog.action <- {'show', 'answer', 'skip'}
        elif isinstance(tree[1], list):
            # {'in': ['AGE', ['AAAAA', 'BBBBB']]}
            return {'in': tree}
        else:
            raise NotImplementedError

    def not_null(self, tree):
        return {'not_null': tree[0]}

    def comparison(self, tree):
        # {'gt': ['AGE', 1]}
        operands = [tree[0], tree[2]]
        operator = tree[1]
        return {operator: operands}

    def unique(self, tree):
        return {'primary': [node for node in tree]}

    def inc(self, tree):
        assert len(tree) == 1, NotImplementedError(f"More than 1 attributes in INC: {tree}")
        return {'inc': tree[0]}

    def op(self, tree):
        operator = str(tree[0])
        match operator:
            case '>':
                return 'gt'
            case '>=':
                return 'gte'
            case '<':
                return 'lt'
            case '<=':
                return 'lte'
            case '!=':
                return 'neq'
            case _:
                raise NotImplementedError(operator)

    def unsupported(self, tree):
        return None

    def attribute(self, tree):
        return {'value': f"{str.upper(tree[0])}__{str.upper(tree[1])}"}

    def NUMBER(self, tree):
        return eval(tree)

    def null(self, tree):
        return None

    def value_range(self, tree):
        return tree[0], tree[1]

    def value_items(self, tree):
        return tree

    def DATE(self, tree):
        return {'date': str(tree)}

    def constraints(self, tree):
        return [node for node in tree if node is not None]

    def STRING(self, tree):
        # return {'literal': tree.value[1:-1]}
        return {'literal': str.upper(tree.value[1:-1])}


class ConstraintParser:

    def __init__(self):
        self._visitor = ConstraintVisitor()
        self._parser = Lark(
            r'''
            constraints: constraint (";" constraint)* [";"]
            ?constraint : membership | not_null | comparison | unique | inc | unsupported
            membership : attribute "<-" attribute
                       | attribute "<-" value_range
                       | attribute "<-" value_items
            not_null : attribute "!=" null
            comparison : value op value
            unique : "unique" "(" [attribute ("," attribute)*] ")"
            inc : "inc" "(" [attribute ("," attribute)*] ")"
            
            unsupported : attribute "|" type ["+" "null"]
                        | attribute "^" attribute
                        | attribute "=" value "=>" attribute "=" value
                        | "inc(" [attribute ("," attribute)*] ")"
            type : "int" | "varchar"
    
            ?value : attribute | NUMBER | DATE
            !op : ">" | "<" | "!=" | ">=" | "<="
            attribute : /[^\W\d]\w*/ "." /[^\W\d]\w*/
            null: "null" | "NULL"
            value_range : "[" NUMBER "," NUMBER "]"
                        | "[" DATE "," DATE "]"
            value_items : "{" [value_item ("," value_item)*] "}"
            ?value_item : STRING | NUMBER
            DATE: NUMBER "-" NUMBER "-" NUMBER
            
            STRING : "'" /[^']+/ "'" | ESCAPED_STRING
            
            %import common.ESCAPED_STRING
            %import common.SIGNED_NUMBER    -> NUMBER
            %import common.WS
            %ignore WS
            ''',
            start='constraints')

    def parse(self, constraints):
        return self._visitor.transform(self._parser.parse(constraints))

    def parse_file(self, file) -> (list, bool):
        out = []
        contain_unsupported_constraints = False
        with open(file, 'r') as reader:
            try:
                constraints = yaml.safe_load(reader)
                if not isinstance(constraints, dict):
                    return out, contain_unsupported_constraints
                constraints = list(itertools.chain(*[constraint.split(";") for constraint in constraints.values()]))
                for constraint in constraints:
                    constraint = constraint.strip()
                    if len(constraint) == 0:
                        continue
                    try:
                        out.extend(self.parse(constraint))
                    except:
                        print(f"Unknown constraint {constraint} from {file}")
                        contain_unsupported_constraints = True
            except:
                print(SyntaxError(file))
                contain_unsupported_constraints = False
        return out, contain_unsupported_constraints


if __name__ == '__main__':
    parser = ConstraintParser()

    string = "inc(Queue.turn)"
    out = parser.parse(string)
    print(out)
