# PyMa

> **This is work in progress!**  The documentation is not complete, yet, and there is no guarantee that all features
> are currently available.


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

> TODO


## FAQ

#### Can I Use _PyMa_ In My Project?

Yes, _PyMa_ is released under the [Apache 2.0 license](LICENSE), which should allow you to freely use _PyMa_ in your
own projects.  Since the project is currently under heavy development, the pattern matching might fail in unexpected
ways.


#### Why Not Just Use Regular Expressions?

Regular expressions are great if you want to match a string, say.  The pattern matching we provide here, however, 
works on general Python objects, and not on strings.  It is more akin to something like `isinstance`, or `hasattr`
tests in Python.


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


#### Will It Break My Code If I Use `case` And `match` As Variable Names?

There is, of course, always a danger that _PyMa_'s compiler will mis-identify one of your variables as a `match`,
or `case` statement.  However, in order to be recognised as a statement, either keyword (`case`, `match`) must be the
first word on a line, and it cannot be followed by a colon, or an operator (such as an assignment).  So, if you have
a function called `case`, the function call `case(...)` might be interpreted as a `case` statement, but an assignment
like `case = ...`, say, will not.


#### Why Is `match` Not An Expression As In Scala?

While _Scala_'s syntax and semantics are based on expressions, _Python_'s is not.  Compound statements like `while`,
`if`, `for` etc. are, as a matter of fact, never expressions in Python, but clearly statements without proper value.
Since both `match` and `case` statements, as implemented here, are obviously compound statements, it would feel very
wrong for Python to try, and make them expressions.


## Contributors

- [Tobias Kohn](https://tobiaskohn.ch)
