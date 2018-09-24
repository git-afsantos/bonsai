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

###############################################################################
# Global data
###############################################################################

composite_names = {
    ast.Dict: 'dict',
    ast.List: 'list',
    ast.Set: 'set',
    ast.Tuple: 'tuple',
}

comprehension_names = {
    ast.DictComp: 'dict',
    ast.GeneratorExp: 'generator',
    ast.ListComp: 'list',
    ast.SetComp: 'set',
}

operator_names = {
    ast.Add: '+',
    ast.And: 'and',
    ast.BitAnd: '&',
    ast.BitOr: '|',
    ast.BitXor: '^',
    ast.Div: '/',
    ast.Eq: '==',
    ast.FloorDiv: '//',
    ast.Gt: '>',
    ast.GtE: '>=',
    ast.IfExp: 'conditional-operator',
    ast.In: 'in',
    ast.Invert: '~',
    ast.Is: 'is',
    ast.IsNot: 'is not',
    ast.LShift: '<<',
    ast.Lt: '<',
    ast.LtE: '<=',
    ast.Mod: '%',
    ast.Mult: '*',
    ast.Not: 'not',
    ast.NotEq: '!=',
    ast.NotIn: 'not in',
    ast.Or: 'or',
    ast.Pow: '**',
    ast.RShift: '>>',
    ast.Sub: '-',
    ast.UAdd: '+',
    ast.USub: '-',
}
