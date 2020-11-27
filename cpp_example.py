#!/usr/bin/env python

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

from __future__ import print_function
from builtins import range

import sys
from bonsai.analysis import *
from bonsai.cpp.clang_parser import CppAstParser

# ----- Setup ------------------------------------------------------------------
if len(sys.argv) < 2:
    print("Please provide a file to be analysed.")
    sys.exit(1)
v = "3.8"
argi = 1
if sys.argv[1] == "-v":
    if len(sys.argv) < 4:
        print("Please provide a file to be analysed.")
        sys.exit(1)
    v = sys.argv[2]
    argi = 3
CppAstParser.set_library_path(lib_path="/usr/lib/llvm-{v}/lib".format(v=v))
CppAstParser.set_standard_includes(
    "/usr/lib/llvm-{v}/lib/clang/{v}.0/include".format(v=v))
parser = CppAstParser(workspace = "examples/cpp")
for i in range(argi, len(sys.argv)):
    if parser.parse(sys.argv[i]) is None:
        print("No compile commands for file", sys.argv[i])
        sys.exit(1)
# ----- Printing Program -------------------------------------------------------
print(parser.global_scope.pretty_str())
print("\n----------------------------------\n")
# ----- Performing Queries -----------------------------------------------------
print("# QUERY FOR VARIABLE 'a'")
for cppobj in (CodeQuery(parser.global_scope).all_references
               .where_name("a").get()):
    print("[{}:{}]".format(cppobj.line, cppobj.column), cppobj.pretty_str())
    print("[type]", cppobj.result)
    print("[canon. type]", cppobj.canonical_type)
    print("[reference]", cppobj.reference or "unknown")
    value = resolve_reference(cppobj)
    if not value is None and value != cppobj:
        print("[value]", value)
    if is_under_control_flow(cppobj, recursive = True):
        print("[conditional evaluation]")
    else:
        print("[always evaluated]")
    print("")
