# PyMa

> **This is work in progress!**  The documentation is not complete, yet, and there is no guarantee that all features
> are available at the moment.


_PyMa_ supports **Pattern Matching** in _Python_.  It is mostly based on pattern matching from 
[_Scala_](https://www.scala-lang.org/).
  
  
## Example

_PyMa_ was initially developed for analysis of Python code via its _Abstract Syntax Tree_ (AST).  The example below
shows how _PyMa_'s pattern matching can be used to implement a very simple code optimiser.  However, there is nothing
special about the `ast`-module from _PyMa_'s point of view, and you can equally use it in combination with anything
else.

```python
from ast import Add, BinOp, Num
import ast

def simplify(node):
    match node:
        case BinOp(Num(x), Add(), Num(y)):
            return Num(x + y)
        case BinOp(Num(n=x), Sub(), Num(n=y)):
            return Num(x - y)
        case ast.UnaryOp(ast.USub(), x @ Num()):
            return Num(-x.n)
        case _:
            return node
```


## Usage

#### Compile/Execute Code Directly

If you simply want to take _PyMa_ on a test drive, use `pyma_exec` as shown below.

```python
from pyma import pyma_exec

my_code = """
match sum([2, 3, 5, 7]):
    case 17:
        print("Everything's OK")
    case x:
        print("The result", x, "is wrong")
"""

pyma_exec(my_code)
```


#### Import Code From Python Modules

Yet, it is probably more convenient to install the auto import hook, so that all modules in your package/project are
compiled using the _PyMa_-compiler (if they contain a `case` statement, that is).
```python
from pyma import enable_auto_import
enable_auto_import()

import my_module
my_module.test_me()
```
The contents of `my_module.py` is then something like:
```python
def test_me():
    match sum([2, 3, 5, 7]):
        case 17:
            print("Everything's OK")
        case 11 | 13 | 17 | 19:
            print("At least, it's still a prime number")
        case i @ int():
            print("The result", i, "is wrong")
        case x:
            print("Not even an integer?", x)
```


## FAQ

#### Can I Use _PyMa_ in My Project?

Yes, _PyMa_ is released under the [Apache 2.0 license](LICENSE), which should allow you to freely use _PyMa_ in your
own projects.  Since the project is currently under heavy development, the pattern matching might fail in unexpected
ways, though.

In order to provide this new syntax for pattern matching, _PyMa_ needs to translate your code before Python's own
parser/compiler can touch it.  But, the translation process is design to only modify the bare minimum of your original
Python code.  No commends are removed, no lines inserted or deleted, and no variables or functions renamed.  But since
`case` and `match` have become keywords, there is a possible incompatibility with your existing code.

In addition to `case` and `match`, _PyMa_ introduces two more names: `__match__`, and `__matchvalue__`, respectively.
It is very unlikely, though, that your program uses either of these names.


#### Why Not Just Use Regular Expressions?

Regular expressions are great if you want to match a string, say.  The pattern matching we provide here, however, 
works on general Python objects, and not on strings.  It is more akin to something like `isinstance`, or `hasattr`
tests in Python.


#### How Do I Check If a Value Has a Certain Type?

Due to Python's syntax, something like `s: str` will not work in order to specify that `s` should be of type `str`.
What you would usually do in Python is something like `isinstance(value, str)`, which translates directly to:
```python
case str():
    print("We have a string!")
``` 
Make sure you put the parentheses after the `str`, as these parentheses tell _PyMa_ that `str` is supposed to be a 
class against which to test, and not a new name for the value.


#### How Do I Check If a Value Has a Certain Attribute?

If you do not care about the class, or type, of an object, but only about its attributes, use the wildcard `_` as the
class name.  The algorithm will then omit the `isinstance` check, and just test if the object's attributes fulfill the
given conditions - which in this case is simply that there is an attribute `egg`, which can be anything.
```python
case _(egg=_):
    print("We have something with an attribute 'egg'.")
```
The example above will be translated to a simple test of the form `hasattr(value, 'egg')`.


#### Can I Nest The Match/Case Structures?

Basically, yes, you can.  The only real limitation here is that you cannot put a `match` directly inside another
`match`, whereas it is no problem to put a `match` inside a case.  That is to say that the following will fail:
```python
match x:
    match y:
        case z:
```
The reason for this is that `match` buts the value of the expression `x` into a local variable (and has some further
book-keeping).  The second `match` messes this book-keeping up, and replaces `x` by `y`, so that subsequent tests fail.
On the other hand, there is hardly any reason why a `match` inside another `match` should make sense, anyway.

At the moment, nesting is not yet fully implemented, though.  As long you put the match/case structures in separate
functions, there is never a problem.


#### Is This Pattern Matching Library Efficient?

The primary objective of this library is correctness, not efficiency.  Once everything runs, there is still time to
worry about improving the performance of the library.  However, there are some strong limitations to how efficient
pattern matching can be done in Python.

Since the matching algorithm must analyse various objects, and classes, each time a matching is performed, there are
certainly limitations to the performance a pattern matching algorithm can deliver in Python.  If you have something
like in the code snippet below, the algorithm must test, if `my_value` is an instance of `Foo`, if it has (at least)
the attributes `eggs` and `ham`, and if the value of the attribute `eggs` is `123`.
```python
match my_value:
    case Foo(eggs=123, ham=x):
        print("A Foo with 123 eggs has ham", x)
```
In statically compiled languages it is possible to test only once (during compilation) if class `Foo` has attributes
`eggs` and `ham`.  In Python, however, even the class `Foo` refers to might change, so that we need to test everything
upon each matching attempt.

Another limitations is due to the fact _PyMa_ tries to minimize the amount your code needs to be changed.  This means
that each `case` statement is treated in isolation from all others, and it is therefore not possible to factor out
common parts.  Again, there is certainly room for further improvement, but it is not a priority of _PyMa_.


#### Will It Break My Code If I Use `case` and `match` as Variable Names?

There is, of course, always a danger that _PyMa_'s compiler will mis-identify one of your variables as a `match`,
or `case` statement.  However, in order to be recognised as a statement, either keyword (`case`, `match`) must be the
first word on a line, and it cannot be followed by a colon, or an operator (such as an assignment).  So, if you have
a function called `case`, the function call `case(...)` might be interpreted as a `case` statement, but an assignment
like `case = ...`, say, will not.


#### Why is `match` Not an Expression as in Scala?

While _Scala_'s syntax and semantics are based on expressions, _Python_'s is not.  Compound statements like `while`,
`if`, `for` etc. are, as a matter of fact, never expressions in Python, but clearly statements without proper value.
Since both `match` and `case` statements, as implemented here, are obviously compound statements, it would feel very
wrong for Python to try, and make them expressions.


## Contributors

- [Tobias Kohn](https://tobiaskohn.ch)
