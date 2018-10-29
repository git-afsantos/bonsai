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

import sys
from bonsai.analysis import *
from bonsai.cpp.clang_parser import CppAstParser

# ----- Setup ------------------------------------------------------------------
files = ["examples/cpp/multi_def/file1.cpp", "examples/cpp/multi_def/file2.cpp"]

CppAstParser.set_library_path()
parser = CppAstParser()
for filename in files:
    if parser.parse(filename) is None:
        print "No compile commands for file", filename
        sys.exit(1)
# ----- Printing Program -------------------------------------------------------
print parser.global_scope.pretty_str()
print "\n----------------------------------\n"
# ----- Performing Queries -----------------------------------------------------
print "# QUERY FOR CALL 'add_ints'"
for cppobj in (CodeQuery(parser.global_scope).all_calls
               .where_name("add_ints").get()):
    print "[{}:{}]".format(cppobj.line, cppobj.column), cppobj.pretty_str()
    print "[type]", cppobj.result
    print "[reference]", cppobj.reference or "unknown"
    print ""
