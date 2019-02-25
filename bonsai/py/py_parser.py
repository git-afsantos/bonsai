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
from glob import glob
from itertools import takewhile
from os import path

from bonsai.py.model import PyGlobalScope
from bonsai.py.visitor import ASTPreprocessor, BuilderVisitor

###############################################################################
# AST Parsing
###############################################################################


class PyAstParser(object):
    def _parse_file(self, file_path):
        with open(file_path) as source_file:
            content = source_file.read()

        py_tree = ASTPreprocessor().visit(ast.parse(content, file_path))
        node, imported_names = BuilderVisitor().build(py_tree, file_path)

        node.scope = self.global_scope
        node.parent = self.global_scope
        node.name = path.basename(path.splitext(file_path)[0])

        return node, imported_names

    def __init__(self, pythonpath=None, workspace=None):
        self.global_scope = PyGlobalScope()
        self.pythonpath = (pythonpath or []) + sys.path
        self.workspace = workspace

        self.top_level = {}

    def add_top_level(self, init_file, module):
        imported_names = self._parse_file(init_file)[1]
        exposed_names = (
            name[1:]
            for name in imported_names
            if name[0] == '.' and name[1] != '.'
        )
        for name in exposed_names:
            _, _, entity = name.rpartition('.')
            full_name = '{}.{}'.format(module, name)
            top_level_name = '{}.{}'.format(module, entity)
            self.top_level[top_level_name] = full_name

    def find_file_by_import(self, importing_path, imported_module):
        leading_dots = ''.join(takewhile(lambda c: c == '.',
                                         iter(imported_module)))
        parent_path = path.join(leading_dots[:2],
                                *('..' for _ in leading_dots[2:]))
        entity_name = imported_module[len(leading_dots):]

        if parent_path:
            file_dir = path.dirname(importing_path)
            pythonpath = [path.normpath(path.join(file_dir, parent_path))]
        else:
            pythonpath = self.pythonpath

        for directory in pythonpath:
            try:
                return self.find_file_in_dir(entity_name, directory)
            except IOError:
                pass

        if imported_module in sys.builtin_module_names:
            return

        raise IOError('{} not found'.format(imported_module))

    def find_file_in_dir(self, module_name, directory):
        module_name = self.top_level.get(module_name, module_name)
        module_splits = module_name.split('.')
        module_path = directory
        module_path_prefix_length = len(directory) + 1

        while module_splits:
            module_path = path.join(module_path, module_splits.pop(0))

            if path.isdir(module_path):
                init_file = path.join(module_path, '__init__.py')
                if path.isfile(init_file):
                    current_module = (module_path[module_path_prefix_length:]
                                      .replace('/', '.'))
                    self.add_top_level(init_file, current_module)

                    try:
                        module_name = self.top_level[module_name]
                        return self.find_file_in_dir(module_name, directory)
                    except KeyError:
                        pass

                if not module_splits:
                    return module_path

            if path.isfile(module_path + '.py'):
                return module_path

        raise IOError('{} not found'.format(module_path))

    def is_in_workspace(self, file_path):
        return file_path and file_path.startswith(self.workspace)

    def parse(self, file_path):
        print(file_path)
        imported_names = self._parse_file(file_path)[1]

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

