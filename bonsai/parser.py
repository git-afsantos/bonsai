
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
# Notes
###############################################################################

# This is not really an implementation. It is more or less a template,
# extracted from the clang cpp implementation, as an inspiration for other
# implementations.

###############################################################################
# Imports
###############################################################################

from __future__ import print_function
from builtins import object

import logging
import sys
from functools import partial

from .model import (
    CodeExpression, CodeExpressionStatement, CodeVariable, CodeGlobalScope
)


###############################################################################
# Language Entity Builders
###############################################################################

class CodeEntityBuilder(object):
    def __init__(self, scope, parent):
        self.scope  = scope
        self.parent = parent
        self.file   = None
        self.line   = None
        self.column = None

    def build(self, data):
        """Build an object for the current tree node and
            corresponding builders for the node's children.
            Return None if an object cannot be built.
            Return (object, [builders]) otherwise.
        """
        return None

    def _lookup_parent(self, cls):
        codeobj = self.parent
        while codeobj is not None and not isinstance(codeobj, cls):
            codeobj = codeobj.parent
        return codeobj


class CodeExpressionBuilder(CodeEntityBuilder):
    def __init__(self, scope, parent):
        CodeEntityBuilder.__init__(self, scope, parent)

    def build(self, data):
        return (self._build_literal()
                or self._build_reference(data)
                or self._build_operator()
                or self._build_function_call(data)
                or self._build_default_argument()
                or self._build_other(data))

    def _build_literal(self):
        return None

    def _build_reference(self, data):
        return None

    def _build_operator(self):
        return None

    def _build_function_call(self, data):
        return None

    def _build_default_argument(self):
        return None

    def _build_other(self, data):
        return None


class CodeStatementBuilder(CodeEntityBuilder):
    def __init__(self, scope, parent):
        CodeEntityBuilder.__init__(self, scope, parent)

    def build(self, data):
        return (self._build_declarations(data)
                or self._build_expression(data)
                or self._build_control_flow()
                or self._build_jump_statement()
                or self._build_block())

    def _build_expression(self, data):
        builder = CodeExpressionBuilder(self.scope, self.parent)
        result = builder.build(data)

        if result:
            expression = result[0]
            codeobj = CodeExpressionStatement(self.scope, self.parent,
                                              expression=expression)
            codeobj.file = self.file
            codeobj.line = self.line
            codeobj.column = self.column

            if isinstance(expression, CodeExpression):
                expression.parent = codeobj

            result = (codeobj, result[1])

        return result

    def _build_declarations(self, data):
        return None

    def _build_control_flow(self):
        return None

    def _build_jump_statement(self):
        return None

    def _build_block(self):
        return None


class CodeTopLevelBuilder(CodeEntityBuilder):
    def __init__(self, scope, parent, workspace=''):
        CodeEntityBuilder.__init__(self, scope, parent)
        self.workspace = workspace

    def build(self, data):
        return (self._build_variable(data)
                or self._build_function(data)
                or self._build_class(data)
                or self._build_namespace())

    def _build_variable(self, data):
        return None

    def _build_function(self, data):
        return None

    def _build_class(self, data):
        return None

    def _build_namespace(self):
        return None


###############################################################################
# AST Parsing
###############################################################################

class MultipleDefinitionError(Exception):
    pass

class AnalysisData(object):
    def __init__(self):
        # Mapping of the AST code entities, indexed by is
        self.entities = {}    # id -> CodeEntity

        # Mapping of all the code entities that reference a certain id.
        # Used only if the entity having said id is not in self.entities yet.
        self._refs = {}       # id -> [CodeEntity]

    def register(self, codeobj, declaration=False):
        """Add a top-level code entity.

        This method adds the code entity to internal list.

        :param codeobj: The code entity that will be added to the AST.
        :param declaration: Whether this is the declaration of the code entity.
        """

        previous = self.entities.get(codeobj.id)
        if declaration and not previous is None:
            codeobj._definition = previous
            return
        if not declaration and not previous is None:
            if not isinstance(codeobj, CodeVariable):
                assert not isinstance(previous, CodeVariable)
                if previous.is_definition:
                    raise MultipleDefinitionError("Multiple definitions for "
                                                  + codeobj.name)
                previous._definition = codeobj
            for ref in previous.references:
                ref.reference = codeobj
            codeobj.references.extend(previous.references)
            previous.references = []
        self.entities[codeobj.id] = codeobj

        # If the code entity has references before it is added to the AST,
        # these are found in self._refs. Therefore, they are moved to the code
        # object here.
        if codeobj.id in self._refs:
            references = self._refs[codeobj.id]
            codeobj.references.extend(references)
            for ref in references:
                ref.reference = codeobj

            del self._refs[codeobj.id]

    def reference(self, refd_id, ref):
        """Add a reference to a code entity.

        This method adds a referencing code entity to another referenced
        entity. The latter is identified by its id.

        :param refd_id: The id of the referenced code entity
        :param ref: The referencing code entity.
        """

        codeobj = self.entities.get(refd_id)

        # Referenced is in parsed entity, adding referencing entity to its
        # `references` list
        if codeobj is not None:
            codeobj.references.append(ref)
            referenced = codeobj

        # Referenced id not parsed yet, storing reference in self._ref
        else:
            if refd_id not in self._refs:
                self._refs[refd_id] = []

            self._refs[refd_id].append(ref)
            referenced = refd_id

        ref.reference = referenced


class CodeAstParser(object):
    class LoggerStream(object):
        def __init__(self, logger, stream, log_level=None):
            self.logger = logger
            self.stream = stream
            self.log_level = (log_level
                              or self.logger.getEffectiveLevel()
                              or logging.INFO)

        def write(self, s):
            self.stream.write(s)
            self.logger.log(self.log_level, s)

    @classmethod
    def with_logger(cls, parse_fn):
        def wrapper(*args, **kwargs):
            self = args[0]

            if not self.has_logger:
                return parse_fn(*args, **kwargs)

            sys.stdout = self.stdout_logger
            sys.stderr = self.stderr_logger

            ret = parse_fn(*args, **kwargs)

            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

            return ret

        return wrapper

    def __init__(self, workspace='', logger=None):
        self.workspace      = workspace
        self.global_scope   = CodeGlobalScope()
        self.data           = AnalysisData()

        if logger is not None:
            logger = logging.getLogger(logger)
            self.stdout_logger = self.LoggerStream(logger, sys.__stdout__)
            self.stderr_logger = self.LoggerStream(logger, sys.__stderr__,
                                                   logging.ERROR)
        else:
            self.stdout_logger = None
            self.stderr_logger = None

    @property
    def has_logger(self):
        return (self.stdout_logger is not None
                and self.stderr_logger is not None)

    def parse(self, file_path):
        return self.global_scope
