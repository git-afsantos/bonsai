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
import itertools
import sys
from functools import partial
from itertools import takewhile
from os import path

from bonsai.analysis import CodeQuery
from bonsai.py.model import PyGlobalScope
from bonsai.py.visitor import ASTPreprocessor, BuilderVisitor

###############################################################################
# AST Parsing
###############################################################################


class FileFinder(object):
    def __init__(self, parser, pythonpath=None, workspace=None):
        self.parser = parser
        self.pythonpath = (pythonpath or []) + sys.path
        self.workspace = workspace

        self.top_level = {}

    def find_files(self, importing_path, imported_names):
        find_file = partial(self.find_file_by_import, importing_path)
        file_paths = map(find_file, imported_names)
        return filter(self.is_in_workspace, file_paths)

    def find_file_by_import(self, importing_path, imported_module):
        entity_name, pythonpath = self.make_absolute(importing_path,
                                                     imported_module)
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
        prefix_length = len(directory) + 1

        while module_splits:
            module_path = path.join(module_path, module_splits.pop(0))

            if path.isdir(module_path):
                node = self.parse_init(module_path,
                                       module_path[prefix_length:])
                try:
                    module_name = self.top_level[module_name]
                    return self.find_file_in_dir(module_name, directory)
                except KeyError:
                    pass

                if not module_splits:
                    return module_path

                if module_splits == ['*']:
                    self.find_star(node)

            file_path = module_path + '.py'
            if path.isfile(file_path):
                return file_path

        raise IOError('{} not found'.format(module_path))

    def find_star(self, node):
        if isinstance(node, basestring):
            node = self.parser._parse_file(node)[0]

        print(node)

        # print((CodeQuery(node)
        #     .all_definitions
        #     .where_name('__all__')
        #     .get()))
        print(node.pretty_str())

        top_level_names = (CodeQuery(node)
                           .definitions
                           .get())

        return top_level_names

    def is_in_workspace(self, file_path):
        return file_path and file_path.startswith(self.workspace)

    def make_absolute(self, importing_path, imported_module):
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

        return entity_name, pythonpath

    def parse_init(self, full_path, module_path):
        init_file = path.join(full_path, '__init__.py')
        if not path.isfile(init_file):
            return

        node, imported_names = self.parser._parse_file(init_file)
        exposed_names = [
            name
            for name in imported_names
            if name[0] == '.' and name[1] != '.'
        ]
        for name in exposed_names:
            if name.endswith('*'):
                node = self.find_file_by_import(init_file, name)
                print(node)
                self.find_star(node)
        # stars = itertools.chain.from_iterable(
        #     self.find_star(name)
        #     for name in exposed_names
        #     if name.endswith('*')
        # )

        module = module_path.replace('/', '.')
        for name in exposed_names:
            _, _, entity = name[1:].rpartition('.')
            full_name = '{}.{}'.format(module, name[1:])
            top_level_name = '{}.{}'.format(module, entity)
            self.top_level[top_level_name] = full_name

        return node


class PyAstParser(object):
    def _parse_file(self, file_path):
        with open(file_path) as source_file:
            content = source_file.read()
        print(file_path)

        py_tree = ASTPreprocessor().visit(ast.parse(content, file_path))
        node, imported_names = BuilderVisitor().build(py_tree, file_path)

        node.scope = self.global_scope
        node.parent = self.global_scope
        node.name = path.basename(path.splitext(file_path)[0])

        return node, imported_names

    def __init__(self, pythonpath=None, workspace=None):
        self.global_scope = PyGlobalScope()
        self.file_finder = FileFinder(self, pythonpath, workspace)

    def parse(self, file_path):
        node, imported_names = self._parse_file(file_path)
        self.global_scope._add(node)

        for source in self.file_finder.find_files(file_path, imported_names):
            self.parse(source)

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

