# Deconstructors

The [introduction](INTRODUCTION.md) already covers how you can check the type of an object, or match any of its fields
to patterns.  However, there are situations when the information you wish to access, and match, is not readily 
available in a universally accessible field.  Or the actual name of the fields might just not be that relevant, 
compared to the order of the data.  Or, finally, you really just want a more convenient way to express your patterns.

Anyway, in such a case where you do not want to, or cannot access an objects data through its attributes, you use a
_de-constructor_ to access the data.  Whereas a _constructor_ takes several bits of data, and mangles them together
to form a new object, the _deconstructor_ takes an object, and try to extract those original bits of data that went
into the constructor in the first place.

_NB: The "deconstructor" is not the same thing as a "destructor".  Its purpose is not to free or destroy an object
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

Python 3.7 has officially introduced _Data Classes_ (see [PEP 557](https://www.python.org/dev/peps/pep-0557/)
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
_there is no reason why this has to be the case_.

