# PyMa

> **This is work in progress!**  The documentation is not complete, yet, and there is no guarantee that all features
> are available at the moment.


_PyMa_ provides **Pattern Matching** in _Python_.  It is mostly based on the pattern matching found in 
[_Scala_](https://www.scala-lang.org/).


## Example

_PyMa_ was initially developed for analysis of Python code via its _Abstract Syntax Tree_ (AST).  The example below
shows how _PyMa_'s pattern matching can be used to implement a very simple code optimiser.  However, there is nothing
special about the `ast`-module from _PyMa_'s point of view, and you can equally use it in combination with anything
else.

```python
import ast
from ast import Add, BinOp, Num

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

You will find more examples in the [examples folder](examples).


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
compiled using the _PyMa_-compiler (if they contain a `case` statement, that is).  The auto import is installed
directly through the import of `enable_auto_import`.
```python
from pyma import enable_auto_import

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


## Writing Patterns

Patterns can be expressed using the elements described below.

> As mentioned above: **not everything is implemented and tested**, yet!

- `Foo()` matches all instances of the class `Foo`;
- `Foo(A, B, C)` deconstructs an instance of `Foo`, which must yield three values, which then must match the patterns
  `A`, `B`, and `C`, respectively;
- `Foo(egg=A, ham=B)` matches all instances of `Foo`, where the attributes `egg`, and `ham` match the patterns
  `A` and `B`, respectively;
- `12`, `'abc'`, `True` and other constant match a value if the value is equal to the constant;
- `{'RE'}` matches if the value is a string that conforms to the regular expression given;
- `A | B | C` matches if at least one of the patterns `A`, `B`, `C` matches;
- `[A, B, C, ..., D, E]` matches any sequence where the first three elements match `A`, `B`, and `C` and the last two 
  elements match `D`, and `E`, respectively.  This also includes Python's usual iterator unpacking, such as 
  `[a, b, *c, d]`, which is interpreted as `[a, b, c @ ..., d]`; 
- `x @ A` matches if the pattern `A` matches, and binds the value to the variable `x` if the entire match is 
  successful;
- `_` is a wildcard that matches everything;
- `*_` and `...` are wildcards used in sequences, usually with the exact same meaning;
- `x` is an abbreviation for `x @ _`, matches everything, and binds it to `x`.


There are some special cases, and limitations you should be aware of:

- Any variable `x` can only be bound once inside a single pattern (a `case` statement).  It is legal to reuse
  `x` in different `case` statements, but you cannot have something like `Foo(x, x)`.  If you need to test if both
  values in `Foo` are equal, use `Foo(x, y) if x == y` instead;
- You cannot bind anything inside an alternative.  Hence, `A|(x @ B)|C` is illegal;
- It is not possible to bind anything to the wildcard `_`.  While `_` is a regular name in Python, it has special
  meaning in _PyMa_ patterns.  Something like `_ @ A` is, however, not illegal, but equivalent to `A()`;
- Even though the ellipsis `...` is a 'normal value' in Python, it has a special meaning in _PyMa_ as a wildcard;
- _PyMa_ does not look at the names involved.  If a name is followed by parentheses as in `Foo()`, the name is taken
  to refer to a class/type, against which the value is tested.  Otherwise, the name is a variable that will match any
  value.  This means that the pattern `str` will match everything and override the variable `str` in the process,
  while `str()` will test if the value is a string;
- Instead of writing a regular expression on your own, you can use `{int}`, or `{float}` to check if a string value
  contains an `int`, or a `float`, respectively;
- There are a few exceptions to the last rule.  Since name bindings are illegal in alternatives, anyway, you can write
  `A|B|C` as an abbreviation for `A()|B()|C()`.  Furthermore, `x @ A` is interpreted as `x @ A()`, since it makes no
  sense to bind two distinct variables to the exact same value;
- `3 | ... | 6` is an abbreviation for the sequence `3|4|5|6`.  This syntax can be used with integers, and characters
  (single-character strings).  Thus, you can also write `'a' | ... | 'z'`, for instance.  Note, that here you need to
  write the ellipsis, and cannot use the otherwise equivalent token `*_`.
  
  
#### Roadmap

- Support for lists, tuples, iterators, etc.  Must be (mostly) compatible with Python's current iterable unpacking 
  syntax `a, b, *c = X`
- Full support for regular expressions and string matching
- Further narrow the translation/compiling of `case` statements to where it is clearly meant to be one
- Pattern matching through function decorators
- Raise error if no match is found
- Test suites
- Documentation, tutorials


## The Two Versions of the `case` Statement

There are two version of the `case` statement.  You can either use `case` inside a `match` block, or as a standalone
statement.

Inside a `match` block, which is compared against the patterns is specified by `match`.
```python
def foo(x):
    match x:
        case 'a' | ... | 'z':
            print("Lowercase letter")
        case '0' | ... | '9':
            print("Digit")
        case _:
            print("Something else")
```
The same could also be written without the `match`.  In that case, you need to specify the value to be tested against
the pattern.  This done using the `as` syntax.  There is a difference, though.  The standalone `case` statements will
all be tested, so that we explicitly need to use `return` in order to avoid printing `"Something else"` for everything.
```python
def foo(x):
    case x as 'a' | ... | 'z':
        print("Lowercase letter")
        return
    case x as '0' | ... | '9':
        print("Digit")
        return
    case x as _:
        print("Something else")
```

At the moment, you cannot put standalone `case` inside a `match` block, and, of course, you cannot use a `case` without
specifying the value outside a `match` block.


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
The reason for this is that `match` puts the value of the expression `x` into a local variable (and has some further
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


#### Why Did You Use `@` for Name Bindings Instead of `:=`?

Python 3.8 will introduce assignment expressions (see [PEP 572](https://www.python.org/dev/peps/pep-0572/)).  It would
therefore be natural to use `x := A` instead of `x @ A` for name bindings.

In fact, I am happy to add full support for `:=`.  At the time of writing, however, `:=` is not yet a valid token in
Python.  Using only `:=` would mean that _PyMa_ requires at least Python 3.8, while `@` has already become a valid 
operator in Python 3.5 [PEP 465](https://www.python.org/dev/peps/pep-0465/).


#### Why `1 | ... | 9` Instead Of the Simpler `1 ... 9`?

The entire syntax of patterns in _PyMa_ is based on standard Python syntax.  Even though the patterns are semantically
nonsense, they are syntactically valid.  The sequence `1 ... 9`, however, is not a valid sequence in Python, and would
issue a syntax error.

There are various reasons for wanting patterns to be valid Python syntax.  One of them is that _PyMa_ gets away with
much less parsing work on its own.

Apart from this issue of pragmatics, writing `1 | ... | 9` seems clearer to me, since `1 ... 9` could also mean that
the value has to be the sequence `1, 2, 3, ..., 9` itself.  This is, however, a matter of personal taste, and thus
debatable.


#### Why Are There Two Versions of `case` Statements?

Pattern matching does usually not only come in the form of `match` blocks.  At times, we only want to deconstruct a
single value.  Python already supports this in part through assignments like `a, b, *c = x`.  Using the standalone
version of `case`, you could write this in the form `case x as (a, b, *c):`.  However, the `case` statement can do much
more than Python's assignment operator.

On the other hand, while developing the library, I wondered if it possible to give meaning to `case` even outside a
`match` block, so as to make the entire syntax as orthogonal, and as flexible as possible.
 
As _PyMa_ is kind of a prototype, in the end, the standalone variant of `case` might not survive, and not make it into
subsequent versions.  For the moment, it remains there to fully test its usefulness.


#### Why is `match` Not an Expression as in Scala?

While _Scala_'s syntax and semantics are based on expressions, _Python_'s is not.  Compound statements like `while`,
`if`, `for` etc. are, as a matter of fact, never expressions in Python, but clearly statements without proper value.
Since both `match` and `case` statements, as implemented here, are obviously compound statements, it would feel very
wrong for Python to try, and make them expressions.


## Contributors

- [Tobias Kohn](https://tobiaskohn.ch)
