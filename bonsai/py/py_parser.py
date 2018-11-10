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
from os import path

from bonsai.py.model import PyGlobalScope
from bonsai.py.visitor import ASTPreprocessor, BuilderVisitor

###############################################################################
# AST Parsing
###############################################################################


class PyAstParser(object):
    def __init__(self):
        self.global_scope = PyGlobalScope()

    def parse(self, file_path):
        file_path = path.abspath(file_path)

        with open(file_path) as source:
            content = source.read()

        py_tree = ASTPreprocessor().visit(ast.parse(content, file_path))
        bonsai_py_module = BuilderVisitor().build(py_tree)

        bonsai_py_module.scope = self.global_scope
        bonsai_py_module.parent = self.global_scope
        bonsai_py_module.name = path.basename(path.splitext(file_path)[0])

        self.global_scope._add(bonsai_py_module)
        return self.global_scope


###############################################################################
# Rest
###############################################################################

if __name__ == '__main__':
    from os.path import abspath, dirname, join, realpath

    file_name = realpath(join(dirname(abspath(__file__)), '..', '..',
                              'examples', 'py', 'examples.py'))
    bonsai_tree = PyAstParser().parse(file_name)

    # print(ast.dump(tree))
    # print(bonsai_tree.pretty_str())
    # bonsai_tree.pretty_str()

    for child in bonsai_tree.walk_preorder():
        print('{} ({}): {!r} -- parent: {!r}'.format(
                type(child).__name__,
                id(child) % 100000,
                child,
                None if child.parent is None else id(child.parent) % 100000))

