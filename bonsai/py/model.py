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

from ..model import *

###############################################################################
# Language Model
###############################################################################

PyEntity = CodeEntity

PyStatementGroup = CodeStatementGroup

PyJumpStatement = CodeJumpStatement


class PyModule(CodeGlobalScope):
    def _add(self, codeobj):
        self.children.append(codeobj)


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

parentheses = {
    'dict': ('{', '}'),
    'generator': ('(', ')'),
    'list': ('[', ']'),
    'set': ('{', '}'),
    'tuple': ('(', ')'),
}


PyExpression = CodeExpression

PyExpressionStatement = CodeExpressionStatement

PyReference = CodeReference

PyVariable = CodeVariable


class PyOperator(CodeOperator, PyExpression):
    _UNARY_TOKENS = ('~', 'not', '+', '-')

    _BINARY_TOKENS = ('and', 'or', '+', '-', '*', '/', '//', '%', '**', '<<',
                      '>>', '|', '^', '&', 'in', 'not in', 'is', 'is not')

    def __init__(self, scope, parent, name, args=None, result=None,
                 from_compare=False, paren=False):
        CodeOperator.__init__(self, scope, parent, name, result,
                              args=args, paren=paren)
        self.from_compare = from_compare

    @property
    def is_assignment(self):
        return False

    def __repr__(self):
        return ('[{0}] if({2})then({1})else({3})'.format(self.result,
                                                         *self.arguments)
                if self.is_ternary
                else CodeOperator.__repr__(self))

    def pretty_str(self, indent=0):
        if self.is_ternary:
            return 'if {1} then {0} else {2}'.format(*self.arguments)

        if self.name == 'not':
            return 'not {}'.format(*self.arguments)

        return CodeOperator.pretty_str(self, indent=indent)


class PyFunctionCall(CodeFunctionCall, PyExpression):
    def __init__(self, scope, parent, name, pos_args=(), named_args=(),
                 star_args=None, kw_args=None, result=None, paren=False):
        CodeFunctionCall.__init__(self, scope, parent, name, result, paren)

        for arg in pos_args:
            self._add(arg)

        self.named_args = named_args
        self.star_args = star_args
        self.kw_args = kw_args

    def pretty_str(self, indent=0):
        args = filter(lambda s: s != '', (
            ', '.join(map(pretty_str, self.arguments)),
            ', '.join(map(pretty_str, self.named_args)),
            ('*{}'.format(pretty_str(self.star_args))
                if self.star_args is not None
                else ''),
            ('**{}'.format(pretty_str(self.kw_args))
                if self.kw_args is not None
                else ''),
        ))

        name = ('{}.{}'.format(pretty_str(self.method_of), self.name)
                if self.method_of is not None
                else self.name)

        return '{}({})'.format(name, ', '.join(args))


class PyComprehension(PyExpression):
    name_suffix_length = len('-comprehension')

    def __init__(self, scope, parent, name, expr, iters, result=None,
                 paren=False):
        PyExpression.__init__(self, scope, parent, name, result, paren)
        self.expr = expr
        self.iters = iters

    def pretty_str(self, indent=0):
        parens = parentheses[self.name[0:-self.name_suffix_length]]
        iters = '\n'.join(
            pretty_str(iter, indent + 4)
            for iter in self.iters
        )

        return '{open}\n{exp}\n{iters}\n{indent}{close}'.format(
                open=parens[0], exp=pretty_str(self.expr, indent=indent + 4),
                iters=iters, indent=' ' * indent, close=parens[1]
        )


class PyComprehensionIterator(PyExpression):
    def __init__(self, parent, target, iter, filters=()):
        assert(isinstance(parent, PyComprehension))
        PyExpression.__init__(self, parent, parent, 'comprehension-iterator',
                              None)
        self.target = target
        self.iter = iter
        self.filters = filters

    def pretty_str(self, indent=0):
        indent = ' ' * indent

        filters = (''
                   if not self.filters
                   else '\n' + '\n'.join(
                       '{}if {}'.format(indent, pretty_str(cond))
                       for cond in self.filters)
                   )

        return '{}for {} in {}{}'.format(indent,
                                         pretty_str(self.target),
                                         pretty_str(self.iter),
                                         filters)


class PyKeyValue(PyExpression):
    def __init__(self, scope, parent, name, value=None, result=None):
        PyExpression.__init__(self, scope, parent, name, result, False)
        self.value = value

    def pretty_str(self, indent=0):
        return '{}{}: {}'.format(' ' * indent, pretty_str(self.name),
                                 pretty_str(self.value))

    def __repr__(self):
        return '[{}] {!r}: {!r}'.format(self.result, self.name, self.value)


class PyCompositeLiteral(CodeCompositeLiteral):
    def __init__(self, scope, parent, result, value=(), paren=False):
        CodeCompositeLiteral.__init__(self, scope, parent, result, value,
                                      paren)

    def pretty_str(self, indent=0):
        indent = ' ' * indent
        parens = parentheses[self.result]
        values = ', '.join(map(pretty_str, self.values))
        vals = '{open}{values}{close}'.format(
                open=parens[0], values=values, close=parens[1])

        return ('{}({})' if self.parenthesis else '{}{}').format(indent, vals)

