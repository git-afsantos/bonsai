Bonsai
======

| Bonsai is an attempt to provide a miniature and refined representation
  for the
| often cumbersome **syntax trees** and **program models**.
| This idea, of providing a *smaller tree* that is more or less the same
  thing,
| is where the name comes from.

| This work started as part of an analysis tool that I am developing for
  my own
| research. I am interested in analysing `ROS`_
| robotics applications, which are often written in C++.
| Since free C++ analysis tools are *rather scarce*, I tried
| to come up with my own, using the Python bindings of the ``clang``
  compiler.
| At the moment of this writing, I am aware that these bindings are
  incomplete
| in terms of AST information they provide.

| As this analysis tool developed, I realized that the C++ analysis
  features
| are independent of ROS or any other framework, and that this kind of
  tool
| might be useful for someone else, either as is, or as a starting point
  for
| something else.

Features
--------

| Bonsai provides an interface to represent, analyse or manipulate
  programs.
| The model it uses is abstract enough to serve as a basis for specific
  language
| implementations, although it focuses more on
  imperative/object-oriented
| languages for now.

What to expect from **bonsai**:

-  classes for the different **entities of a program** (e.g. variables,
   functions, etc.);
-  extended classes for **specific programming languages** (only C++ for
   now);
-  **parser implementations**, able to take a file and produce a model
   (e.g. ``clang`` for C++);
-  extensible interface to **manipulate and query** the resulting model
   (e.g. find calls for a function);
-  a console script to use as a standalone application.

Installation
------------

| Here are some instructions to help you get bonsai.
| Bonsai has been tested with *Linux Ubuntu* and *Python 2.7*,
| but the platform should not make much of a difference.
| Dependencies are minimal, and depend on what you want to analyse.

| Since at the moment there is only a single implementation for C++
| using clang 3.8, you will need to install ``libclang`` and the
| `clang.cindex bindings`_
| (``pip install clang``) to parse C++ files. Skip this if you want to
  use
| the library in any other way.

Method 1: Running Without Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

| Open a terminal, and move to a directory where you want to clone this
| repository.

.. code:: bash

    git clone https://github.com/git-afsantos/bonsai.git

| There is an executable script in the root of this repository to help
  you get started.
| It allows you to run bonsai without installing it. Make sure that your
  terminal is at
| the root of the repository.

.. code:: bash

    cd bonsai
    python bonsai-runner.py <args>

You can also run it with the executable package syntax.

.. code:: bash

    python -m bonsai <args>

Method 2: Installing Bonsai on Your Machine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

| Bonsai is now available on `PyPi`_.
| You can install it from source or from a wheel.

.. code:: bash

    [sudo] pip install bonsai-code

| The above command will install bonsai for you. Alternatively, download
  and extract its
| source, move to the project’s root directory, and then execute the
  following.

.. code:: bash

    python setup.py install

| After installation, you should be able to run the command ``bonsai``
  in your terminal
| from anywhere.

Examples
--------

| The ``cpp_example.py`` script at the root of this repository is a
  small example on
| how to parse a C++ file and then find all references to a variable
  ``a`` in that file.
| In it, you can see parser creation

.. code:: python

    parser = CppAstParser(workspace = "examples/cpp")

| access to the global (top level, or root) scope of the program, and
  obtaining
| a pretty string representation of everything that goes in it

.. code:: python

    parser.global_scope.pretty_str()

| getting a list of all references to variable ``a``, starting the
  search from
| the top of the program (global scope)

.. code:: python

    CodeQuery(parser.global_scope).all_references.where_name("a").get()

| and accessing diverse properties from the returned ``CodeReference``
  objects,
| such as file line and column (``cppobj.line``, ``cppobj.column``), the
  type of the
| object (``cppobj.result``), what is it a reference of
  (``cppobj.reference``,
| in this case a ``CodeVariable``) and an attempt to interpret the
  program and
| resolve the reference to a concrete value
  (``resolve_reference(cppobj)``).

| Do note that **resolving expressions and references is still
  experimental**,
| and more often that not will not be able to produce anything useful.

| This is the pretty string output for a program that defines a class
  ``C``
| and a couple of functions.

::

    class C:
      C():
        [declaration]

      void m(int a):
        [declaration]

      int x_ = None

    C():
      x_ = 0

    void m(int a):
      a = (a + 2) * 3
      this.x_ = a

    int main(int argc, char ** argv):
      C c = new C()
      c.m(42)
      C * c1 = new C()
      C * c2 = new C()
      new C()
      delete(c1)
      delete(c2)
      return 0

| The pretty string representation, as seen, is a sort of
  pseudo-language, inspired
| in the Python syntax, even though the parsed program is originally in
  C++.

| For more details on what you can get from the various program
  entities, check out
| the source for the abstract model and then the language-specific
| implementation of your choice.

.. _ROS: http://www.ros.org/
.. _clang.cindex bindings: https://github.com/llvm-mirror/clang/tree/master/bindings/python
.. _PyPi: https://pypi.python.org/pypi/bonsai-code