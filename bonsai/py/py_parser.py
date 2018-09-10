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

import bonsai.model as bonsai_model
import bonsai.py.model as py_model

from collections import deque
from inspect import getmembers, isroutine

###############################################################################
# Builder
###############################################################################


def identity(x):
    return x


operator_names = {
    ast.Add: '+',
    ast.Sub: '-',
}


class PyBonsaiBuilder(object):
    """

    Holds a scope and a parent and builds children into results


    """

    def __init__(self, parent=None, scope=None):
        self.children = deque()

        self.parent = parent
        self.scope = scope or parent

    def add_child(self, child):
        self.children.append(child)
        return self

    def finalize(self, bonsai_node):
        method_name = 'finalize_' + bonsai_node.__class__.__name__
        return getattr(self, method_name, identity)(bonsai_node)

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
            bonsai_node, children_scope = visitor_method(node)

            # build the children recursively
            children_visitor = cls(bonsai_node, children_scope)
            children_visitor.generic_visit(node)

            # finalize this node
            bonsai_node = children_visitor.builder.finalize(bonsai_node)

            # return to parent
            self.builder.add_child(bonsai_node)

        return builder_visit

    def __init__(self, parent=None, scope=None):
        ast.NodeVisitor.__init__(self)

        self.builder = PyBonsaiBuilder(parent, scope)

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

    def visit_BinOp(self, py_node):
        op_name = operator_names[py_node.op.__class__]
        bonsai_node = py_model.PyOperator(self.scope, self.parent, op_name)
        return bonsai_node, self.scope

    def visit_Expr(self, py_node):
        bonsai_node = bonsai_model.CodeExpressionStatement(self.scope,
                                                           self.parent, None)
        return bonsai_node, self.scope

    def visit_Module(self, py_node):
        bonsai_node = py_model.PyModule()
        return bonsai_node, bonsai_node

    def visit_Num(self, py_node):
        return py_node.n, self.scope


###############################################################################
# Rest
###############################################################################


from os.path import abspath, dirname, join, realpath
file_name = realpath(join(dirname(abspath(__file__)), '..', '..', 'examples',
                          'py', 'examples.py'))

with open(file_name) as source:
    content = source.read()
    tree = ast.parse(content, file_name)
    bonsai_tree = BuilderVisitor().build(tree)

    print(bonsai_tree.pretty_str())

    for child in bonsai_tree.walk_preorder():
        print('{} ({}): {!r} -- parent: {!r}'.format(
                type(child).__name__,
                id(child) % 100000,
                child,
                None if child.parent is None else id(child.parent) % 100000))
