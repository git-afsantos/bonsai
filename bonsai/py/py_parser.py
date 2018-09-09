# Copyright (c) 2017 Davide Laezza
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

from ast import parse, NodeVisitor, BoolOp, iter_child_nodes
from collections import deque
from inspect import getmembers, isroutine

from ..model import CodeExpressionStatement
from ..parser import AnalysisData
from .model import PyOperator, PyModule

###############################################################################
# Visitor adapters
###############################################################################


class BuilderVisitor(NodeVisitor):

    @classmethod
    def with_build(cls, self, visitor_method):
        def builder_visit(node):
            build, parent, scope = visitor_method(node)

            visitor = cls(parent, scope)
            visitor.generic_visit(node)
            self.returns.append(build(*visitor.returns))

        return builder_visit

    def __init__(self, scope=None, parent=None):
        NodeVisitor.__init__(self)

        self.returns = deque()

        self.scope = scope
        self.parent = parent

        for (name, method) in getmembers(self, isroutine):
            if name.startswith('visit_'):
                setattr(self, name, self.with_build(self, method))

    def build(self, node):
        self.visit(node)
        return self.returns[0]

    def visit_BinOp(self, node):
        bonsai_node = PyOperator(self.scope, self.parent, node.op, (1, 2))

        def build(*children):
            for child in children:
                bonsai_node._add(child)
            return bonsai_node

        return build, bonsai_node, self.scope

    def visit_Exp(self, node):
        bonsai_node = CodeExpressionStatement(self.scope, self.parent, None)

        def build(child):
            bonsai_node.expression = child
            return bonsai_node

        return build, self.scope, self.parent

    def visit_Module(self, node):
        module = PyModule()
        self.scope = module

        def build(*children):
            for child in children:
                module._add(child)
            return module

        return build, module, module


from os.path import abspath, dirname, join, realpath
file_name = realpath(join(dirname(abspath(__file__)), '..', '..', 'examples',
                          'py', 'examples.py'))

with open(file_name) as source:
    content = source.read()
    tree = parse(content, file_name)
    bonsai_tree = BuilderVisitor().build(tree)

    print(bonsai_tree.pretty_str())

    # for node in bonsai_tree.returns[0].walk_preorder():
    #     print(node.pretty_str())
