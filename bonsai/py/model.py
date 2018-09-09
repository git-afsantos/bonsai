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

from ..model import (CodeEntity, CodeStatementGroup, CodeExpression,
                     CodeStatement, CodeOperator, CodeJumpStatement, SomeValue,
                     CodeReference, CodeVariable, CodeFunctionCall)

###############################################################################
# Language Model
###############################################################################

PyEntity = CodeEntity

PyStatementGroup = CodeStatementGroup

PyJumpStatement = CodeJumpStatement


class PyStatement(CodeStatement):
    def __init__(self, parent, scope):
        CodeStatement.__init__(self, parent, scope)

    def is_assignment(self):
        return isinstance(self, PyAssignment)


class PyAssignment(PyStatement, CodeOperator):
    def __init__(self, scope, parent, operator='=', result=None, args=None,
                 paren=False):
        CodeStatement.__init__(self, scope, parent)
        CodeOperator.__init__(self, scope, parent, operator, result, args,
                              paren)

    def is_assignment(self):
        return True

    def is_binary(self):
        return True

    def is_ternary(self):
        return False

    def is_unary(self):
        return False


class PyDel(PyStatement):
    def __init__(self, parent, scope, *targets):
        PyStatement.__init__(self, parent, scope)
        self.arguments = targets


# class PyLambda(PyExpression):
#     NAME = '(lambda)'
#     TYPE = 'lambda'
#
#     def __init__(self, scope, parent, paren=False):
#         PyExpression.__init__(self, scope, parent, self.NAME, self.TYPE, paren)


# ----- Expression Entities ---------------------------------------------------

PyExpression = CodeExpression

PyReference = CodeReference

PyValue = SomeValue

PyVariable = CodeVariable


class PyOperator(CodeOperator, PyExpression):
    _UNARY_TOKENS = ('~', 'not', '+', '-')

    _BINARY_TOKENS = ('and', 'or', '+', '-', '*', '/', '//', '%', '**', '<<',
                      '>>', '|', '^', '&', 'in', 'not in', 'is', 'is not')

    def __init__(self, scope, parent, name, args=None, result=None,
                 from_compare=True, paren=False):
        CodeOperator.__init__(self, scope, parent, name, result,
                              args=args, paren=paren)
        self.from_compare = from_compare

    @property
    def is_assignment(self):
        return False


class PyComprehension(PyExpression):
    PARENS = {
        'dict': ('{', '}'),
        'generator': ('(', ')'),
        'list': ('[', ']'),
        'set': ('{', '}'),
    }

    def __init__(self, scope, parent, name, expr, iters, ifs=None, result=None,
                 paren=False):
        PyExpression.__init__(self, scope, parent, name, result, paren)
        self.expr = expr
        self.iters = iters
        self.ifs = ifs

    def pretty_str(self, indent=0):
        inner_indent = ' ' * (indent + 1)
        indent = ' ' * indent

        iters = '\n'.join(
            '{}for {} in {}'.format(inner_indent, decls.pretty_str(indent=0),
                                    iterable.pretty_str(indent=0))
            for decls, iterable in self.iters
        )
        filters = '\n'.join(
            '{}if {}'.format(inner_indent, cond.pretty_str(indent=0))
            for cond in self.ifs
        )
        parens = self.PARENS[self.name]

        return '{open}\n{exp}\n{iters}\n{ifs}\n{indent}{close}'.format(
                open=parens[0], exp=self.expr.pretty_str(indent=inner_indent),
                iters=iters, ifs=filters, indent=indent, close=parens[1]
        )


class PyFunctionCall(CodeFunctionCall, PyExpression):
    def __init__(self, scope, parent, name, pos_args=(), named_args=(),
                 star_args=None, kw_args=None, result=None, paren=False):
        CodeFunctionCall.__init__(self, scope, parent, name, result, paren)

        for arg in pos_args:
            self._add(arg)

        self.named_args = named_args
        self.star_args = star_args
        self.kw_args = kw_args


class PyCompositeValue(PyValue):
    def __init__(self):
        pass
