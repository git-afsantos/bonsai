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
import sys
from copy import copy
from functools import partial
from itertools import takewhile, dropwhile
from os import path

from bonsai.py.model import PyGlobalScope
from bonsai.py.visitor import ASTPreprocessor, BuilderVisitor

###############################################################################
# AST Parsing
###############################################################################


class PyAstParser(object):
    @classmethod
    def find_file_in_dir(cls, module_name, directory):
        if not module_name:
            raise ValueError(module_name)

        module_path = path.join(directory, module_name.pop(0))

        if path.isdir(module_path):
            return (module_path
                    if not module_name
                    else cls.find_file_in_dir(module_name, module_path))

        if path.isfile(module_path + '.py'):
            return module_path

        raise IOError('{} not found'.format(module_path))

    def __init__(self, pythonpath=None, workspace=None):
        self.global_scope = PyGlobalScope()
        self.pythonpath = (pythonpath or []) + sys.path
        self.workspace = workspace

    def find_file_by_import(self, importing_path, imported_module):
        leading_dots = ''.join(takewhile(lambda c: c == '.',
                                         iter(imported_module)))
        parent_path = path.join(leading_dots[:2],
                                *('..' for _ in leading_dots[2:]))
        entity_name = imported_module[len(leading_dots):].split('.')

        if parent_path:
            file_dir = path.dirname(importing_path)
            pythonpath = [path.normpath(path.join(file_dir, parent_path))]
        else:
            pythonpath = self.pythonpath

        for directory in pythonpath:
            try:
                return self.find_file_in_dir(copy(entity_name), directory)
            except IOError:
                continue

        if imported_module in sys.builtin_module_names:
            return

        raise IOError('{} not found'.format(imported_module))

    def is_in_workspace(self, file_path):
        return file_path and file_path.startswith(self.workspace)

    def parse(self, file_path):
        print(file_path)
        with open(file_path) as source_file:
            content = source_file.read()

        py_tree = ASTPreprocessor().visit(ast.parse(content, file_path))
        bonsai_py_module, imported_names = (BuilderVisitor()
                                            .build(py_tree, file_path))

        bonsai_py_module.scope = self.global_scope
        bonsai_py_module.parent = self.global_scope
        bonsai_py_module.name = path.basename(path.splitext(file_path)[0])

        self.global_scope._add(bonsai_py_module)

        if imported_names:
            find_file = partial(self.find_file_by_import, file_path)
            file_paths = map(find_file, imported_names)
            for file_path in filter(self.is_in_workspace, file_paths):
                self.parse(file_path)

        return self.global_scope


###############################################################################
# Rest
###############################################################################

if __name__ == '__main__':
    import sys
    from os.path import abspath, dirname, join, realpath

    try:
        source_file = sys.argv[1]
    except IndexError:
        source_file = 'examples.py'

    file_name = realpath(join(dirname(abspath(__file__)), '..', '..',
                              'examples', 'py', source_file))
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

