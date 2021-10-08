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

from __future__ import division
from __future__ import unicode_literals

import ast

import bonsai.py.model as py_model

from inspect import getmembers, isroutine

from bonsai.py import composite_names, comprehension_names, operator_names
from bonsai.py.builder import PyBonsaiBuilder


###############################################################################
# Transformer
###############################################################################


class Bool(ast.expr):
    def __init__(self, name_node):
        ast.expr.__init__(self, lineno=name_node.lineno,
                          col_offset=name_node.col_offset)
        self._fields = self._fields + ('b',)

        self.b = True if name_node.id == 'True' else False


class NoneAST(ast.expr):
    def __init__(self, name_node):
        ast.expr.__init__(self, lineno=name_node.lineno,
                          col_offset=name_node.col_offset)


class ASTPreprocessor(ast.NodeTransformer):
    name_mappings = {
        'False': Bool,
        'None': NoneAST,
        'True': Bool,
    }

    print_name = ast.Name('print', ast.Load())

    def visit_Name(self, n):
        try:
            return self.name_mappings[n.id](n)
        except KeyError:
            return n

    def visit_Print(self, n):
        args = (n.values[0].elts
                if len(n.values) == 1 and isinstance(n.values[0], ast.Tuple)
                else n.values)
        keywords = ([ast.keyword('file', n.dest, lineno=n.lineno,
                                 col_offset=n.col_offset)]
                    if n.dest is not None
                    else None)
        return ast.Call(self.print_name, args, keywords, None, None,
                        lineno=n.lineno, col_offset=n.col_offset)


###############################################################################
# Visitor
###############################################################################


variable_contexts = {
    ast.AugLoad: py_model.PyVariableContext.REFERENCE,
    ast.AugStore: py_model.PyVariableContext.DEFINITION,
    ast.Del: py_model.PyVariableContext.DELETION,
    ast.Load: py_model.PyVariableContext.REFERENCE,
    ast.Param: py_model.PyVariableContext.PARAMETER,
    ast.Store: py_model.PyVariableContext.DEFINITION,
}


class BuilderVisitor(ast.NodeVisitor):

    @classmethod
    def with_builder(cls, visitor_method):
        def builder_visit(self, node):
            # start to build this node
            bonsai_node, children_scope, props = visitor_method(node)
            if isinstance(bonsai_node, py_model.PyEntity):
                bonsai_node.file = self.file_name
                bonsai_node.line = getattr(node, 'lineno', None)
                bonsai_node.column = getattr(node, 'col_offset', None)

            # build the children recursively
            children_visitor = cls(bonsai_node, children_scope, props)
            children_visitor.file_name = self.file_name
            children_visitor.generic_visit(node)

            # finalize this node
            children_builder = children_visitor.builder
            bonsai_node = children_builder.finalize(bonsai_node)

            # return to parent
            self.builder.add_child(bonsai_node,
                                   children_builder.imported_names)
            return bonsai_node, children_scope, props

        return builder_visit

    def _make_assign(self, py_node):
        operator_modifier = getattr(py_node, 'op', None)
        operator = operator_names.get(operator_modifier.__class__, '') + '='
        bonsai_node = py_model.PyAssignment(self.scope, self.parent, operator)
        return bonsai_node, self.scope, None

    def _make_composite_literal(self, py_node):
        comp_name = composite_names[py_node.__class__]
        bonsai_node = py_model.PyCompositeLiteral(self.scope, self.parent,
                                                  comp_name)
        return bonsai_node, self.scope, None

    def _make_comprehension(self, py_node):
        comp_name = comprehension_names[py_node.__class__] + '_comprehension'
        bonsai_node = py_model.PyComprehension(self.scope, self.parent,
                                               comp_name, None, None)
        return bonsai_node, bonsai_node, None

    def _make_name(self, py_node, name):
        context = variable_contexts[py_node.ctx.__class__]

        if context.is_reference:
            bonsai_node = py_model.PyReference(self.scope, self.parent, name,
                                               None)

        if context.is_definition:
            bonsai_node = py_model.PyVariable(self.scope, self.parent, name,
                                              context)

        return bonsai_node, self.scope, None

    def _make_operator(self, py_node):
        op_name = (operator_names.get(py_node.__class__)
                   or operator_names[py_node.op.__class__])
        bonsai_node = py_model.PyOperator(self.scope, self.parent, op_name)
        return bonsai_node, self.scope, {'ops': ()}

    def __init__(self, parent=None, scope=None, props=None):
        ast.NodeVisitor.__init__(self)

        self.builder = PyBonsaiBuilder(parent, scope, props)
        self.file_name = None

        for (name, method) in getmembers(self, isroutine):
            if name.startswith('visit_'):
                decorated_method = self.with_builder(method)
                bound_method = decorated_method.__get__(self, self.__class__)
                setattr(self, name, bound_method)

    @property
    def scope(self):
        return self.builder.scope

    @property
    def parent(self):
        return self.builder.parent

    def build(self, node, file_name):
        self.file_name = file_name
        self.visit(node)
        return self.builder.children[0], self.builder.imported_names

    def visit_alias(self, py_node):
        if py_node.asname is None:
            return py_node.name, self.scope, None

        bonsai_node = py_model.PyAlias(self.scope, self.parent, py_node.name,
                                       py_node.asname)
        return bonsai_node, self.scope, None

    def visit_arguments(self, py_node):
        bonsai_node = py_model.PyParameters(self.scope, self.parent,
                                            star_args=py_node.vararg,
                                            kw_args=py_node.kwarg)
        props = dict(self.builder.props,
                     args_count=len(py_node.args),
                     defaults_count=len(py_node.defaults))
        return bonsai_node, self.scope, props

    def visit_Assign(self, py_node):
        return self._make_assign(py_node)

    def visit_Assert(self, py_node):
        return py_model.PyDummyBlock(self.scope, self.parent), self.scope, None

    def visit_Attribute(self, py_node):
        return self._make_name(py_node, py_node.attr)

    def visit_AugAssign(self, py_node):
        return self._make_assign(py_node)

    def visit_BinOp(self, py_node):
        return self._make_operator(py_node)

    def visit_Bool(self, py_node):
        return py_node.b, self.scope, None

    def visit_BoolOp(self, py_node):
        return self._make_operator(py_node)

    def visit_Break(self, py_node):
        return py_model.PyDummyBlock(self.scope, self.parent), self.scope, None

    def visit_Continue(self, py_node):
        return py_model.PyDummyBlock(self.scope, self.parent), self.scope, None

    def visit_Call(self, py_node):
        # (lambda n: n)(9) is not handled yet

        bonsai_node = py_model.PyFunctionCall(self.scope, self.parent, None)
        if hasattr(py_node, 'starargs'):
            # python < 3.5
            props = {
                'args_count': len(py_node.args or ()),
                'kwargs_count': len(py_node.keywords or ()),
                'has_starargs': py_node.starargs is not None,
                'has_kwargs': py_node.kwargs is not None,
            }
        else:
            # python >= 3.5
            props = {
                'args_count': len(py_node.args or ()),
                'kwargs_count': len(py_node.keywords or ()),
                'has_starargs': any(isinstance(arg, ast.Starred)
                    for arg in (py_node.args or ())),
                'has_kwargs': any(not kw.arg
                    for kw in (py_node.keywords or ())),
            }
        return bonsai_node, self.scope, props

    def visit_ClassDef(self, py_node):
        bonsai_node = py_model.PyClass(self.scope, self.parent, py_node.name)
        props = {
            'bases_count': len(py_node.bases),
            'members_count': len(py_node.body),
        }
        return bonsai_node, bonsai_node, props

    def visit_Compare(self, py_node):
        # No chained comparisons here
        if len(py_node.ops) == 1:
            return self._make_operator(py_node.ops[0])

        # Chained comparison
        bonsai_node = py_model.PyOperator(self.scope, self.parent,
                                          operator_names[ast.And])
        props = {
            'ops': (operator_names[op.__class__] for op in py_node.ops)
        }
        return bonsai_node, self.scope, props

    def visit_comprehension(self, py_node):
        bonsai_node = py_model.PyComprehensionIterator(self.parent, None, None)
        return bonsai_node, self.scope, None

    def visit_Delete(self, py_node):
        bonsai_node = py_model.PyDelete(self.scope, self.parent)
        return bonsai_node, self.scope, None

    def visit_Dict(self, py_node):
        return self._make_composite_literal(py_node)

    def visit_DictComp(self, py_node):
        return self._make_comprehension(py_node)

    def visit_Exec(self, py_node):
        return py_model.PyDummyBlock(self.scope, self.parent), self.scope, None

    def visit_Expr(self, py_node):
        bonsai_node = py_model.PyExpressionStatement(self.scope, self.parent,
                                                     None)
        return bonsai_node, self.scope, None

    def visit_For(self, py_node):
        return py_model.PyDummyBlock(self.scope, self.parent), self.scope, None

    def visit_keyword(self, py_node):
        bonsai_node = py_model.PyKeyValue(self.scope, self.parent, py_node.arg)
        return bonsai_node, self.scope, None

    def visit_FunctionDef(self, py_node):
        bonsai_node = py_model.PyFunction(self.scope, self.parent,
                                          py_node.name)
        props = {
            'parent_scope': self.scope
        }
        return bonsai_node, bonsai_node, props

    def visit_Global(self, py_node):
        return py_model.PyDummyBlock(self.scope, self.parent), self.scope, None

    def visit_GeneratorExp(self, py_node):
        return self._make_comprehension(py_node)

    def visit_If(self, py_node):
        bonsai_node = py_model.PyConditional(self.scope, self.parent)

        props = {
            'then_count': len(py_node.body),
            'else_count': len(py_node.orelse)
        }
        return bonsai_node, self.scope, props

    def visit_IfExp(self, py_node):
        return self._make_operator(py_node)

    def visit_Import(self, py_node):
        bonsai_node = py_model.PyImport(self.scope, self.parent, level=0)
        props = {
            'modules_count': len(py_node.names),
            'entities_count': 0,
        }
        return bonsai_node, self.scope, props

    def visit_ImportFrom(self, py_node):
        bonsai_node = py_model.PyImport(self.scope, self.parent,
                                        (py_node.module,),
                                        level=py_node.level)
        props = {
            'modules_count': 0,
            'entities_count': len(py_node.names),
        }
        return bonsai_node, self.scope, props

    def visit_Lambda(self, py_node):
        props = {
            'parent_scope': self.scope
        }
        return py_model.PyDummyExpr(self.scope, self.parent), self.scope, props

    def visit_List(self, py_node):
        return self._make_composite_literal(py_node)

    def visit_ListComp(self, py_node):
        return self._make_comprehension(py_node)

    def visit_Module(self, py_node):
        bonsai_node = py_model.PyModule()
        return bonsai_node, bonsai_node, None

    def visit_Name(self, py_node):
        return self._make_name(py_node, py_node.id)

    def visit_NameConstant(self, py_node):
        return py_node.value, self.scope, None

    def visit_NoneAST(self, py_node):
        bonsai_node = py_model.PyNull(self.scope, self.parent)
        return bonsai_node, self.scope, None

    def visit_Num(self, py_node):
        return py_node.n, self.scope, None

    def visit_Pass(self, py_node):
        return py_model.PyDummyBlock(self.scope, self.parent), self.scope, None

    def visit_Raise(self, py_node):
        return py_model.PyDummyBlock(self.scope, self.parent), self.scope, None

    def visit_Return(self, py_node):
        return py_model.PyDummyBlock(self.scope, self.parent), self.scope, None

    def visit_Set(self, py_node):
        return self._make_composite_literal(py_node)

    def visit_SetComp(self, py_node):
        return self._make_comprehension(py_node)

    def visit_Str(self, py_node):
        return py_node.s, self.scope, None

    def visit_Subscript(self, py_node):
        return py_model.PyDummyExpr(self.scope, self.parent), self.scope, None

    def visit_TryFinally(self, py_node):
        return py_model.PyDummyBlock(self.scope, self.parent), self.scope, None

    def visit_TryExcept(self, py_node):
        return py_model.PyDummyBlock(self.scope, self.parent), self.scope, None

    def visit_Tuple(self, py_node):
        return self._make_composite_literal(py_node)

    def visit_UnaryOp(self, py_node):
        return self._make_operator(py_node)

    def visit_While(self, py_node):
        return py_model.PyDummyBlock(self.scope, self.parent), self.scope, None

    def visit_With(self, py_node):
        return py_model.PyDummyBlock(self.scope, self.parent), self.scope, None

    def visit_Yield(self, py_node):
        return py_model.PyDummyExpr(self.scope, self.parent), self.scope, None
