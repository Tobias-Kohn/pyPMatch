# Introduction

Python already has some builtin "pattern matching" capabilities, which are very handy.  If you have a sequence, or even
any iterable object, you can assign its elements to different variables.  Like so, for instance:
```python
a, b, c = [4, 9, 16]
x, y, *_, z = [1, 3, 5, 7, 9]
```
There are many other instances of where you might encounter unpacking of sequences, or even dictionaries.

Another feature that comes very close to what pattern matching does is the `getattr` function.  At the same time, it
can test if a given object has a specific attribute, and return its value if present.
```python
NO_VALUE = object()

def eat_bacon(obj):
    bacon = getattr(obj, 'bacon', NO_VALUE)
    if bacon is not NO_VALUE:
        print(f"We found {bacon} bacon, and eat it all")
        obj.bacon = 0
    else:
        print("There is no bacon here")
```

However, would it not be cool if could somehow merge the `getattr`, and even the sequence unpacking, with the 
subsequent `if`?  Or have a way to easily check if we can unpack three, or five, elements from an object?

That is where pattern matching comes in - at least the flavour that is offered by _pyPMatch_ (there are various 
different kinds of pattern matching, all with their own benefits).  In short, the `case` statement takes over the
unpacking, or attribute extraction for you.  By doing so, it always checks if the unpacking, or extraction is
valid.  The code of a case-statement is only executed if the unpacking, or extraction has been successful.
```python
def showcase(arg):
    match arg:
        case (a, b, c):       # case A
            print("We have three elements:", a, b, c)
        case (a, _, _, _, _):
            print("We have five elements, starting with:", a)
        case (x, y, ..., last) if x == y:
            print("The first two elements are equal, the last is:", last)
        case (1, 2, 3|4):     # case D  (never applies...)
            print("We have a nice sequence of 1,2,3 or 1,2,4")
        case _:
            print("I don't know what this is supposed to be...")
```
There are few things to be aware of in the context of pattern matching:
- Python checks each case in order, and takes the first that matches the value.  This is basically the same as what you
  get with an `if`-`elif`-chain.  In the example above, this means that the sequence `(1, 2, 3)` is never actually
  "detected", because the first case already covers _all_ sequences with three elements.  If you want the sequences
  `(1, 2, 3)`, and `(1, 2, 4)` to be handled correctly, then case "D" would have to come before case "A".
- The cases in a `match`-statement need to be exhaustive.  This is like saying that each `if`-`elif`-chain must have
  an `else` at the end.  In the example above, the last case has the pattern `_`, which is a wildcard that matches
  anything.  You will often find this being the last case in a match, unless you are absolutely sure you have already
  covered everything (or you are willing to risk a runtime exception).
- While you can test if an element has a specific value by using a constant (as in case "D"), it does not work with
  variables.  The pattern `case pi:`, say, will never check if it the tested value is `3.14159`, but simply assign
  whatever it gets to the name `pi`.  Use `case x if x == pi:` to check if you get pi.


### Basic Principle

The basic idea of pattern matching is this: after the `case` keyword, you specify a possible way of how the object in
question could have been constructed.  It this construction recipe contains any wildcards, or placeholders, Python
will try, and figure out, what they should be.

Hence, `case [1, 2, x]:`, say, means that the object in question could have been constructed as a list, where we do 
not know the value of the last element.  `case ast.UnaryOp(ast.USub(), item):` means that we assume the object could
have been created through `obj = ast.UnaryOp(ast.USub(), <item>)`, but we do not know (yet), what has been used as
`<item>`.

There are a few exceptions for reasons of convenience.  For example, `case 3|4|5:` matches one of the numbers 
`3`, `4`, or `5`, even though `3|4|5` itself would just evaluate to `7`.



## Syntax For Writing Patterns

### Wildcards

If you do not care about the actual value of an element in the matched object, you can use the wildcard `_`.  While
this is a perfectly legal name in Python, it has a special meaning in pattern matching: _do not care_.

Similarly, you can use the ellipsis `...` to express that it is not important to you, how many, or what kind of
elements are in there.  In fact, the ellipsis means the same as `*_`: it matches any subsequence, and then throws
it away.  Of course, you can also use `*_` itself to mean the same thing.

Variable names like `a`, `b`, `x`, etc. in the example above are also considered to be wildcards.  In contrast to `_`,
the extracted value is assigned to the respective variable.  If you do care about sub-sequences, you are absolutely
free to use `*x`, etc.  In other words: the syntax from unpacking sequences still works as before.


### Constants And Alternatives

One of the simplest patterns are constants, such as numbers, or strings.  Hence `case 3:` will just check if the 
provided object has the value `3`, and, likewise, `case 'abc':` will check if the object is the string `'abc'`.
Internally, these are translated to comparisons of the form `if obj == 3:`, or `if obj == 'abc'`, and so on.  
Naturally, the same rules apply, and `case 3:` will not only match the integer `3`, but also the floating point
value `3.0`.

Ever so often, you might have more than one value, which is acceptable, or even a range of concrete values.  If
any two-digit square number is acceptable, the according pattern is: `case 16|25|36|49|64|81:`.  This simply
translates internally to `if obj in (16, 25, 36, 49, 64, 81):`.  You can, of course, freely mix different types,
and have something like `case 'abc'|123:` if you want to.

A use case that might appear rather frequently is checking against a range of integers, or characters (strings of
length one).  There is a special syntax for such patterns, which, however, works only with integer values, and
characters.  If you put the ellipsis between a lower, and an upper bound, _pyPMatch_ will fill out the missing
values for you.
```python
def letter_type(ch):
    match ch:
        case '\n':
            return 'newline'
        case '0' | ... | '9':
            return 'digit'
        case 'A' | ... | 'Z':
            return 'alpha'
        case 'a' | ... | 'z':
            return 'alpha'
        case '(' | '[' | '{':
            return 'left bracket'
        case ')' | ']' | '}':
            return 'right bracket'
        case _:
            return 'symbol'
```
Note that, internally, the respective range really is completed.  `0 | ... | 4` is equivalent to `0 | 1 | 2 | 3 | 4`,
and not to `0 <= obj <= 4`.  The reason is that a value like `2.5` would fulfill the latter condition, but is 
probably not intended to match the pattern.


What makes pattern matching so powerful is that constants, and alternatives can be used anywhere inside a pattern.
To check if a string starts with the markers for a hexadecimal number, you do the following (the inner parentheses
are not strictly necessary here, but help with readability):
```python
match list(s):
    case ['0', ('x' | 'X'), ('0' | ... | '9' | 
                             'A' | ... | 'F' | 'a' | ... | 'f'), *_]:
        print("This looks like a hexadecimal number")
    case _:
        pass
```


### Sequence Unpacking

Basically, sequence unpacking works exactly as you would expect it in Python.  The pattern `x, y, *z` matches any
sequence with at least two elements, assigns the first two elements to `x`, and `y`, respectively, and the rest to
`z` (meaning that `z` is itself a sequence).

In contrast to Python's unpacking, _pyPMatch_ can do more, though.  Instead of variables acting as targets, you can 
use constants, making sure that a specific element has a certain value.  And, moreover, you can have more than one
sub-sequence.  Here is, for instance, a pattern that extract the first element of any sequence that contains the
number 42 later on: `case (x, *_, 42, *_):`.  If you want to know what comes before `42`, use `case (*b4, 42, *_):`.

In order for several sub-sequences in a pattern to work, the pattern matcher needs to have a firm rule to detect
an element in the middle.  For instance, `case (*x, y, *z):` will _not_ work, because the pattern matcher cannot
figure out, which element it should assign to `y`.

In Python, unpacking works with any iterable object.  When used in pattern matching, however, the object must be 
sequence, where each element is accessible through the syntax `obj[0]`, `obj[1]`, etc.  The difference is that Python
does its unpacking exactly once, and raises an exception, if it fails.  During pattern matching, however, we might need
to try, and unpack an object several times with slightly different approaches.  The very moment we have more than one
`case` statement inside the match (which is almost invariable always the case), it does not work iterating over the
object only once, anymore.

The internally generated code for unpacking can be somewhat complicated, due to cases like `case (*_, x, 42, 0, *_)`,
for instance.  For simple patterns, however, the code simply checks the elements one by one, 
i. e. `case (x, 21, 42, _*):` basically translates to:
```python
if len(obj) >= 3 and obj[1] == 21 and obj[2] == 42:
    x = obj[0]
```
If you leave out the `*_` at the end, the `len(obj) >= 3` becomes `len(obj) == 3`, of course.


### Type Checking

Pattern Matching is often used to check the type of an object.  While there is much more to say about this later, we
briefly cover the case of basic types like `int`, or `str`.

A pattern like `case int:` will not work to check if the object is type integer.  Instead, if will assign whatever 
object it has got to the name `int`.  _pyPMatch_ does not look at the names you provide it with, and therefore will
not see that `int` is a builtin type.

In order to check if an object is an integer, you have to put parentheses, just like for a call: `case int():` will,
indeed, check if the given object is of type integer.  Recall the basic principle from above: patterns try to emulate
how the object could have been constructed.  And if you want something to be an integer, you use `int()` as a function,
i. e. you write `int(4.25)` to convert the floating point value to an int.  Hence, `case int():` tells the pattern
matcher to check if the object could have been the result of a call to the builtin constructor `int`.

Because constructors like `int()` are really versatile, you cannot expect the pattern matcher to suggest meaningful
arguments for `int()`.  In fact, there are almost an infinite number of arguments `A` that would lead to `int(A)`
being `4`, say.

```python
match obj:
    case int():
        print("Integer")
    case float():
        print("Float")
    case str():
        print("String")
    case bool:              # Missing parentheses; performs `bool = obj`, and
        print("Anything")   # therefore matches anything...
```


### Name Binding

...
