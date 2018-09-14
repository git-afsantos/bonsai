# Copyright (c) 2018 Davide Laezza
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

###############################################################################
# Imports
###############################################################################

import ast
import re

import bonsai.py.model as py_model

from inspect import getmembers, isroutine


###############################################################################
# Transformer
###############################################################################


class Bool(ast.expr):
    def __init__(self, name_node):
        ast.expr.__init__(self, lineno=name_node.lineno,
                          col_offset=name_node.col_offset)
        self._fields = self._fields + ('b',)

        self.b = True if name_node.id == 'True' else False


class NoneAST(ast.expr):
    def __init__(self, name_node):
        ast.expr.__init__(self, lineno=name_node.lineno,
                          col_offset=name_node.col_offset)


class ASTPreprocessor(ast.NodeTransformer):
    name_mappings = {
        'False': Bool,
        'None': NoneAST,
        'True': Bool,
    }

    def visit_Compare(self, node):
        return self.generic_visit(node)

    def visit_Name(self, node):
        try:
            return self.name_mappings[node.id](node)
        except KeyError:
            return node


###############################################################################
# Builder
###############################################################################


def identity(x):
    return x


operator_names = {
    ast.Add: '+',
    ast.And: 'and',
    ast.BitAnd: '&',
    ast.BitOr: '|',
    ast.BitXor: '^',
    ast.Div: '/',
    ast.Eq: '==',
    ast.FloorDiv: '//',
    ast.Gt: '>',
    ast.GtE: '>=',
    ast.In: 'in',
    ast.Invert: '~',
    ast.Is: 'is',
    ast.IsNot: 'is not',
    ast.LShift: '<<',
    ast.Lt: '<',
    ast.LtE: '<=',
    ast.Mod: '%',
    ast.Mult: '*',
    ast.Not: 'not',
    ast.NotEq: '!=',
    ast.NotIn: 'not in',
    ast.Or: 'or',
    ast.Pow: '**',
    ast.RShift: '>>',
    ast.Sub: '-',
    ast.UAdd: '+',
    ast.USub: '-',
}

comprehension_name = {
    ast.DictComp: 'dict',
    ast.GeneratorExp: 'generator',
    ast.ListComp: 'list',
    ast.SetComp: 'set',
}


class PyBonsaiBuilder(object):
    """

    Holds a scope and a parent and builds children into results


    """

    bonsai_prefix = re.compile('^Code')

    @classmethod
    def _make_class_name(cls, bonsai_node):
        return re.sub(cls.bonsai_prefix, 'Py', bonsai_node.__class__.__name__)

    def __init__(self, parent=None, scope=None, props=None):
        self.children = []

        self.parent = parent
        self.scope = scope or parent
        self.props = props or {}

    def __getattr__(self, item):
        try:
            return self.props[item]
        except KeyError:
            raise AttributeError()

    def add_child(self, child):
        self.children.append(child)
        return self

    def finalize(self, bonsai_node):
        method_name = 'finalize_' + self._make_class_name(bonsai_node)
        return getattr(self, method_name, identity)(bonsai_node)

    def finalize_PyComprehension(self, bonsai_node):
        if 'dict' in bonsai_node.name:
            bonsai_node.expr = py_model.PyKeyValue(bonsai_node, bonsai_node,
                                                   *self.children[:2])
            first_iter_index = 2
        else:
            bonsai_node.expr = self.children[0]
            first_iter_index = 1

        bonsai_node.iters = self.children[first_iter_index:]
        return bonsai_node

    def finalize_PyComprehensionIterator(self, bonsai_node):
        bonsai_node.target = self.children[0]
        bonsai_node.iter = self.children[1]
        bonsai_node.filters = tuple(self.children[2:])
        return bonsai_node

    def finalize_PyExpressionStatement(self, bonsai_node):
        bonsai_node.expression = self.children[0]
        return bonsai_node

    def finalize_PyFunctionCall(self, bonsai_node):
        function_name = self.children[0]
        bonsai_node.name = function_name.name
        if function_name.field_of is not None:
            bonsai_node._set_method(function_name.field_of)

        start, end = 1, 1 + self.args_count
        for arg in self.children[start:end]:
            bonsai_node._add(arg)

        start, end = end, end + self.kwargs_count
        bonsai_node.named_args = tuple(self.children[start:end])

        if self.has_starargs:
            start, end = end, end + 1
            bonsai_node.star_args = self.children[start]

        if self.has_kwargs:
            start = end
            bonsai_node.kw_args = self.children[start]

        return bonsai_node

    def finalize_PyKeyValue(self, bonsai_node):
        bonsai_node.value = self.children[0]
        return bonsai_node

    def finalize_PyModule(self, bonsai_node):
        for child in self.children:
            bonsai_node._add(child)
        return bonsai_node

    def finalize_PyOperator(self, bonsai_node):
        for child in self.children:
            bonsai_node._add(child)
        return bonsai_node

    def finalize_PyReference(self, bonsai_node):
        if self.children:
            bonsai_node._set_field(self.children[0])

        return bonsai_node


###############################################################################
# Visitor
###############################################################################


class BuilderVisitor(ast.NodeVisitor):

    @classmethod
    def with_builder(cls, self, visitor_method):
        def builder_visit(node):
            # start to build this node
            bonsai_node, children_scope, props = visitor_method(node)

            # build the children recursively
            children_visitor = cls(bonsai_node, children_scope, props)
            children_visitor.generic_visit(node)

            # finalize this node
            bonsai_node = children_visitor.builder.finalize(bonsai_node)

            # return to parent
            self.builder.add_child(bonsai_node)

        return builder_visit

    def _make_comprehension(self, py_node):
        comp_name = comprehension_name[py_node.__class__] + '_comprehension'
        bonsai_node = py_model.PyComprehension(self.scope, self.parent,
                                               comp_name, None, None)
        return bonsai_node, self.scope, None

    def _make_operator(self, py_node):
        op_name = operator_names[py_node.op.__class__]
        bonsai_node = py_model.PyOperator(self.scope, self.parent, op_name)
        return bonsai_node, self.scope, None

    def __init__(self, parent=None, scope=None, props=None):
        ast.NodeVisitor.__init__(self)

        self.builder = PyBonsaiBuilder(parent, scope, props)

        for (name, method) in getmembers(self, isroutine):
            if name.startswith('visit_'):
                setattr(self, name, self.with_builder(self, method))

    @property
    def scope(self):
        return self.builder.scope

    @property
    def parent(self):
        return self.builder.parent

    def build(self, node):
        self.visit(node)
        return self.builder.children[0]

    def visit_Attribute(self, py_node):
        # Still need to handle definitions (just use py_node.ctx)
        bonsai_node = py_model.PyReference(self.scope, self.parent,
                                           py_node.attr, None)
        return bonsai_node, self.scope, None

    def visit_BinOp(self, py_node):
        return self._make_operator(py_node)

    def visit_Bool(self, py_node):
        return py_node.b, self.scope, None

    def visit_BoolOp(self, py_node):
        return self._make_operator(py_node)

    def visit_Call(self, py_node):
        # (lambda n: n)(9) is not handled yet

        bonsai_node = py_model.PyFunctionCall(self.scope, self.parent, None)
        props = {
            'args_count': len(py_node.args or ()),
            'kwargs_count': len(py_node.keywords or ()),
            'has_starargs': py_node.starargs is not None,
            'has_kwargs': py_node.kwargs is not None,
        }
        return bonsai_node, self.scope, props

    def visit_Compare(self, py_node):
        op_name = operator_names[py_node.ops[0].__class__]
        bonsai_node = py_model.PyOperator(self.scope, self.parent, op_name)
        return bonsai_node, self.scope, None

    def visit_comprehension(self, py_node):
        bonsai_node = py_model.PyComprehensionIterator(self.parent, None, None)
        return bonsai_node, self.scope, None

    def visit_DictComp(self, py_node):
        return self._make_comprehension(py_node)

    def visit_Expr(self, py_node):
        bonsai_node = py_model.PyExpressionStatement(self.scope, self.parent,
                                                     None)
        return bonsai_node, self.scope, None

    def visit_IfExp(self, py_node):
        bonsai_node = py_model.PyOperator(self.scope, self.parent,
                                          'conditional-operator')
        return bonsai_node, self.scope, None

    def visit_keyword(self, py_node):
        bonsai_node = py_model.PyKeyValue(self.scope, self.parent, py_node.arg)
        return bonsai_node, self.scope, None

    def visit_GeneratorExp(self, py_node):
        return self._make_comprehension(py_node)

    def visit_ListComp(self, py_node):
        return self._make_comprehension(py_node)

    def visit_Module(self, py_node):
        bonsai_node = py_model.PyModule()
        return bonsai_node, bonsai_node, None

    def visit_Name(self, py_node):
        # Still need to handle definitions (just use py_node.ctx)
        bonsai_node = py_model.PyReference(self.scope, self.parent, py_node.id,
                                           None)
        return bonsai_node, self.scope, None

    def visit_NoneAST(self, py_node):
        return 'None', self.scope, None

    def visit_Num(self, py_node):
        return py_node.n, self.scope, None

    def visit_SetComp(self, py_node):
        return self._make_comprehension(py_node)

    def visit_Str(self, py_node):
        return py_node.s, self.scope, None

    def visit_UnaryOp(self, py_node):
        return self._make_operator(py_node)


###############################################################################
# Rest
###############################################################################


from os.path import abspath, dirname, join, realpath

file_name = realpath(join(dirname(abspath(__file__)), '..', '..', 'examples',
                          'py', 'examples.py'))

with open(file_name) as source:
    content = source.read()
    tree = ASTPreprocessor().visit(ast.parse(content, file_name))
    bonsai_tree = BuilderVisitor().build(tree)

    # print(ast.dump(tree))
    print(bonsai_tree.pretty_str())

    # for child in bonsai_tree.walk_preorder():
    #     print('{} ({}): {!r} -- parent: {!r}'.format(
    #             type(child).__name__,
    #             id(child) % 100000,
    #             child,
    #             None if child.parent is None else id(child.parent) % 100000))
