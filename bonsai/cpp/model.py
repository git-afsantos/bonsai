
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

class CppEntity(object):
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
            for cppobj in self.walk_preorder():
                if isinstance(cppobj, cls):
                    objects.append(cppobj)
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
        cppobj = self.parent
        while not cppobj is None and not isinstance(cppobj, cls):
            cppobj = cppobj.parent
        return cppobj


    def pretty_str(self, indent = 0):
        return (" " * indent) + self.__str__()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "[unknown]"


class CppStatementGroup(object):
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

class CppVariable(CppEntity):
    def __init__(self, scope, parent, id, name, result):
        CppEntity.__init__(self, scope, parent)
        self.id = id
        self.name = name
        self.full_type = result
        self.result = result[6:] if result.startswith("const ") else result
        self.value = None
        self.member_of = None
        self.references = []
        self.writes = []

    @property
    def is_local(self):
        return (isinstance(self.scope, CppStatement)
                or (isinstance(self.scope, CppFunction)
                    and not self in self.scope.parameters))

    @property
    def is_global(self):
        return isinstance(self.scope, (CppGlobalScope, CppNamespace))

    @property
    def is_parameter(self):
        return (isinstance(self.scope, CppFunction)
                and self in self.scope.parameters)

    @property
    def is_member(self):
        return isinstance(self.scope, CppClass)


    def _add(self, cppobj):
        assert isinstance(cppobj, CppExpression.TYPES)
        self.value = cppobj

    def _children(self):
        if isinstance(self.value, CppEntity):
            yield self.value


    def pretty_str(self, indent = 0):
        indent = " " * indent
        return "{}{} {} = {}".format(indent, self.result, self.name,
                                     pretty_str(self.value))

    def __repr__(self):
        return "[{}] {} = ({})".format(self.result, self.name, self.value)


class CppFunction(CppEntity, CppStatementGroup):
    def __init__(self, scope, parent, id, name, result):
        CppEntity.__init__(self, scope, parent)
        self.id = id
        self.name = name
        self.full_type = result
        self.result = result[6:] if result.startswith("const ") else result
        self.parameters = []
        self.template_parameters = 0
        self.body = CppBlock(self, self, explicit = True)
        self.member_of = None
        self.references = []
        self._definition = self

    @property
    def is_definition(self):
        return self._definition is self

    @property
    def is_constructor(self):
        return self.member_of and self.name == self.member_of.name

    def _add(self, cppobj):
        assert isinstance(cppobj, (CppStatement, CppExpression))
        self.body._add(cppobj)

    def _children(self):
        for cppobj in self.parameters:
            yield cppobj
        for cppobj in self.body._children():
            yield cppobj

    def _afterpass(self):
        if hasattr(self, "_fi"):
            return
        fi = 0
        for cppobj in self.walk_preorder():
            cppobj._fi = fi
            fi += 1
            if isinstance(cppobj, CppOperator) and cppobj.is_assignment:
                if cppobj.arguments and isinstance(cppobj.arguments[0],
                                                   CppReference):
                    # left side can be CALL_EXPR: operator[] or operator()
                    # or ARRAY_SUBSCRIPT_EXPR: a[]
                    # or UNARY_OPERATOR: *a
                    # or PAREN_EXPR: (*a)
                    var = cppobj.arguments[0].reference
                    if isinstance(var, CppVariable):
                        var.writes.append(cppobj)


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


class CppClass(CppEntity):
    def __init__(self, scope, parent, id, name):
        CppEntity.__init__(self, scope, parent)
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

    def _add(self, cppobj):
        assert isinstance(cppobj, (CppFunction, CppVariable, CppClass))
        self.members.append(cppobj)
        cppobj.member_of = self

    def _children(self):
        for cppobj in self.members:
            yield cppobj

    def _afterpass(self):
        for cppobj in self.members:
            if isinstance(cppobj, CppVariable):
                continue
            if not cppobj.is_definition:
                cppobj._definition.member_of = self
            cppobj._afterpass()


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


class CppNamespace(CppEntity):
    def __init__(self, scope, parent, name):
        CppEntity.__init__(self, scope, parent)
        self.name = name
        self.children = []

    def _add(self, cppobj):
        assert isinstance(cppobj, (CppNamespace, CppClass,
                                    CppFunction, CppVariable))
        self.children.append(cppobj)

    def _children(self):
        for cppobj in self.children:
            yield cppobj

    def _afterpass(self):
        for cppobj in self.children:
            if isinstance(cppobj, CppVariable):
                continue
            cppobj._afterpass()


    def pretty_str(self, indent = 0):
        spaces = " " * indent
        pretty = spaces + "namespace " + self.name + ":\n"
        pretty += "\n\n".join([c.pretty_str(indent + 2) for c in self.children])
        return pretty

    def __repr__(self):
        return "[namespace {}]".format(self.name)


class CppGlobalScope(CppEntity):
    def __init__(self):
        CppEntity.__init__(self, None, None)
        self.children = []

    def _add(self, cppobj):
        assert isinstance(cppobj, (CppNamespace, CppClass,
                                    CppFunction, CppVariable))
        self.children.append(cppobj)

    def _children(self):
        for cppobj in self.children:
            yield cppobj

    def _afterpass(self):
        for cppobj in self.children:
            if isinstance(cppobj, CppVariable):
                continue
            cppobj._afterpass()


    def pretty_str(self, indent = 0):
        return "\n\n".join([cppobj.pretty_str(indent = indent) \
                            for cppobj in self.children])


# ----- Expression Entities ---------------------------------------------------

class CppExpression(CppEntity):
    def __init__(self, scope, parent, name, result, paren = False):
        CppEntity.__init__(self, scope, parent)
        self.name = name
        self.full_type = result
        self.result = result[6:] if result.startswith("const ") else result
        self.parenthesis = paren

    LITERALS = (int, long, float, bool, basestring)

    @property
    def function(self):
        return self._lookup_parent(CppFunction)

    @property
    def statement(self):
        return self._lookup_parent(CppStatement)

    def pretty_str(self, indent = 0):
        if self.parenthesis:
            return (" " * indent) + "(" + self.name + ")"
        return (" " * indent) + self.name

    def __repr__(self):
        return "[{}] {}".format(self.result, self.name)


class SomeCpp(CppExpression):
    def __init__(self, result):
        CppExpression.__init__(self, None, None, result, result)

SomeCpp.INTEGER = SomeCpp("int")
SomeCpp.FLOATING = SomeCpp("float")
SomeCpp.CHARACTER = SomeCpp("char")
SomeCpp.BOOL = SomeCpp("bool")


CppExpression.TYPES = (int, long, float, bool,
                       basestring, SomeCpp, CppExpression)


class CppReference(CppExpression):
    def __init__(self, scope, parent, name, result):
        CppExpression.__init__(self, scope, parent, name, result)
        self.field_of = None
        self.reference = None

    def _set_field(self, cppobj):
        assert isinstance(cppobj, CppExpression)
        self.field_of = cppobj

    def _children(self):
        if self.field_of:
            yield self.field_of


    def pretty_str(self, indent = 0):
        spaces = (" " * indent)
        pretty = "{}({})" if self.parenthesis else "{}{}"
        name = self.name
        if self.field_of:
            o = self.field_of
            if isinstance(o, CppFunctionCall) and o.name == "operator->":
                name = o.arguments[0].pretty_str() + "->" + self.name
            else:
                name = o.pretty_str() + "." + self.name
        return pretty.format(spaces, name)

    def __str__(self):
        return "#" + self.name

    def __repr__(self):
        if self.field_of:
            return "[{}] ({}).{}".format(self.result, self.field_of, self.name)
        return "[{}] #{}".format(self.result, self.name)


class CppOperator(CppExpression):
    _UNARY_TOKENS = ("+", "-", "++", "--", "*", "&", "!", "~")

    _BINARY_TOKENS = ("+", "-", "*", "/", "%", "&", "|", "^", "<<", ">>",
                      "<", ">", "<=", ">=", "==", "!=", "&&", "||", "=",
                      "+=", "-=", "*=", "/=", "%=", "<<=", ">>=", "&=",
                      "|=", "^=", ",")

    def __init__(self, scope, parent, name, result, args = None):
        CppExpression.__init__(self, scope, parent, name, result)
        self.arguments = args or ()

    @property
    def is_unary(self):
        return len(self.arguments) == 1

    @property
    def is_binary(self):
        return len(self.arguments) == 2

    @property
    def is_assignment(self):
        return (self.name == "=" or self.name == "+=" or self.name == "-="
                or self.name == "*=" or self.name == "/=" or self.name == "%="
                or self.name == "&=" or self.name == "|=" or self.name == "^="
                or self.name == "<<=" or self.name == ">>=")

    def _add(self, cppobj):
        assert isinstance(cppobj, CppExpression.TYPES)
        self.arguments = self.arguments + (cppobj,)

    def _children(self):
        for cppobj in self.arguments:
            if isinstance(cppobj, CppExpression):
                yield cppobj


    def pretty_str(self, indent = 0):
        indent = (" " * indent)
        pretty = "{}({})" if self.parenthesis else "{}{}"
        operator = self.name
        if self.is_unary:
            if self.name.startswith("_"):
                operator = pretty_str(self.arguments[0]) + self.name[1:]
            else:
                operator += pretty_str(self.arguments[0])
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


class CppFunctionCall(CppExpression):
    def __init__(self, scope, parent, name, result):
        CppExpression.__init__(self, scope, parent, name, result)
        self.full_name = name
        self.template = None
        self.arguments = ()
        self.method_of = None
        self.reference = None

    @property
    def is_constructor(self):
        result = self.result.split("::")[-1]
        if result.endswith(" *"):
            result = result[:-2]
        return result == self.name

    def _add(self, cppobj):
        assert isinstance(cppobj, CppExpression.TYPES)
        self.arguments = self.arguments + (cppobj,)

    def _set_method(self, cppobj):
        assert isinstance(cppobj, CppExpression)
        self.method_of = cppobj
        self.full_name = cppobj.result + "::" + self.name

    def _children(self):
        if self.method_of:
            yield self.method_of
        for cppobj in self.arguments:
            if isinstance(cppobj, CppExpression):
                yield cppobj


    def pretty_str(self, indent = 0):
        indent = " " * indent
        pretty = "{}({})" if self.parenthesis else "{}{}"
        call = self.name
        operator = self.name[8:]
        args = [pretty_str(arg) for arg in self.arguments]
        if operator in CppOperator._BINARY_TOKENS:
            call = "{} {} {}".format(args[0], operator, args[1])
        else:
            temp = "<" + ",".join(self.template) + ">" if self.template else ""
            args = ", ".join(args)
            if self.method_of:
                o = self.method_of
                if isinstance(o, CppFunctionCall) and o.name == "operator->":
                    call = "{}->{}{}({})".format(o.arguments[0].pretty_str(),
                                                 self.name, temp, args)
                else:
                    call = "{}.{}{}({})".format(o.pretty_str(),
                                                self.name, temp, args)
            elif self.is_constructor:
                call = "new {}{}({})".format(self.name, temp, args)
            else:
                call = "{}{}({})".format(self.name, temp, args)
        return pretty.format(indent, call)

    def __repr__(self):
        temp = "<" + ",".join(self.template) + ">" if self.template else ""
        args = ", ".join([str(arg) for arg in self.arguments])
        if self.is_constructor:
            return "[{}] new {}({})".format(self.result, self.name, args)
        if self.method_of:
            return "[{}] {}.{}{}({})".format(self.result, self.method_of.name,
                                           self.name, temp, args)
        return "[{}] {}{}({})".format(self.result, self.name, temp, args)


class CppDefaultArgument(CppExpression):
    def __init__(self, scope, parent, result):
        CppExpression.__init__(self, scope, parent, "(default)", result)

# ----- Statement Entities ----------------------------------------------------

class CppStatement(CppEntity):
    def __init__(self, scope, parent):
        CppEntity.__init__(self, scope, parent)
        self._si = -1

    @property
    def function(self):
        return self._lookup_parent(CppFunction)


class CppJumpStatement(CppStatement):
    def __init__(self, scope, parent, name):
        CppStatement.__init__(self, scope, parent)
        self.name = name
        self.value = None

    def _add(self, cppobj):
        assert isinstance(cppobj, CppExpression.TYPES)
        self.value = cppobj

    def _children(self):
        if isinstance(self.value, CppExpression):
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


class CppExpressionStatement(CppStatement):
    def __init__(self, scope, parent, expression = None):
        CppStatement.__init__(self, scope, parent)
        self.expression = expression

    def _children(self):
        if isinstance(self.expression, CppExpression):
            yield self.expression

    def pretty_str(self, indent = 0):
        return pretty_str(self.expression, indent = indent)

    def __repr__(self):
        return repr(self.expression)


class CppBlock(CppStatement, CppStatementGroup):
    def __init__(self, scope, parent, explicit = True):
        CppStatement.__init__(self, scope, parent)
        self.body = []
        self.explicit = explicit

    def statement(self, i):
        return self.body[i]

    def _add(self, cppobj):
        assert isinstance(cppobj, CppStatement)
        cppobj._si = len(self.body)
        self.body.append(cppobj)

    def _children(self):
        for cppobj in self.body:
            yield cppobj


    def pretty_str(self, indent = 0):
        if self.body:
            return "\n".join([stmt.pretty_str(indent) for stmt in self.body])
        else:
            return (" " * indent) + "[empty]"

    def __repr__(self):
        return str(self.body)


class CppDeclaration(CppStatement):
    def __init__(self, scope, parent):
        CppStatement.__init__(self, scope, parent)
        self.variables = []

    def _add(self, cppobj):
        assert isinstance(cppobj, CppVariable)
        self.variables.append(cppobj)

    def _children(self):
        for cppobj in self.variables:
            yield cppobj


    def pretty_str(self, indent = 0):
        spaces = " " * indent
        return spaces + ", ".join([v.pretty_str() for v in self.variables])

    def __repr__(self):
        return str(self.variables)


class CppControlFlow(CppStatement, CppStatementGroup):
    def __init__(self, scope, parent, name):
        CppStatement.__init__(self, scope, parent)
        self.name       = name
        self.condition  = True
        self.body       = CppBlock(scope, self, explicit = False)

    def get_branches(self):
        return [(self.condition, self.body)]

    def _set_condition(self, condition):
        assert isinstance(condition, CppExpression.TYPES)
        self.condition = condition

    def _set_body(self, body):
        assert isinstance(body, CppStatement)
        if isinstance(body, CppBlock):
            self.body = body
        else:
            self.body._add(body)

    def _children(self):
        if isinstance(self.condition, CppExpression):
            yield self.condition
        for cppobj in self.body._children():
            yield cppobj

    def __repr__(self):
        return "{} {}".format(self.name, self.get_branches())


class CppConditional(CppControlFlow):
    def __init__(self, scope, parent):
        CppControlFlow.__init__(self, scope, parent, "if")
        self.else_body = CppBlock(scope, self, explicit = False)

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
        assert isinstance(body, CppStatement)
        if isinstance(body, CppBlock):
            self.else_body = body
        else:
            self.else_body._add(body)

    def __len__(self):
        return len(self.body) + len(self.else_body)

    def _children(self):
        if isinstance(self.condition, CppExpression):
            yield self.condition
        for cppobj in self.body._children():
            yield cppobj
        for cppobj in self.else_body._children():
            yield cppobj


    def pretty_str(self, indent = 0):
        spaces = " " * indent
        condition = pretty_str(self.condition)
        pretty = spaces + "if (" + condition + "):\n"
        pretty += self.body.pretty_str(indent = indent + 2)
        if self.else_body:
            pretty += "\n" + spaces + "else:\n"
            pretty += self.else_body.pretty_str(indent = indent + 2)
        return pretty


class CppLoop(CppControlFlow):
    def __init__(self, scope, parent, name):
        CppControlFlow.__init__(self, scope, parent, name)
        self.declarations = None
        self.increment = None

    def _set_declarations(self, declarations):
        assert isinstance(declarations, CppStatement)
        self.declarations = declarations
        declarations.scope = self.body

    def _set_increment(self, statement):
        assert isinstance(statement, CppStatement)
        self.increment = statement
        statement.scope = self.body

    def _children(self):
        if self.declarations:
            yield self.declarations
        if isinstance(self.condition, CppExpression):
            yield self.condition
        if self.increment:
            yield self.increment
        for cppobj in self.body._children():
            yield cppobj


    def pretty_str(self, indent = 0):
        spaces = " " * indent
        condition = pretty_str(self.condition)
        if self.name == "while":
            pretty = spaces + "while (" + condition + "):\n"
            pretty += self.body.pretty_str(indent = indent + 2)
        elif self.name == "do":
            pretty = spaces + "do:\n"
            pretty += self.body.pretty_str(indent = indent + 2)
            pretty += "\n" + spaces + "while (" + condition + ")"
        elif self.name == "for":
            v = self.declarations.pretty_str() if self.declarations else ""
            i = self.increment.pretty_str(indent = 1) if self.increment else ""
            pretty = spaces + "for ({}; {};{}):\n".format(v, condition, i)
            pretty += self.body.pretty_str(indent = indent + 2)
        return pretty


class CppSwitch(CppControlFlow):
    def __init__(self, scope, parent):
        CppControlFlow.__init__(self, scope, parent, "switch")
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
    if isinstance(something, CppEntity):
        return something.pretty_str(indent = indent)
    else:
        return (" " * indent) + repr(something)
