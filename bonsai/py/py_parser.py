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
from functools import partial
from imp import find_module, load_module
from os import path

from bonsai.py.model import PyGlobalScope
from bonsai.py.visitor import ASTPreprocessor, BuilderVisitor

###############################################################################
# AST Parsing
###############################################################################


class PyAstParser(object):

    @classmethod
    def find_file(cls, pythonpath, module_names):
        if isinstance(module_names, basestring):
            module_names = module_names.split('.')

        if not module_names:
            raise ValueError

        module_name = module_names[0]
        try:
            open_file, pathname, description = find_module(module_name, pythonpath)
        except ImportError:
            return

        if open_file is None:
            module = load_module(module_name, open_file, pathname, description)
            return cls.find_file(module_names[1:],
                                 pythonpath + module.__path__)

        return open_file, pathname

    def __init__(self):
        self.global_scope = PyGlobalScope()

    def parse(self, file_path, source_file=None):
        if source_file is None:
            source_file = open(file_path)

        content = source_file.read()
        source_file.close()

        py_tree = ASTPreprocessor().visit(ast.parse(content, file_path))
        bonsai_py_module, imported_names = (BuilderVisitor()
                                            .build(py_tree, file_path))

        bonsai_py_module.scope = self.global_scope
        bonsai_py_module.parent = self.global_scope
        bonsai_py_module.name = path.basename(path.splitext(file_path)[0])

        self.global_scope._add(bonsai_py_module)

        if imported_names:
            find_file = partial(self.find_file, [path.dirname(file_path)])
            files = filter(bool, map(find_file, imported_names))
            for open_file, file_path in files:
                self.parse(file_path, open_file)

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

