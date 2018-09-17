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

**NB:** Please be aware that many symbols are either not supported, or have a different meaning in pattern matching.
In particular, do not expect any kind of expression to be evaluated!  For instance, `case 3+4:` is _not_ equivalent to
`case 7:`, because the `3+4` is never evaluated, but indicates that an object should be decomposable into `3` and `4`.


## Installation

_pyPMatch_ can be installed using `pip`:
```
pip install pyPMatch
```
You might also want to look at the [example](../examples); modify, and run [run_example.py](../examples/run_example.py).

## Syntax For Writing Patterns

### Wildcards and Names

If you do not care about the actual value of an element in the matched object, you can use the wildcard `_`.  While
this is a perfectly legal name in Python, it has a special meaning in pattern matching: _do not care_.

Similarly, you can use the ellipsis `...` to express that it is not important to you, how many, or what kind of
elements are in there.  In fact, the ellipsis means the same as `*_`: it matches any subsequence, and then throws
it away.  Of course, you can also use `*_` itself to mean the same thing.

Variable names like `a`, `b`, `x`, etc. in the example above are also considered to be wildcards.  In contrast to `_`,
the extracted value is assigned to the respective variable.  If you do care about sub-sequences, you are absolutely
free to use `*x`, etc.  In other words: the syntax from unpacking sequences still works as before.

Note that each name can only occur once in any given pattern.  Something like `case (x, x):` is illegal, and will
raise a syntax error.  Use _guards_ (see below) to check if two elements are equal.


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
match s:
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

Internally, type checks are done through `isinstance(obj, int)`, etc.  Something like `case int()|float():` directly
translates to `isinstance(obj, (int, float)):`.

Type checking as explained here works not only with builtin types, but with any type or class.  See the section on
**Deconstructing Types** further below for extended possibilities.


### Name Binding

There are situations, where you want to check if an element has a certain type, or value, and bind it to a variable at
the same time.  For example, you might want to have a case covering all sequences starting with a lowercase letter,
but you also want to extract this first letter.
```python
match obj:
    case [('a' | ... | 'z'), *_]:
        print("Starts with a lowercase letter, but which one?")
    case [x, *_]:
        print("We get the first element, but is it a lowercase letter?")
```

Luckily for us, there is a _name binding operator_ `@`, which allows us to check for specific values, or types, _and_
assign it to a variable.
```python
match obj:
    case [x @ ('a' | ... | 'z'), *_]:
        print("Starts with a lowercase letter:", x)
```

This works just as well for types, of course:
```python
match obj:
    case x @ int():
        print("Integer", x)
    case s @ str():
        print("String", s)
```

There is one limitation to name binding, though.  Name binding cannot occur inside alternatives.  The following is
invalid, and will raise a syntax error (even if you use the same variable name in both cases):
```python
match obj:
    case (i @ int() | f @ float()):
        # ERROR: DOES NOT WORK!
```

Recall, that all names must be unique in any given pattern.  Something like `case (x, x):` is illegal, and will not
work.  Use _guards_ to test if two elements are equal.



## Guards

There are situations where patterns alone do not suffice to capture the full intent.  Sometimes, you need to check for
additional conditions to be satisfied.  For these situations, you use a _guard_.

After any pattern, you can specify an additional _guard_ with the keyword `if`.  The condition behind the `if` can,
in fact, be any condition, making use of both variables from inside the pattern, as well as other variables in the
surrounding scope.

If you want to check if the first, and last element of a sequence are equal, you might write:
```python
match obj:
    case [first, ..., last] if first == last:
        print("First and last are the same")
    case [x, y, z, *_] if x <= y <= z:
        print("Seems to be in ascending order")
    case _:
        pass
```

This also allows you test if the object contains a value from a variable:
```python
match obj:
    case [P, ...] if P == math.pi:
        print("We start off with PI")
    case [1, 2, *rest] if 5 > len(rest):
        print("Nice start, but not enough elements.")
    case _:
        pass
```

If you need to have more than one condition to be checked, use `and` or `or`, as you normally would in an 
`if`-statement.  It is _not_ possible to write something like `case A if B if C:`.


## Deconstructing Types and Classes

### Checking Types and Fields

If you have a class `Chicken` and want to test if an object is an instance of `Chicken`, you can either use Python's
`isinstance()` function, or you use pattern matching with `case Chicken():`.  The true power of pattern matching,
however, comes to play, when we start to nest patterns.

Let us assume that instances of `Chicken` have a field `age`, and a field `sex`.  The first one is an integer giving 
a chicken's age in months, say, while `sex` is either `'m'`, or `'f'`.  If we now want to find all female chicken older
than five months, we do the following:
```python
match bird:
    case Chicken(sex='f', age=x) if x > 5:
        print("got one")
    case Chicken(age=x) if x <= 5:
        print("too young")
    case _:
        pass
```

Based on the basic principle, we assume that we can create a chicken through a constructor like 
`my_chicken = Chicken(sex='f', age=0)`.  There might be more fields, or attributes, of course, but for pattern 
matching, we just ignore them.  Keep in mind that in Python, we can usually add a new field to any chicken just
like so: `my_chicken.eye_color = 'blue'`.  It would therefore not make sense for pattern matching in Python to
require all fields to be named in the pattern.

Going a step further, we might not actually have a chicken, but rather an egg, which contains a young chick.  And we
would like to find those white eggs that will produce a female chicken one day.  This time, we also factor in the 
possibility that someone used `'F'` instead of `'f'` for the chicken's sex:
```python
match thing:
    case Egg(contents=Chicken(sex='f'|'F'), color='white'):
        print("got one")
    case _:
        pass
```
Seeing how easy it is to inspect the sex of a chick in an egg using Python, we understand why computer science becomes
so important in the sciences.  But, apart from that, what is the point here?

Pattern matching unfolds its full power when it is combined with recursion/nesting.  You can not only specify the type 
of an object, but, at the same time, also match any, or all of its fields to specific patterns on their own.  You can
nest patterns as deep as ever you need them to be, and extract information, or make sure that an object satisfies a
complex structure.  

Just think of how easy it is to get a white egg containing a female chick out of a box with several eggs:
```python
match thing:
    case Box(contents=[..., 
                       x @ Egg(contents=Chicken(sex='f'|'F'), 
                               color='white'), 
                       ...]):
        print("got one:", x)
    case _:
        pass
```

Finally, if you do not care about the specific type of an object, but only about its fields, just use a wildcard as
its type/class.  If we are happy with any female animal, we write:
```python
match animal:
    case _(sex='f'|'F'):
        print("got one")
    case _:
        pass
```
Again, you can put this into a list, or any other pattern, if you so wish.

Internally, the code for checking types, and fields is translated directly to `isinstance()` and `getattr()` calls. 
Findings a female chicken with `case Chicken(sex='f', age=x) if x > 5:` ends up with code like:
```python
NO_VALUE = object()

def _check_case_1(obj):   
    """Returns tuple ('cond fulfilled?', 'value of x')"""
    if isinstance(obj, Chicken):
        _field_1 = getattr(obj, 'sex', NO_VALUE)
        _field_2 = getattr(obj, 'age', NO_VALUE)
        if _field_1 == 'f':
            x = _field_2
            if x > 5:
                return (True, x)
    return (False, None)
```


### De-Constructor

Many constructors have positional arguments, which are then mapped to fields.  The order of the arguments, or fields,
might even be quite obvious.  Take, for instance, the `BinOp`-class from Python's `ast`-module.  It represents a binary
operation (such as an addition, multiplication, etc.), and has the three fields `left`, `op`, and `right`.  The 
addition `x + 1` could be created like so:
```python
from ast import BinOp, Name, Add, Num
addition = BinOp(Name('x'), Add(), Num(1))
```
There is little ambiguity there, even though you could equally write:
```python
addition = BinOp(left=Name(id='x'), op=Add(), right=Num(n=1))
```

If, in pattern matching, we want to to check if we have an addition with a variable on the left side, and the number 
`1` on the right side, we can certainly do it like this:
```python
match ast_node:
    case BinOp(left=Name(id=x), op=Add(), right=Num(n=1)):
        print("The increased variable is", x)
    case _:
        pass
```
However, it is also possible to write it without explicitly naming all the fields:
```python
match ast_node:
    case BinOp(Name(id=x), Add(), Num(1)):
        print("The increased variable is", x)
    case _:
        pass
```
In order for this to work, _pyPMatch_ needs a way to figure out the values it needs to extract from the object `BinOp`.
There are several possibilities, which are supported by _pyPMatch_, so that most cases should be covered out of the 
box.  This kind of using deconstructors is discussed in detail in [destructuring](DESTRUCTURING.md).

Because _pyPMatch_ does not have the name of fields, anymore, the generated code is quite different to what you get 
with "named arguments" (the magic behind `extract_fields` is explained in [destructuring](DESTRUCTURING.md); here it
should suffice to say that it returns a tuple):
```python
def _check_case_1(obj):
    """Returns tuple ('cond fulfilled?', 'value of x')"""
    if isinstance(obj, Chicken):
        _fields = extract_fields(cls=Chicken, obj=obj)
        if len(_fields) >= 3 and isinstance(_fields[0], Name) and \
           isinstance(_fields[1], Add) and isinstance(_fields[2], Num):
            x = getattr(_fields[0], 'id', NO_VALUE)
            if x is NO_VALUE:
                return (False, None)
            _fields_2 = extract_fields(cls=Num, obj=_fields[2])
            if len(_fields_2) >= 1 and _fields_2[0] == 1:
                return (True, x)
    return (False, None)
```

There are two limitations to keep in mind here, though.  First, for the time being, you cannot mix the variant with 
position arguments using deconstructors, and the variant where you explicitly name the fields: you cannot have both
for the same class pattern, that is.  As the example above shows, there is no problem in using one variant for `BinOp`,
and another one for `Name`.  Second, you need to specify a valid class/type.  When using positional arguments, you 
obviously cannot use the wildcard `_` as class name, because the pattern matcher needs a specific class.


## Concluding Remarks

There is much more to say (and discuss) about pattern matching, and its implementation.  This introduction should, 
however, get you started.

At various points, this introduction shows the code generated for some of the patterns.  Actually, _pyPMatch_ usually
generates more complex code, capable of handling arbitrarily nested patterns.  The examples of generated code are thus
not meant to be taken literally, but as basic guide to explain (or at least give a hint of) what is happening under 
the hood.

