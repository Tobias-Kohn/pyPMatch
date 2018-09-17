# Destructuring

The [introduction](INTRODUCTION.md) already covers how you can check the type of an object, or match any of its fields
to patterns.  However, there are situations when the information you wish to access, and match, is not readily 
available in a universally accessible field.  Or the actual name of the fields might just not be that relevant, 
compared to the order of the data.  Or, finally, you really just want a more convenient way to express your patterns.

Anyway, in such a case where you do not want to, or cannot access an objects data through its attributes, you use a
_de-constructor_ to access the data.  Whereas a _constructor_ takes several bits of data, and mangles them together
to form a new object, the _de-constructor_ takes an object, and tries to extract those original bits of data that went
into the constructor in the first place.

_NB: The "de-constructor" is not the same thing as a "destructor".  Its purpose is not to free or destroy an object
instance, but to extract the information encoded by the "constructor"._

Let us resume the example from the introduction featuring the `BinOp`-class from the `ast`-module.  The constructor
takes three pieces of data: the node on the left of the binary operation, the operator, and the node on the right:
```python
new_node = BinOp(left, op, right)
```
The deconstructor's job is then to extract these three pieces of data:
```python
left, op, right = deconstruct(new_node)
```

Pattern matching tries to figure out how an object might have been constructed, according to the pattern templates you
provide.  That is, if you write
```python
match node:
    case BinOp(left, Add(), right):
        print("Left:", left, "Right:", right)
```
then the pattern matcher tests the hypothesis that `node` could be created through the constructor `BinOp` with `Add`
as the operator, but unknown objects for `left`, and `right`.  How does the pattern matcher actually do this?  It tries
to deconstruct the object `node` as a `BinOp`, and then matches patterns on the individual items.  The code for the
actual pattern matching looks (more or less) like this:
```python
    def case1(_node):
        nonlocal left, right
        items = deconstruct(node)
        if items is not None:
            left, op, right = items
            if isinstance(op, Add):
                return True
        return False
    if case1(node):
        print("Left:", left, "Right:", right)
```
Clearly, the function that is called `deconstruct` here is at the core of the entire pattern matching process in such
an instance.


## Extracting Data from Objects

The difficulty of the `deconstruct` method is to know, which data it needs to extract from an object, and in which
order.  Luckily, Python's ability to inspect objects, and their methods, is of great help in this regard.  However,
there are few special cases worth considering.


### Data Classes

Python 3.7 has officially introduced _Data Classes_ (see [PEP 557](https://www.python.org/dev/peps/pep-0557/),
or the specs on [Data Classes](https://docs.python.org/3/library/dataclasses.html)).
A data class works similar to a "struct" or "record" in other languages, in that you primarily specify the data
fields along with their types, and do not necessarily define methods (even though you can, of course).  A trivial 
example might look like this:
```python
@dataclass
class Person:
    name: str
    first_name: str
    age: int
     
john = Person('Doe', 'John', 34)
```
The constructor of a data class is created automatically.  For this to work, all relevant fields need to be annotated,
and, of course, their order matters.  In short: this is an ideal case for _pyPMatch_ to extract the data.  Just as
the constructor for data classes is created automatically, _pyPMatch_ can automatically create a deconstructor.


### AST Nodes

The objects representing nodes in the Abstract Syntax Tree (AST) in the `ast`-module all contain a tuple specifying 
the relevant fields with their names.  For the `BinOp`-node from above, for instance, this looks as follows (we leave
out all the unnecessary details here):
```python
class BinOp(expr):
    ...
    _fields = ('left', 'op', 'right')
```
This, again, is an ideal case for _pyPMatch_: it can simply base the deconstructor for AST-nodes on their respective
`_fields` attribute.


### Other Objects

If an object is neither a data class, nor has a `_fields` attribute, finding the relevant data, and its order, is
more difficult, and brittle.  On the basis of a best effort, _pyPMatch_ inspects the `__init__`-method of the class
in question, or, more precisely, the arguments of the `__init__`-method.

In other words: _pyPMatch_ really tries to create a deconstructor based on the constructor.  The underlying assumption
is, of course, that when you, as the programmer using pattern matching, uses a specific class in a pattern, the
constructor's arguments are somehow reflected in an object's fields, and can be extracted later on; even though
there is no reason why this has to be the case.


## Customising Extraction

While _pyPMatch_ does a good job in extracting data from objects in most of the cases, there are use cases, where you
want to directly specify how the extraction should work.  You this by writing your own "deconstruct" function for a 
specific class.

Just for the sake of explanation, you might take the `Person` class from above, and want the deconstructor to return
the name as a single string like `"John Doe"` instead of separated by first, and last name.  For the magic to happen,
you add a static method `__unaplpy__` to your class, which takes the object to deconstruct as its single argument,
and returns either a tuple to signify success, or `None` otherwise.
```python
@dataclass
class Person:
    name: str
    first_name: str
    age: int
    
    @staticmethod
    def __unapply__(obj):
        if isinstance(obj, Person):
            name = obj.first_name + ' ' + obj.name
            return (name, obj.age)
        else:
            return None
```
In your pattern, you can then use `Person` as if it took two arguments for the constructor:
```python
match person:
    case Person("John Doe", johns_age):
        print(f"John is now {johns_age} years old.")
    case _:
        pass
```

There are two points to consider when declaring your own `__unapply__`-method.
- The method must either return a _tuple_, or `None`, where `None` means that the given object does not match.  This
  applies even if you have only a single element to return; it still needs to be packed as a tuple.
- _pyPMatch_ does **not** check the type of the object before calling `__unapply__`.  In case of automated 
  deconstruction as explained above, type checking _does_ take place, but not for `__unapply__`.  Accordingly,
  note how the `__unapply__`-method of `Person` above starts by doing this type checking.  The reasons for not
  doing type checking per default is explained below.


Incidentally, due to Python's method resolving scheme, the `__unapply__`-method does not need to be declared as a
static method.  If it is not a static method, it has no argument except for the mandatory `self`, which takes on the
role of `obj`.  See the example on [custom deconstructors](../examples/pm_extractors.py).

By the way, the naming `__unapply__` stems from [Scala](https://scala-lang.org/), from which _pyPMatch_ has primarily
drawn its ideas, and design.  There are, of course, valid reasons to use one of several other names, but for now, 
`__unapply__` works just as fine.


### Type Checking

Whenever _pyPMatch_ deconstructs a data class, say, it starts by checking if the given object is an instance of the
specific data class in question.  This type check is not done in case it uses an `__unapply__`-method.  The rationale
for this is to allow greater freedom, and support kind of "duck typing".  As long as `__unapply__` is happy with 
whatever object it has received, there is no need for _pyPMatch_ to deny this.

The Scala book has a nice example to illustrate this point.  Let us assume, we are given a string `s`, which should be
an email address, and we want to get the server user for this email-address.  You can, of course, use something like
regular expressions to tackle this problem.  But you can also write a class `Email`, which can do the deconstruction
for strings.
```python
class Email:
    @staticmethod
    def __unapply__(s):
        if type(s) is str and '@' in s:
            parts = s.split('@')
            if len(parts) == 2:
                return tuple(parts)
        return None
        
def get_email_server(s):
    match s:
        case Email(_, ''):
            return "<server missing>"
        case Email(_, server):
            return server
        case _:
            return "<invalid email-address>"
```
Naturally, you can have a fully equipped `Email`-class, which just happens to _also_ support strings in its
deconstructor, or even widen the range of accepted objects further:
```python
class Email:

    def __init__(self, user_name: str, server: str):
        self.user_name = user_name
        self.server = server

    @staticmethod
    def __unapply__(s):
        if isinstance(s, Email):
            return (s.user_name, s.server)
        elif type(s) is str and '@' in s:
            parts = s.split('@')
            if len(parts) == 2:
                return tuple(parts)
        elif hasattr(s, 'user_name') and hasattr(s, 'server'):
            user_name = s.user_name
            server = s.server
            if type(user_name) is str and type(server) is str:
                return (user_name, server)
        return None
```

## Concluding Remarks

Note that deconstruction is always based on a class.  That is, even if the object that is deconstructed in pattern
matching has a `__unapply__`-method, it will never be used.  The reason for this is simple: if we used the 
`__unapply__`-method on a specific object, there is absolutely no telling what the returned values _mean_.
If we base it on classes/types instead, we _know_ that `Email` returns the user name, and the server.

The deconstruction of objects is taking place in a function `unapply`, which resides in
[match_template.py](../pmatch/match_template.py).  It takes an object, and a class as arguments, and then goes through
the following sequence:
- If the class has an `__unapply__`-method, that method is called, and its result is returned.  In this case, there
  is no other deconstruction attempted.  However, if the `__unapply__`-method returns the value `NotImplemented`,
  _pyPMatch_ does continue with the deconstruction process (I am not sure if there really is a use case for this,
  though).
- If the given object is an instance of the given class, the following are tried:
    - If the class is one of the builtin types like `int`, or `str`, there is no further deconstruction done, but
      the empty tuple is returned;
    - If the class (!) has an attribute `_fields`, which is a tuple of strings, the respective attributes of the
      object are read, and then returned as a tuple.  If one of the attributes is missing, `None` is returned instead;
    - If the class has annotated fields (like a data class), the names of the annotated fields are used to choose
      the attributes from the object (similar to `_fields` above).  Names starting with an underscore `_` are ignored;
    - If the class has an  `__init__`-method, _pyPMatch_ inspects its arguments, and assumes that the arguments carry
      the same name as the fields holding the respective data.  Names starting with an underscore `_` are ignored,
      again.  In contrast to the previous methods, the object is not required to have an attribute for each argument
      of the `__init__`-method.  Missing attributes are simply replaced by `None`.  Keep in mind that there needs not
      be an exact match between arguments to `__init__`, and actual attributes;
- A special case is considered: if the given class is the builtin `callable`, _pyPMatch_ checks if the object is
  callable, and returns either an empty tuple, or `None`.
  
The entire code is included below, but please keep in mind that [match_template.py](../pmatch/match_template.py) might
contain a newer, updated version.
```python
def unapply(obj, cls):
    method = getattr(cls, '__unapply__', None)
    if method is not None:
        result = method(obj)
        if result is not NotImplemented:
            return result

    if isinstance(obj, cls):
        # Primitive types are not really deconstructable, but should always register as a match.
        # By returning the object itself as its only argument, we allow the "type check" to be combined
        # with further checks.  Say, you want to make sure you have dictionary with a key `foo`, you can
        # write: `dict({ 'foo': _ })`.  Note that `{ 'foo': _ }` will, in contrast, only check if the
        # given value has a key `'foo'`, but there is no check for its type at all.
        if cls in (bool, bytearray, bytes, complex, dict, float, frozenset, int, list, set, str, tuple):
            return (obj,)

        fields = getattr(cls, '_fields', None)
        if isinstance(fields, tuple):
            try:
                result = [getattr(obj, field) for field in fields if not field.startswith('_')]
                return tuple(result)
            except AttributeError:
                return None

        annotations = getattr(cls, '__annotations__', None)
        if isinstance(annotations, dict) and len(annotations) > 0:
            try:
                result = [getattr(obj, annot) for annot in annotations if not annot.startswith('_')]
                return tuple(result)
            except AttributeError:
                return None

        method = getattr(cls, '__init__', None)
        if hasattr(method, '__code__'):
            code = method.__code__
            result = [getattr(obj, arg, None)
                      for arg in code.co_varnames[1:code.co_argcount+code.co_kwonlyargcount]
                      if not arg.startswith('_')]
            return tuple(result)

        return ()

    # `callable` deconstructs all callable objects
    elif cls is callable and cls(obj):
        return ()

    return None
```
