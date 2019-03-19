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
from enum import Enum

from bonsai.model import *
from bonsai.py import parentheses

###############################################################################
# Language Model
###############################################################################

# ----- Common Entities -------------------------------------------------------

PyEntity = CodeEntity
PyStatementGroup = CodeStatementGroup
PyBlock = CodeBlock


class PyGlobalScope(CodeGlobalScope):
    def __getitem__(self, key):
        return self.children[key]

    def _add(self, codeobj):
        # Python global scope is modeled as a container for modules
        assert isinstance(codeobj, PyModule)
        self.children.append(codeobj)


class PyModule(PyEntity):
    def __init__(self, scope=None, parent=None, name=None):
        PyEntity.__init__(self, scope, parent)
        self.name = name
        self.content = []

    @property
    def is_directory(self):
        """Return True if this module represents a module directory."""
        return all(isinstance(child, PyModule) for child in self._children())

    @property
    def is_file(self):
        """Return True if this module represents a python source file."""
        return not self.is_directory

    def __contains__(self, item):
        return item in self.content

    def __getitem__(self, key):
        return self.content[key]

    def __repr__(self):
        return '{!r}'.format(self.name)

    def _add(self, codeobj):
        assert (not isinstance(codeobj, PyGlobalScope)
                and (not self.content
                     or (self.is_file and not isinstance(codeobj, PyModule))
                     or (self.is_directory and isinstance(codeobj, PyModule))))
        self.content.append(codeobj)

    def _children(self):
        for child in self.content:
            yield child

    def pretty_str(self, indent=0):
        return '{}{}:\n\n{}'.format(' ' * indent, pretty_str(self.name),
                                    pretty_str(self.content, indent))


class PyVariableContext(Enum):
    DEFINITION = 0,
    DELETION = 1,
    PARAMETER = 2,
    REFERENCE = 3

    @property
    def is_definition(self):
        return self in (self.DEFINITION, self.PARAMETER)

    @property
    def is_reference(self):
        return self in (self.DELETION, self.REFERENCE)


class PyVariable(CodeVariable):
    def __init__(self, scope, parent, name, context, result=None):
        CodeVariable.__init__(self, scope, parent, 0, name, result)
        self.context = context
        self.attribute_of = None

    @property
    def is_attribute(self):
        return isinstance(self.attribute_of, CodeReference)

    @property
    def is_definition(self):
        return self.context.is_definition or self.is_parameter

    @property
    def is_parameter(self):
        return (self.context == PyVariableContext.PARAMETER
                or super(CodeVariable, self).is_parameter)

    def _children(self):
        if isinstance(self.attribute_of, CodeEntity):
            yield self.attribute_of

        if isinstance(self.value, CodeEntity):
            yield self.value

    def __repr__(self):
        return '{} :{}'.format(self.name, self.result or 'any')

    def pretty_str(self, indent=0):
        format_str = '{}{}'

        if self.is_attribute:
            format_str = '{}%s.{}' % pretty_str(self.attribute_of)

        if self.result is not None:
            format_str += ' :' + self.result

        return format_str.format(' ' * indent, self.name)


class PyFunction(CodeFunction):
    def __init__(self, scope, parent, name, result=None, params=None):
        CodeFunction.__init__(self, scope, parent, 0, name, result)
        self.parameters = params

    def _children(self):
        yield self.parameters

        for stmt in self.body._children():
            yield stmt

    @property
    def is_definition(self):
        return True

    def __repr__(self):
        return '[{}] {}({!r})'.format(self.result, self.name, self.parameters)

    def pretty_str(self, indent=0):
        body = '\n'.join(pretty_str(stmt, indent + 4) for stmt in self.body)
        return '{}{} {}({}):\n{}'.format(' ' * indent, self.result, self.name,
                                         pretty_str(self.parameters), body)


class PyParameters(CodeEntity):
    def __init__(self, scope, parent, pos_args=(), star_args=None,
                 kw_args=None):
        CodeEntity.__init__(self, scope, parent)
        self.pos_args = pos_args
        self.star_args = star_args
        self.kw_args = kw_args

    def _add(self, pos_arg, default=None):
        if default is not None:
            if isinstance(default, CodeEntity):
                key_val = PyKeyValue(default.scope, self, pos_arg, default)
                default.parent = key_val
            else:
                key_val = PyKeyValue(self.scope, self, pos_arg, default)

            pos_arg.parent = key_val
            pos_arg = key_val

        self.pos_args = self.pos_args + (pos_arg,)

    def _children(self):
        for pos_arg in self.pos_args:
            yield pos_arg

        if isinstance(self.star_args, CodeEntity):
            yield self.star_args

        if isinstance(self.kw_args, CodeEntity):
            yield self.kw_args

    def __contains__(self, item):
        return (item == self.star_args
                or item == self.kw_args
                or item in (arg.name if isinstance(arg, PyKeyValue) else arg
                            for arg in self.pos_args))

    def __repr__(self):
        pos_args = ', '.join(map(repr, self.pos_args))
        return '{}, *{!r}, **{!r}'.format(pos_args, self.star_args,
                                          self.kw_args)

    def pretty_str(self, indent=0):
        args = list(map(pretty_str, self.pos_args))

        if self.star_args is not None:
            args.append('*{}'.format(pretty_str(self.star_args)))

        if self.kw_args is not None:
            args.append('**{}'.format(pretty_str(self.kw_args)))

        return ', '.join(args)


class PyClass(CodeClass):
    def __init__(self, scope, parent, name):
        CodeClass.__init__(self, scope, parent, 0, name)

    @property
    def is_definition(self):
        return True

    def _add(self, codeobj):
        self.members.append(codeobj)
        codeobj.member_of = self


# ----- Statement Entities ----------------------------------------------------

class PyStatement(CodeStatement):
    # No bare aliasing, need to override is_assignment
    def __init__(self, scope, parent):
        CodeStatement.__init__(self, scope, parent)

    def is_assignment(self):
        return isinstance(self, PyAssignment)


# Needs to be redefined in order to inherit from PyStatement. Could be just an
# alias for CodeConditional otherwise
class PyConditional(CodeConditional, PyStatement):
    def __init__(self, *args, **kwargs):
        CodeConditional.__init__(self, *args, **kwargs)
        PyStatement.__init__(self, *args, **kwargs)


class PyAssignment(PyStatement, CodeOperator):
    def __init__(self, scope, parent, operator='=', args=(), result=None,
                 paren=False):
        CodeStatement.__init__(self, scope, parent)
        CodeOperator.__init__(self, scope, parent, operator, result, args,
                              paren)

    @property
    def is_assignment(self):
        return True

    @property
    def is_binary(self):
        return True

    @property
    def is_ternary(self):
        return False

    @property
    def is_unary(self):
        return False

    def _add(self, child):
        assert (isinstance(child, CodeExpression.TYPES)
                or isinstance(child, CodeVariable)
                and child.context == PyVariableContext.DEFINITION)

        self.arguments = self.arguments + (child,)

    def _children(self):
        for arg in self.arguments:
            if isinstance(arg, CodeEntity):
                yield arg

    def __repr__(self):
        # Multiple targets are used like this (`a` and `b`): a = b = 1
        targets = ' = '.join(map(repr, self.arguments[:-1]))
        return '[{}] {} {} {!r}'.format(self.result, targets, self.name,
                                        self.arguments[-1])

    def pretty_str(self, indent=0):
        # Multiple targets are used like this (`a` and `b`): a = b = 1
        targets = ' = '.join(map(pretty_str, self.arguments[:-1]))
        return '{}{} {} {}'.format(' ' * indent, targets, self.name,
                                   pretty_str(self.arguments[-1]))


class PyDelete(PyStatement):
    def __init__(self, scope, parent, targets=()):
        PyStatement.__init__(self, scope, parent)
        self.targets = targets

    def __repr__(self):
        return '[del] {}'.format(', '.join(map(repr, self.targets)))

    def _add(self, target):
        self.targets = self.targets + (target,)

    def _children(self):
        for target in self.targets:
            yield target

    def pretty_str(self, indent=0):
        targets = ', '.join(map(pretty_str, self.targets))
        return '{}del {}'.format(' ' * indent, targets)


class PyImport(PyStatement):
    def __init__(self, scope, parent, modules=(), entities=(), level=None):
        PyStatement.__init__(self, scope, parent)
        self.modules = modules
        self.entities = entities
        self.level = level

    @property
    def is_absolute(self):
        return self.level == 0

    @property
    def is_from(self):
        return len(self.entities) > 0

    @property
    def is_wildcard(self):
        return self.entities and self.entities[0] == '*'

    def _add_module(self, module):
        assert not self.is_from

        self.modules = self.modules + (module,)

    def _add_entity(self, entity):
        assert not self.is_wildcard

        self.entities = self.entities + (entity,)

    def _children(self):
        for module in self.modules:
            if isinstance(module, CodeEntity):
                yield module

        for entity in self.entities:
            if isinstance(entity, CodeEntity):
                yield entity

    def __repr__(self):
        if self.entities:
            # . as a module name is None
            module = '{}{}'.format('.' * self.level, self.modules[0] or '')
            entities = ', '.join(
                    '{}->({!r})'.format(module, entity)
                    for entity in self.entities
            )
            return '[import] {}'.format(entities)

        modules = ', '.join(map(repr, self.modules))
        return 'import {}'.format(modules)

    def pretty_str(self, indent=0):
        indent = ' ' * indent

        if self.entities:
            entities = ', '.join(map(pretty_str, self.entities))
            # . as a module name is None
            module = '{}{}'.format('.' * self.level, self.modules[0] or '')
            return '{}import {} from {}'.format(indent, entities, module)

        modules = ', '.join(map(pretty_str, self.modules))
        return '{}import {}'.format(indent, modules)


class PyAlias(PyStatement):
    def __init__(self, scope, parent, name, alias):
        PyStatement.__init__(self, scope, parent)
        self.name = name
        self.alias = alias

    def _children(self):
        return iter(())

    def __repr__(self):
        return '[alias] {} => {}'.format(self.alias, self.name)

    def pretty_str(self, indent=0):
        return '{}{} as {}'.format(' ' * indent, self.name, self.alias)


# ----- Expression Entities ---------------------------------------------------

PyExpression = CodeExpression

PyExpressionStatement = CodeExpressionStatement

PyReference = CodeReference

PyNull = CodeNull


class PyDummyExpr(PyExpression):
    def __init__(self, scope, parent):
        PyExpression.__init__(self, scope, parent, None, None)
        self._subtree = []

    def _add(self, child):
        self._subtree.append(child)

    def _children(self):
        for child in self._subtree:
            yield child


# class PyLambda(PyExpression):
#     NAME = '(lambda)'
#     TYPE = 'lambda'
#
#     def __init__(self, scope, parent, paren=False):
#       PyExpression.__init__(self, scope, parent, self.NAME, self.TYPE, paren)


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
        spaces = ' ' * indent

        if self.is_ternary:
            return '{0}if {2} then {1} else {3}'.format(spaces,
                                                        *self.arguments)

        if self.name == 'not':
            return '{}not {}'.format(spaces, *self.arguments)

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
        args = (list(map(pretty_str, self.arguments))
                + list(map(pretty_str, self.named_args)))

        if self.star_args is not None:
            args.append('*{}'.format(pretty_str(self.star_args)))

        if self.kw_args is not None:
            args.append('**{}'.format(pretty_str(self.kw_args)))

        name = ('{}.{}'.format(pretty_str(self.method_of), self.name)
                if self.method_of is not None
                else self.name)

        return '{}{}({})'.format(' ' * indent, name, ', '.join(args))


class PyComprehension(PyExpression):
    name_suffix_length = len('-comprehension')

    def __init__(self, scope, parent, name, expr, iters, result=None,
                 paren=False):
        PyExpression.__init__(self, scope, parent, name, result, paren)
        self.expr = expr
        self.iters = iters

    def _children(self):
        yield self.expr

        for iter in self.iters:
            yield iter

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

    def _children(self):
        yield self.target
        yield self.iter

        for filter in self.filters:
            yield filter

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

    def _children(self):
        if isinstance(self.name, CodeEntity):
            yield self.name

        if isinstance(self.value, CodeEntity):
            yield self.value

    def __repr__(self):
        return '[{}] {!r}: {!r}'.format(self.result, self.name, self.value)

    def pretty_str(self, indent=0):
        return '{}{}: {}'.format(' ' * indent, pretty_str(self.name),
                                 pretty_str(self.value))


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

