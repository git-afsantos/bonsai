
#Copyright (c) 2017 Andre Santos
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

###############################################################################
# Language Model
###############################################################################

class CodeEntity(object):
    def __init__(self, scope, parent):
        self.scope = scope
        self.parent = parent
        self.file = None
        self.line = None
        self.column = None

    def walk_preorder(self):
        yield self
        for child in self._children():
            for descendant in child.walk_preorder():
                yield descendant

    def filter(self, cls, recursive = False):
        objects = []
        if recursive:
            for codeobj in self.walk_preorder():
                if isinstance(codeobj, cls):
                    objects.append(codeobj)
        else:
            if isinstance(self, cls):
                objects.append(self)
            for child in self._children():
                if isinstance(child, cls):
                    objects.append(child)
        return objects

    def _validity_check(self):
        return True

    def _children(self):
        return
        yield

    def _lookup_parent(self, cls):
        codeobj = self.parent
        while not codeobj is None and not isinstance(codeobj, cls):
            codeobj = codeobj.parent
        return codeobj


    def pretty_str(self, indent = 0):
        return (" " * indent) + self.__str__()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "[unknown]"


class CodeStatementGroup(object):
    def statement(self, i):
        return self.body.statement(i)

    def statement_after(self, i):
        """Return the statement after the ith one, or None."""
        try:
            return self.statement(i + 1)
        except IndexError as e:
            return None

    def __len__(self):
        return len(self.body)

# ----- Common Entities -------------------------------------------------------

class CodeVariable(CodeEntity):
    def __init__(self, scope, parent, id, name, result):
        CodeEntity.__init__(self, scope, parent)
        self.id = id
        self.name = name
        self.result = result
        self.value = None
        self.member_of = None
        self.references = []
        self.writes = []

    @property
    def is_local(self):
        return (isinstance(self.scope, CodeStatement)
                or (isinstance(self.scope, CodeFunction)
                    and not self in self.scope.parameters))

    @property
    def is_global(self):
        return isinstance(self.scope, (CodeGlobalScope, CodeNamespace))

    @property
    def is_parameter(self):
        return (isinstance(self.scope, CodeFunction)
                and self in self.scope.parameters)

    @property
    def is_member(self):
        return isinstance(self.scope, CodeClass)


    def _add(self, codeobj):
        assert isinstance(codeobj, CodeExpression.TYPES)
        self.value = codeobj

    def _children(self):
        if isinstance(self.value, CodeEntity):
            yield self.value


    def pretty_str(self, indent = 0):
        indent = " " * indent
        return "{}{} {} = {}".format(indent, self.result, self.name,
                                     pretty_str(self.value))

    def __repr__(self):
        return "[{}] {} = ({})".format(self.result, self.name, self.value)


class CodeFunction(CodeEntity, CodeStatementGroup):
    def __init__(self, scope, parent, id, name, result):
        CodeEntity.__init__(self, scope, parent)
        self.id = id
        self.name = name
        self.result = result
        self.parameters = []
        self.body = CodeBlock(self, self, explicit = True)
        self.member_of = None
        self.references = []
        self._definition = self

    @property
    def is_definition(self):
        return self._definition is self

    @property
    def is_constructor(self):
        return not self.member_of is None

    def _add(self, codeobj):
        assert isinstance(codeobj, (CodeStatement, CodeExpression))
        self.body._add(codeobj)

    def _children(self):
        for codeobj in self.parameters:
            yield codeobj
        for codeobj in self.body._children():
            yield codeobj

    def _afterpass(self):
        if hasattr(self, "_fi"):
            return
        fi = 0
        for codeobj in self.walk_preorder():
            codeobj._fi = fi
            fi += 1
            if isinstance(codeobj, CodeOperator) and codeobj.is_assignment:
                if codeobj.arguments and isinstance(codeobj.arguments[0],
                                                    CodeReference):
                    var = codeobj.arguments[0].reference
                    if isinstance(var, CodeVariable):
                        var.writes.append(codeobj)


    def pretty_str(self, indent = 0):
        spaces = " " * indent
        params = ", ".join(map(lambda p: p.result + " " + p.name,
                            self.parameters))
        if self.is_constructor:
            pretty = "{}{}({}):\n".format(spaces, self.name, params)
        else:
            pretty = "{}{} {}({}):\n".format(spaces, self.result,
                                             self.name, params)
        if not self._definition is self:
            pretty += spaces + "  [declaration]"
        else:
            pretty += self.body.pretty_str(indent + 2)
        return pretty

    def __repr__(self):
        params = ", ".join([str(p) for p in self.parameters])
        return "[{}] {}({})".format(self.result, self.name, params)


class CodeClass(CodeEntity):
    def __init__(self, scope, parent, id, name):
        CodeEntity.__init__(self, scope, parent)
        self.id = id
        self.name = name
        self.members = []
        self.superclasses = []
        self.member_of = None
        self.references = []
        self._definition = self

    @property
    def is_definition(self):
        return True # TODO

    def _add(self, codeobj):
        assert isinstance(codeobj, (CodeFunction, CodeVariable, CodeClass))
        self.members.append(codeobj)
        codeobj.member_of = self

    def _children(self):
        for codeobj in self.members:
            yield codeobj

    def _afterpass(self):
        for codeobj in self.members:
            if isinstance(codeobj, CodeVariable):
                continue
            if not codeobj.is_definition:
                codeobj._definition.member_of = self
            codeobj._afterpass()


    def pretty_str(self, indent = 0):
        spaces = " " * indent
        pretty = spaces + "class " + self.name
        if self.superclasses:
            superclasses = ", ".join(self.superclasses)
            pretty += "(" + superclasses + ")"
        pretty += ":\n"
        pretty += "\n\n".join([c.pretty_str(indent + 2) for c in self.members])
        return pretty

    def __repr__(self):
        return "[class {}]".format(self.name)


class CodeNamespace(CodeEntity):
    def __init__(self, scope, parent, name):
        CodeEntity.__init__(self, scope, parent)
        self.name = name
        self.children = []

    def _add(self, codeobj):
        assert isinstance(codeobj, (CodeNamespace, CodeClass,
                                    CodeFunction, CodeVariable))
        self.children.append(codeobj)

    def _children(self):
        for codeobj in self.children:
            yield codeobj

    def _afterpass(self):
        for codeobj in self.children:
            if isinstance(codeobj, CodeVariable):
                continue
            codeobj._afterpass()


    def pretty_str(self, indent = 0):
        spaces = " " * indent
        pretty = spaces + "namespace " + self.name + ":\n"
        pretty += "\n\n".join([c.pretty_str(indent + 2) for c in self.children])
        return pretty

    def __repr__(self):
        return "[namespace {}]".format(self.name)


class CodeGlobalScope(CodeEntity):
    def __init__(self):
        CodeEntity.__init__(self, None, None)
        self.children = []

    def _add(self, codeobj):
        assert isinstance(codeobj, (CodeNamespace, CodeClass,
                                    CodeFunction, CodeVariable))
        self.children.append(codeobj)

    def _children(self):
        for codeobj in self.children:
            yield codeobj

    def _afterpass(self):
        for codeobj in self.children:
            if isinstance(codeobj, CodeVariable):
                continue
            codeobj._afterpass()


    def pretty_str(self, indent = 0):
        return "\n\n".join([codeobj.pretty_str(indent = indent) \
                            for codeobj in self.children])


# ----- Expression Entities ---------------------------------------------------

class CodeExpression(CodeEntity):
    def __init__(self, scope, parent, name, result, paren = False):
        CodeEntity.__init__(self, scope, parent)
        self.name = name
        self.result = result
        self.parenthesis = paren

    LITERALS = (int, long, float, bool, basestring)

    @property
    def function(self):
        return self._lookup_parent(CodeFunction)

    @property
    def statement(self):
        return self._lookup_parent(CodeStatement)

    def pretty_str(self, indent = 0):
        if self.parenthesis:
            return (" " * indent) + "(" + self.name + ")"
        return (" " * indent) + self.name

    def __repr__(self):
        return "[{}] {}".format(self.result, self.name)


class SomeValue(CodeExpression):
    def __init__(self, result):
        CodeExpression.__init__(self, None, None, result, result)

SomeValue.INTEGER = SomeValue("int")
SomeValue.FLOATING = SomeValue("float")
SomeValue.CHARACTER = SomeValue("char")
SomeValue.BOOL = SomeValue("bool")


CodeExpression.TYPES = (int, long, float, bool,
                       basestring, SomeValue, CodeExpression)


class CodeReference(CodeExpression):
    def __init__(self, scope, parent, name, result):
        CodeExpression.__init__(self, scope, parent, name, result)
        self.field_of = None
        self.reference = None

    def _set_field(self, codeobj):
        assert isinstance(codeobj, CodeExpression)
        self.field_of = codeobj

    def _children(self):
        if self.field_of:
            yield self.field_of


    def pretty_str(self, indent = 0):
        spaces = (" " * indent)
        pretty = "{}({})" if self.parenthesis else "{}{}"
        name = self.name
        if self.field_of:
            name = self.field_of.pretty_str() + "." + self.name
        return pretty.format(spaces, name)

    def __str__(self):
        return "#" + self.name

    def __repr__(self):
        if self.field_of:
            return "[{}] ({}).{}".format(self.result, self.field_of, self.name)
        return "[{}] #{}".format(self.result, self.name)


class CodeOperator(CodeExpression):
    _UNARY_TOKENS = ("+", "-")

    _BINARY_TOKENS = ("+", "-", "*", "/", "%", "<", ">", "<=", ">=",
                      "==", "!=", "&&", "||", "=")

    def __init__(self, scope, parent, name, result, args = None):
        CodeExpression.__init__(self, scope, parent, name, result)
        self.arguments = args or ()

    @property
    def is_unary(self):
        return len(self.arguments) == 1

    @property
    def is_binary(self):
        return len(self.arguments) == 2

    @property
    def is_assignment(self):
        return self.name == "="

    def _add(self, codeobj):
        assert isinstance(codeobj, CodeExpression.TYPES)
        self.arguments = self.arguments + (codeobj,)

    def _children(self):
        for codeobj in self.arguments:
            if isinstance(codeobj, CodeExpression):
                yield codeobj


    def pretty_str(self, indent = 0):
        indent = (" " * indent)
        pretty = "{}({})" if self.parenthesis else "{}{}"
        if self.is_unary:
            operator = self.name + pretty_str(self.arguments[0])
        else:
            operator = "{} {} {}".format(pretty_str(self.arguments[0]),
                                         self.name,
                                         pretty_str(self.arguments[1]))
        return pretty.format(indent, operator)

    def __repr__(self):
        if self.is_unary:
            return "[{}] {}({})".format(self.result, self.name,
                                        self.arguments[0])
        elif self.is_binary:
            return "[{}] ({}){}({})".format(self.result, self.arguments[0],
                                            self.name, self.arguments[1])
        return "[{}] {}".format(self.result, self.name)


class CodeFunctionCall(CodeExpression):
    def __init__(self, scope, parent, name, result):
        CodeExpression.__init__(self, scope, parent, name, result)
        self.full_name = name
        self.arguments = ()
        self.method_of = None
        self.reference = None

    @property
    def is_constructor(self):
        return self.result == self.name

    def _add(self, codeobj):
        assert isinstance(codeobj, CodeExpression.TYPES)
        self.arguments = self.arguments + (codeobj,)

    def _set_method(self, codeobj):
        assert isinstance(codeobj, CodeExpression)
        self.method_of = codeobj

    def _children(self):
        if self.method_of:
            yield self.method_of
        for codeobj in self.arguments:
            if isinstance(codeobj, CodeExpression):
                yield codeobj


    def pretty_str(self, indent = 0):
        indent = " " * indent
        pretty = "{}({})" if self.parenthesis else "{}{}"
        call = self.name
        args = ", ".join([pretty_str(arg) for arg in self.arguments])
        if self.method_of:
            call = "{}.{}({})".format(self.method_of.pretty_str(),
                                        self.name, args)
        elif self.is_constructor:
            call = "new {}({})".format(self.name, args)
        else:
            call = "{}({})".format(self.name, args)
        return pretty.format(indent, call)

    def __repr__(self):
        args = ", ".join([str(arg) for arg in self.arguments])
        if self.is_constructor:
            return "[{}] new {}({})".format(self.result, self.name, args)
        if self.method_of:
            return "[{}] {}.{}({})".format(self.result, self.method_of.name,
                                           self.name, args)
        return "[{}] {}({})".format(self.result, self.name, args)


class CodeDefaultArgument(CodeExpression):
    def __init__(self, scope, parent, result):
        CodeExpression.__init__(self, scope, parent, "(default)", result)


# ----- Statement Entities ----------------------------------------------------

class CodeStatement(CodeEntity):
    def __init__(self, scope, parent):
        CodeEntity.__init__(self, scope, parent)
        self._si = -1

    @property
    def function(self):
        return self._lookup_parent(CodeFunction)


class CodeJumpStatement(CodeStatement):
    def __init__(self, scope, parent, name):
        CodeStatement.__init__(self, scope, parent)
        self.name = name
        self.value = None

    def _add(self, codeobj):
        assert isinstance(codeobj, CodeExpression.TYPES)
        self.value = codeobj

    def _children(self):
        if isinstance(self.value, CodeExpression):
            yield self.value


    def pretty_str(self, indent = 0):
        indent = " " * indent
        if not self.value is None:
            return indent + self.name + " " + pretty_str(self.value)
        return indent + self.name

    def __repr__(self):
        if not self.value is None:
            return self.name + " " + str(self.value)
        return self.name


class CodeExpressionStatement(CodeStatement):
    def __init__(self, scope, parent, expression = None):
        CodeStatement.__init__(self, scope, parent)
        self.expression = expression

    def _children(self):
        if isinstance(self.expression, CodeExpression):
            yield self.expression

    def pretty_str(self, indent = 0):
        return pretty_str(self.expression, indent = indent)

    def __repr__(self):
        return repr(self.expression)


class CodeBlock(CodeStatement, CodeStatementGroup):
    def __init__(self, scope, parent, explicit = True):
        CodeStatement.__init__(self, scope, parent)
        self.body = []
        self.explicit = explicit

    def statement(self, i):
        return self.body[i]

    def _add(self, codeobj):
        assert isinstance(codeobj, CodeStatement)
        codeobj._si = len(self.body)
        self.body.append(codeobj)

    def _children(self):
        for codeobj in self.body:
            yield codeobj


    def pretty_str(self, indent = 0):
        if self.body:
            return "\n".join([stmt.pretty_str(indent) for stmt in self.body])
        else:
            return (" " * indent) + "[empty]"

    def __repr__(self):
        return str(self.body)


class CodeDeclaration(CodeStatement):
    def __init__(self, scope, parent):
        CodeStatement.__init__(self, scope, parent)
        self.variables = []

    def _add(self, codeobj):
        assert isinstance(codeobj, CodeVariable)
        self.variables.append(codeobj)

    def _children(self):
        for codeobj in self.variables:
            yield codeobj


    def pretty_str(self, indent = 0):
        spaces = " " * indent
        return spaces + ", ".join([v.pretty_str() for v in self.variables])

    def __repr__(self):
        return str(self.variables)


class CodeControlFlow(CodeStatement, CodeStatementGroup):
    def __init__(self, scope, parent, name):
        CodeStatement.__init__(self, scope, parent)
        self.name       = name
        self.condition  = True
        self.body       = CodeBlock(scope, self, explicit = False)

    def get_branches(self):
        return [(self.condition, self.body)]

    def _set_condition(self, condition):
        assert isinstance(condition, CodeExpression.TYPES)
        self.condition = condition

    def _set_body(self, body):
        assert isinstance(body, CodeStatement)
        if isinstance(body, CodeBlock):
            self.body = body
        else:
            self.body._add(body)

    def _children(self):
        if isinstance(self.condition, CodeExpression):
            yield self.condition
        for codeobj in self.body._children():
            yield codeobj

    def __repr__(self):
        return "{} {}".format(self.name, self.get_branches())


class CodeConditional(CodeControlFlow):
    def __init__(self, scope, parent):
        CodeControlFlow.__init__(self, scope, parent, "if")
        self.else_body = CodeBlock(scope, self, explicit = False)

    @property
    def then_branch(self):
        return (self.condition, self.body)

    @property
    def else_branch(self):
        return (True, self.else_body)

    def statement(self, i):
        """Behaves as if "then" and "else" were concatenated.
            This code is just to avoid creating a new list and
            returning a custom exception message.
        """
        o = len(self.body)
        n = o + len(self.else_body)
        if i >= 0 and i < n:
            if i < o:
                return self.body.statement(i)
            return self.else_body.statement(i - o)
        elif i < 0 and i >= -n:
            if i >= o - n:
                return self.else_body.statement(i)
            return self.body.statement(i - o + n)
        raise IndexError("statement index out of range")

    def statement_after(self, i):
        k = i + 1
        o = len(self.body)
        n = o + len(self.else_body)
        if k > 0:
            if k < o:
                return self.body.statement(k)
            if k > o and k < n:
                return self.else_body.statement(k)
        if k < 0:
            if k < o - n and k > -n:
                return self.body.statement(k)
            if k > o - n:
                return self.else_body.statement(k)
        return None

    def get_branches(self):
        if self.else_branch:
            return [self.then_branch, self.else_branch]
        return [self.then_branch]

    def _add_default_branch(self, body):
        assert isinstance(body, CodeStatement)
        if isinstance(body, CodeBlock):
            self.else_body = body
        else:
            self.else_body._add(body)

    def __len__(self):
        return len(self.body) + len(self.else_body)

    def _children(self):
        if isinstance(self.condition, CodeExpression):
            yield self.condition
        for codeobj in self.body._children():
            yield codeobj
        for codeobj in self.else_body._children():
            yield codeobj


    def pretty_str(self, indent = 0):
        spaces = " " * indent
        condition = pretty_str(self.condition)
        pretty = spaces + "if (" + condition + "):\n"
        pretty += self.body.pretty_str(indent = indent + 2)
        if self.else_body:
            pretty += "\n" + spaces + "else:\n"
            pretty += self.else_body.pretty_str(indent = indent + 2)
        return pretty


class CodeLoop(CodeControlFlow):
    def __init__(self, scope, parent, name):
        CodeControlFlow.__init__(self, scope, parent, name)
        self.declarations = None
        self.increment = None

    def _set_declarations(self, declarations):
        assert isinstance(declarations, CodeStatement)
        self.declarations = declarations
        declarations.scope = self.body

    def _set_increment(self, statement):
        assert isinstance(statement, CodeStatement)
        self.increment = statement
        statement.scope = self.body

    def _children(self):
        if self.declarations:
            yield self.declarations
        if isinstance(self.condition, CodeExpression):
            yield self.condition
        if self.increment:
            yield self.increment
        for codeobj in self.body._children():
            yield codeobj


    def pretty_str(self, indent = 0):
        spaces = " " * indent
        condition = pretty_str(self.condition)
        v = self.declarations.pretty_str() if self.declarations else ""
        i = self.increment.pretty_str(indent = 1) if self.increment else ""
        pretty = spaces + "for ({}; {}; {}):\n".format(v, condition, i)
        pretty += self.body.pretty_str(indent = indent + 2)
        return pretty


class CodeSwitch(CodeControlFlow):
    def __init__(self, scope, parent):
        CodeControlFlow.__init__(self, scope, parent, "switch")
        self.cases = []
        self.default_case = None

    def _add_branch(self, value, statement):
        self.cases.append((value, statement))

    def _add_default_branch(self, statement):
        self.default_case = statement


    def pretty_str(self, indent = 0):
        spaces = " " * indent
        condition = pretty_str(self.condition)
        pretty = spaces + "switch (" + condition + "):\n"
        pretty += self.body.pretty_str(indent = indent + 2)
        return pretty


###############################################################################
# Helpers
###############################################################################

def pretty_str(something, indent = 0):
    if isinstance(something, CodeEntity):
        return something.pretty_str(indent = indent)
    else:
        return (" " * indent) + repr(something)
