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

from collections import deque
from inspect import getmembers, isroutine

from ..model import CodeExpressionStatement
from ..py.model import PyModule, PyOperator


###############################################################################
# Builder
###############################################################################

operator_names = {
    ast.Add: '+',
    ast.Sub: '-',
}


class PyBonsaiBuilder(object):
    """

    Holds a scope and a parent and builds children into results


    """

    def __call_node_method(self, prefix, node):
        method_name = prefix + node.__class__.__name__
        return getattr(self, method_name, lambda n: n)(node)

    def __init__(self, parent=None, scope=None):
        self.children = deque()

        self.parent = parent
        self.scope = scope or parent

    def add_child(self, child):
        self.children.append(child)
        return self

    def build(self, py_node):
        return self.__call_node_method('build_', py_node)

    def finalize(self, bonsai_node):
        return self.__call_node_method('finalize_', bonsai_node)

    def build_BinOp(self, py_node):
        op_name = operator_names[py_node.op.__class__]
        return PyOperator(self.scope, self.parent, op_name)

    def build_Expr(self, py_node):
        return CodeExpressionStatement(self.scope, self.parent, None)

    def build_Module(self, py_node):
        return PyModule()

    def build_Num(self, py_node):
        return py_node.n

    def finalize_PyOperator(self, bonsai_node):
        for child in self.children:
            bonsai_node._add(child)
        return bonsai_node

    def finalize_CodeExpressionStatement(self, bonsai_node):
        bonsai_node.expression = self.children[0]
        return bonsai_node

    def finalize_PyModule(self, bonsai_node):
        for child in self.children:
            bonsai_node._add(child)
        return bonsai_node


###############################################################################
# Visitor
###############################################################################


class BuilderVisitor(ast.NodeVisitor):

    @classmethod
    def with_builder(cls, self, visitor_method):
        def builder_visit(node):

            # start to build this node
            bonsai_node = self.builder.build(node)

            # build the children recursively
            defines_scope = visitor_method(node)
            children_scope = self.builder.scope if not defines_scope else None
            children_builder = PyBonsaiBuilder(bonsai_node, children_scope)
            children_visitor = cls(children_builder)
            children_visitor.generic_visit(node)

            # finalize this node
            bonsai_node = children_builder.finalize(bonsai_node)

            # return to parent
            self.builder.add_child(bonsai_node)

        return builder_visit

    def __init__(self, builder):
        ast.NodeVisitor.__init__(self)

        self.builder = builder

        for (name, method) in getmembers(self, isroutine):
            if name.startswith('visit_'):
                setattr(self, name, self.with_builder(self, method))

    def build(self, node):
        self.visit(node)
        return self.builder.children[0]

    def visit_BinOp(self, node):
        return False

    def visit_Expr(self, node):
        return False

    def visit_Module(self, node):
        return True

    def visit_Num(self, node):
        return False


###############################################################################
# Rest
###############################################################################


from os.path import abspath, dirname, join, realpath
file_name = realpath(join(dirname(abspath(__file__)), '..', '..', 'examples',
                          'py', 'examples.py'))

with open(file_name) as source:
    content = source.read()
    tree = ast.parse(content, file_name)
    bonsai_tree = BuilderVisitor(PyBonsaiBuilder()).build(tree)

    print(bonsai_tree.pretty_str())

    for child in bonsai_tree.walk_preorder():
        print('{} ({}): {!r} -- parent: {!r}'.format(
                type(child).__name__,
                id(child) % 100000,
                child,
                None if child.parent is None else id(child.parent) % 100000))
