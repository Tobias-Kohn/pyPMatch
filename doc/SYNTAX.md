# On the Syntax of Pattern Matching in Python

_This is a copy of the article on [my homepage](https://tobiaskohn.ch/index.php/2018/09/18/pattern-matching-syntax-in-python/)._

## Introduction

As part of a recent project, I needed to analyse the abstract syntax tree (AST) of Python programs.  To illustrate the task, let us consider a piece of a code that is supposed to optimise a binary-operation-node in the AST.  Traditionally, the code for this looks as follows:
```python
    def visit_BinOp(self, node: ast.BinOp):
        if isinstance(node.left, ast.Num) and \
           isinstance(node.right, ast.Num) and \
           isinstance(node.op, ast.Add):
            return ast.Num(node.left.n + node.right.n)
        elif isinstance(node.right, ast.Num) and \
             isinstance(node.op, (ast.Add, ast.Sub)) and \
             node.right.n == 0:
            return node.left
        elif isinstance(node.right, ast.Num) and \
             isinstance(node.op, (ast.Mul, ast.Div)) and \
             node.right.n == 1:
            return node.left
        else:
            return node
```
However, after having written enough `isinstance`, `hasattr`, and `getattr` calls, along with deeply nested conditions, I decided to rewrite the same code using pattern matching, which ended up looking like this:
```python
    def visit_BinOp(self, node: ast.BinOp):
        match node:
            case BinOp(Num(x), Add(), Num(y)):
                return Num(x + y)
            case BinOp(x, Add()|Sub(), Num(0)):
                return x
            case BinOp(x, Mul()|Div(), Num(1)):
                return x
            case _:
                return node
```
Of course, I also had to implement pattern matching itself, a project which led to [_pyPMatch_](https://github.com/Tobias-Kohn/pyPMatch).  Along the way, however, there were a few design decisions to make, and I started to collect the rationales for my decisions, and challenges I encountered.  While it is certainly impossible to be exhaustive in such a matter, this article reflects my thoughts behind choosing a specific syntax.  In addition, I have also written an article on [Implementing Pattern Matching](https://tobiaskohn.ch/index.php/2018/09/12/implementing-pattern-matching/).

This article is thus an overview of different syntactic possibilities for implementing pattern matching in Python.  Adding pattern matching to Python in a consistent, and useful manner is hard, and involves many details to be considered.  Accordingly, my article is not intended as a final solution, or PEP (Python Enhancement Proposal), but more as an experience report, and a basis for further discussion.


### Previous Discussions

Pattern matching has already been extensively discussed in the Python community over the past few years.  It is simply impossible for me to reflect the entire discussion in this article, and still restrict myself to a manageable size.  If you feel that I have left out an important contribution, or crucial insights from these discussions, I would like to apologise, and I am, of course, always open for constructive suggestions.

The discussion about pattern matching has often been mixed with discussions about switch-statements, particularly concerning the syntax.  Indeed, the structure of match-statements are very reminiscent of switch-statements, although the idea behind it differs.  This article is _not_ about switch-statements, but about pattern matching, as elaborated further below.

Concerning various possibilities for the syntax, there is a similar discussion by Guido van Rossum in the form of [PEP 3103](https://www.python.org/dev/peps/pep-3103/).  Other discussions I am ware of include the following:
- [M. Eriksen: Pattern Matching in Python](https://monkey.org/~marius/pattern-matching-in-python.html)
- [J. Edge: A more generalized switch statement for Python?](https://lwn.net/Articles/693482/)
- [?. Barnert: Pattern matching again](http://stupidpythonideas.blogspot.com/2015/12/pattern-matching-again.html)
- [L. Haoyi: Pattern Matching in MacroPy](https://macropy3.readthedocs.io/en/latest/pattern.html)

And, finally, the idea has already been discussed several times on the Python Ideas Mailing List (this is not a complete list, though):
- [Pattern Matching Syntax (2018)](https://groups.google.com/forum/#!topic/python-ideas/nqW2_-kKrNg)
- [Match statement brainstorm (2016)](https://groups.google.com/forum/#!msg/python-ideas/aninkpPpEAw/wCQ1IH5mAQAJ)
- [Pattern Matching (2015)](https://groups.google.com/d/topic/python-ideas/Rn7df0cq0Kk/discussion)
- [Yet another Switch-Case Syntax Proposal (2014)](https://groups.google.com/d/topic/python-ideas/J5O562NKQMY/discussion)
- [PEP-3151 pattern-matching (2011)](https://groups.google.com/d/topic/python-ideas/GYVAzJeDWCc/discussion)
- [ML Style Pattern Matching for Python (2010)](https://groups.google.com/d/topic/python-ideas/kuoWgMl7LrI/discussion)


## Flavours of Pattern Matching

Pattern matching is the process of inspecting the structure of a given data object, and comparing it to a pattern.  If the object matches the pattern, it is either possible to extract specific information, or to execute an action.  In this article, we will call these aspects **data extraction**, and **dispatch**, respectively.

The two aspects can either be used individually, or in combination. However, the lines between the three categories I present here are sometimes blurred.  Yet, for the purposes of this article, this overview will suffice.
- _Data extraction_ alone usually requires the object in question to adhere to the proposed pattern.  Otherwise an error occurs.  Such data extraction is typically done in assignments.
- _Dispatch_ alone comes most frequently in the form of _multiple dispatch_, or _overloaded functions_: the system is capable of choosing one of several implementations of a function, based on the type, or value of its arguments.  Languages such as _Java_ support overloaded functions, but not full pattern matching;  dispatch is based only on the type of the arguments, and not on values.
- The _combination_ of the two forms leads to structures that resemble switch/case statements.  Based on a given value, and a set of patterns, the system then chooses the first pattern that matches the value, extracts information, and executes the associated code.


### Data Extraction

Python supports a limited form of data extraction through _unpacking_ of sequences, and other iterables:
```python
x, y = y, x
a, b, *c = [2, 3, 5, 7, 11]
n, m = m, n-m
```
There is, of course, a broad range of techniques available to access specific information inside a larger object.  In contrast to unpacking, however, other techniques are not based on a specific _pattern_.

Languages like _Scala_ support a greater class of patterns in assignments, such as `val BinOp(left, op, right) = expr`.  This expects `expr` to be of type `BinOp`, and then assigns the respective fields of `expr` to `left`, `op`, and `right`.


### Dispatch

At first glance, it looks like Python does not even support multiple dispatch of functions.  Indeed, Python does not even have syntactic means to require the parameter of a function to be of a specific type (yes, it has _type hints_/annotations, but they do not _enforce_ the type of an argument.  The specifications are very clear on this issue that those annotations are ignored by the Python interpreted, and shall never be used to enforce typing).  And if we define two functions with the same name, Python happily just replaces the prior definition with the new one (whereas static languages see a name conflict).

On second glance, however, we can indeed have multiple dispatch in Python, and it is actually used.  It occurs, for instance, in the form of the _visitor pattern_.  Here is a trivial example of a class, that acts like a multi-dispatch function:
```python
class Root:
    def visit_0(self, arg):
        return 0
    def visit_float(self, arg: float):
        return arg ** 0.5
    def visit_int(self, arg: int):
        return int(arg ** 0.5)
    def generic_visit(self, arg):
        raise TypeError(f"cannot compute the root of {repr(arg)}")
        
    def __call__(self, *args):
        arg = args[0]
        method = getattr(self, 'visit_' + repr(arg), None)
        if method is not None:
            return method(arg)
        name = arg.__class__.__name__
        method = getattr(self, 'visit_' + name, self.generic_visit)
        return method(arg)
        
root = Root()
print(root(0), root(144))
```
The disadvantage of this approach is that you have to explicitly write the dispatch algorithm yourself (the code inside the `__call__` method).  Or you use an approach with decorators that take over the work for you.  Such a decorator based approach is, for instance, explained by Guido van Rossum in [Five-minute Multimethods in Python](https://www.artima.com/weblogs/viewpost.jsp?thread=101605).

In the context of pattern matching, multi-dispatch through the visitor pattern as shown above is a rather crude approach.  Yes, the dispatch algorithm can take into account arbitrary types, and even extract fields from arguments, and then inspect their types as well.  But there is no support from Python itself to match a value to a specific _pattern_.  In particular, you have to encode the pattern as part of the name, say, or in strings, etc.


### Extract and Dispatch

The combination of data extraction, and multiple dispatch often takes the form of _case-statements_, which superficially look like switch-statements in C, even though the particular choice of keywords varies, of course.  Taking a simple example, this might look as follows (this example can also done through multiple dispatch, of course):
```python
def sum(arg):
    case arg:
        of []: 
            return 0
        of [x, *rest]: 
            return x + sum(rest)
```
Note that in the second case of `[x, *rest]`, we extract data (namely the first element) from the given value, and then choose an action (to return the sum of `x` and the sum of the rest).


## Objective and Scope of the Article

It is the third type of combined data extraction, and dispatch, which is the subject of this article.  A discussion of one of the other two types is, of course, equally thinkable, but beyond the scope of this article.  Moreover, I will not discuss a specific choice a keywords.  Whether the structure is written using `case`, `switch`, or `match` is of little importance in my opinion (it is important when discussing backwards compatibility with existing libraries, which, however, is a completely different matter).  Anyway, when talking about _pattern matching_, I usually refer to this third kind of combined data extraction, and dispatch.

I have implemented pattern matching in Python in the project [pyPMatch](https://github.com/Tobias-Kohn/pyPMatch), and am still continuing its development.  My take on pattern matching is heavily influenced by [Scala](https://scala-lang.org/) (see, e. g., [Pattern Matching in Scala](https://docs.scala-lang.org/tour/pattern-matching.html)).  Indeed, my choice of most symbols, and keywords in _pyPMatch_ is a direct copy from Scala.

In Particular, I will use the following syntax, and speak of _match_-, and _case_-statements, respectively:
```python
def sum(arg):
    match arg:      # <- match-statement
        case []:    # <- case-statement
            return 0
        case [x, *rest]: 
            return x + sum(rest)
```

Finally, this is _not_ about switch-statements.  Of course, the syntax of pattern matching is highly reminiscent of switch statements.  We could even make the case that the classical switch statement is a special case of modern pattern matching.  The motivation, and scope, however, between the two differ greatly (even though there is not always that clear cut a line).  Switch statements tend to stem from optimising native code generation.  By restricting the type of values to compare to integers, or characters, the range can clearly be defined, and the compiler can, e. g., generate tables to directly jump to a specific point in the code.  In Python, this can be emulated through a combination of dictionaries and lambdas.  Pattern matching, on the other hand, is more geared towards the readability of code, and less about efficient implementation in the underlying hardware.  Its main objective is, as explained above, to inspect the structure of data, and either choose an action based on the data's structure, or extract pieces of specific information from larger data structures.


## Match and Case

Why do we need a match-, _and_ a case-statement?  Would it not be enough to just have case-statements, and specify the value each time, like `case arg is [x, *rest]:`?  Sure, writing the value `arg` each time might be annoying, but given the burden of yet another keyword, and structure, this would hardly be enough as rationale.

In fact, the enclosing match-statement fulfills several duties:
- Most obviously, it stores the value of `arg` for later inspection by each case-statement.  This caching is very convenient if the argument is not just a variable name, but a more complex expression, which we do not want to re-evaluate.  This can, however, easily be solved by explicitly storing the value to be inspected in a local variable.
- The match-block forms a unity out of several case-statements, and ensures that only the first matching pattern is applied, and executed.  It is certainly conceivable to have semantics where all matching patterns are applied, and executed.  But apart from being rather unusual, many actual situations rely on the fact that undesired cases can be ruled out before applying a certain pattern.
- The match-block makes sure that at least one pattern matches the value, or raises an exception otherwise.  Again, it is possible to argue if a match-block should raise an exception if no pattern matches.  But raising an exception in case of no matching pattern is probably more in line with the idea of multiple dispatch in functions, and how unpacking in Python is currently handled.
- By forming a unity of case-statements, the compiler could, in principle, perform various optimisations.  If all patterns are simple constants, for example, the compiler could generate a switch-statement with fast dispatch.

In summary, the match-statement's primary duty is to ensure that _exactly one_ case-statement is applied, and executed for each given value.  In addition, it also allows for easier _optimisation_.

Unfortunately, having the match-block comes at the cost of (a) an additional keyword, which can no longer be used as a variable name, and might break older code, (b) adding another level of indentation, and (c) non-orthogonal syntax (see below).  The result is therefore a trade-off, and given that Python code is only moderately optimised, a solution without the surrounding match-block might fit Python even better.

Another consideration of the surrounding match-block is the idea that it act as a switch-statement (a feature that has been asked for in Python for years).  Without the surrounding match-block, pattern matching would offer no more advantage than the traditional `if/elif/else`-chains.

In my implementation _pyPMatch_, I currently support both variants: match-blocks containing case-statements, as well as standalone case-statements.


## Orthogonality

_Orthogonality_ basically means that you can freely combine the structures of a programming language (cf. also the [respective article on Wikipedia](https://en.wikipedia.org/wiki/Orthogonality#Computer_science)).  For example, defining a method in a class adheres to the exact same syntax as defining a function outside a class, because there is no syntactic difference between code inside a class's body, and other code.  You can also define functions inside functions.  So far, there is nothing special about the body of a function, or class (of course, there are differences with respect to name resolving, etc).  However, some statements do not fit this picture, namely, e. g., `return`, and `break`.  Even though the syntax/grammar of Python allows these statements to be placed anywhere, they only make sense inside a function, or loop, respectively.

Although this is hardly ever done, it is in fact perfectly legal to have a loop, say, inside a class's body:
```python
class Foo:
    x = 0
    for i in range(20):
        x += i
print(Foo.x)
```

Now, if we have a surrounding match-block for case-statements, we need to think about what kind of statements would be allowed inside that block, and how and when such statements are executed.  At the moment, I am not aware of any compound statement in Python that would allow only one specific kind of statement to appear inside the block itself.  As shown above, even for classes, say, there is no restriction to functions and assignments only, but any statement is allowed.  This orthogonality is a great strength of Python, as it helps to keep its syntax clear, and simple.

To give a concrete example: the following code would be possible if we allow the block of a match-statement to contain any type of statement.
```python
def sum(arg):
    match arg:
        x = 0
        case []:    
            return 0
        x += 1
        match arg[0]:
            case 0:
                return sum(arg[1:])
        case [x, *rest]: 
            return x + sum(rest)
```
There is a catch, though: when I implemented _match_-blocks, I decided to store/cache the value `arg` in a local variable called `__matchvalue__`.  The choice for a local variable, instead of a global one inside the _pyPMatch_-library, say, is to support multi-threading.  However, the inner match-statement will replace the original `__matchvalue__` variable, so that the last case-statement actually matches against the first element of `arg`, and not the entire argument.  This is not an insurmountable problem, but an example of the details we need to keep in mind.

Another question that comes up with this situation is: does the match-statement leave its block if a pattern has been matched, or does it continue executing the other statements in the block?  In the example above, imagine that the first case-statement `case []:` did not return, and leave the function, but would allow execution inside the function to continue.  We have already established that the match-statement makes sure that no further pattern is tested, and matched.  But would a statement like `x += 1` still be executed?


## A New Kind of Compound Statement

In light of the issues discussed above, a solution without surrounding `match`-block might be much easier to realise.  On the other hand, it is also possible to consider introducing a new kind of compound statement, where only a single kind of statement is allowed to occur inside the block/suite, namely case-statements.

Another consequence of such a limited block-structure is that only one keyword needs to be effectively added to Python.  As in the case of other "semi-keywords" like `async`, `case` could have meaning only directly inside the block of a match-statement, and be a regular name everywhere else.

Or, eventually, we use a syntax that allows for both: single case-statements, as well as blocks of various altenatives as shown below.  But then, we need to reconsider if unmatched values should raise an exception.  A match-statement with a single pattern should probably _not_ raise an exception if it does not match.  However, if the match-statement with several cases is seen as a mere variant of the single-case match-statement, then it should behave the same way, too.
```python
match arg as BinOp(left, '+', right):
    print(left + right)
    
match arg:
    as BinOp(left, '+', right):
        print(left + right)
    as BinOp(left, '-', right):
        print(left - right)
```


## if/elif/else-Chains

With `if`/`elif`/`else`-chains, Python has a structure with a several alternatives.  The basic idea is that of all the alternatives, at most one should be executed.  In addition, the `else` (if present) makes sure that _exactly one_ alternative is chosen.  Sonds familiar?  This is Python's current solution to almost the exact same problem we have been discussing in the context of pattern matching.

Pattern matching has already strong similarities to `if` and its conditional execution.  It is therefore absolutely conceivable to match its syntax to the current syntax of if/elif/else-chains.  This would mean that `match` comes with a possible else clause.  The `else: match` combination could then be shortened to `elmatch`, say (well, it sure looks funny, but keep in mind that this is about the structure, not about the effective choice of keywords):
```python
match arg as BinOp(left, '+', right):
    print(left + right)
elmatch arg as BinOp(left, '-', right):
    print(left - right)
else:
    print("no matching pattern found")
```

As already mentioned earlier, the major disadvantage of such an approach is that the similarity to, and convenience of switch-statements is lost.  While this similarity to switch is not necessary for pattern matching itself, it might still be worth to consider such ramifications.  Interestingly, though, there has been a proposal for "switch-statements" in Python, using a very similar syntax, as [discussed on the mailing list](https://groups.google.com/forum/#!msg/python-ideas/J5O562NKQMY/DrMHwncrmIIJ).


## Try-Except-Blocks

In a [thread about Pattern Matching](https://groups.google.com/forum/#!topic/python-ideas/nqW2_-kKrNg) on the _Python ideas_ mailing list, Andrés Delfino proposed a structure based on `try`/`except` in Python.  The main idea is to avoid the issue of having a specialised kind of body for match-statements, similar to what I have discussed above.
```python
match:
    arg
case BinOp(left, '+', right):
    print(left + right)
case BinOp(left, '-', right):
    print(left - right)
else:
    print("no matching pattern found")
```
Indeed, Python's `try`/`except`-statements provide some limited form of pattern matching for exception handling.  Hence, this proposal picks up an already existing structure in Python, and might therefore feel familiar to Python programmers.

To some extend, this idea is very similar to the if/elif/else-chains explained above.  However, it introduces another oddity with respect to Python's syntax: the first match-block should obviously return a value.  While it is very common in functional languages that each block return a value, this is not the case in Python.  Values are always "returned" explicitly using keywords such as `return`, `yield`, or `raise`.  Moreover, the previously discussed problems of orthogonality apply here as well: would it be possible, for instance, to define functions inside the match-block, break out of a surrounding loop, etc.?


## Coconut

[Coconut](http://coconut-lang.org/) is a programming language that builds on Python, and adds pattern matching, among other features.  It uses both a match- and a case-statement. Interestingly, Coconut's match-statements use the keyword `case`, whereas their case-statements use `match`.  When presenting the examples to illustrate Coconut's approach, we use the convention of this article to remain consistent.

As explained in [Coconut's documentation](https://coconut.readthedocs.io/en/master/DOCS.html#case), match-statements ensure that only one of the pattern cases actually succeeds.  Adapted to the symbols used in this article, Coconut's syntax looks as follows.  Note the `else`-branch, which belongs to the match-statement, and not to the case-statements.
```python
match value:
    case []:
        print("empty")
    case [_]:
        print("singleton")
    case [x, y] if x == y:
        print("duplicate pair")
    case [_, _]:
        print("pair")
else:
    raise TypeError()
```
However, note that Coconut significantly deviates from Python.  For example, two single case-statements can be combined as follows.  Note the `else:`, and `case` being on the same line.
```python
def sum(x):
    case [] in x:
        return 0
    else: case [x, *rest] in x:
        return x + sum(rest)
    else:
        raise TypeError()
```
Further deviations occur in the way patterns are expressed.  Type checking, for instance, is done using the keyword `is`: `case x is int:`.  These issues of inconsistency with existing Python syntax make it very difficult to adapt the proposed syntax to Python itself, to say the least.


## The Syntax of Patterns

The discussion so far has been about the overall structure of pattern matching statements.  It is, however, also worth to consider a few issues concerning the syntax of the actual patterns.

It probably goes without saying that any syntax for patterns should be compatible to current Python as far as possible.  Since Python already has limited support for patterns in the form of (sequence) unpacking, the exact same syntax should also be fully supported in patterns here.  This is with one difference, though.  Current unpacking works on the basis of iteration.  However, in case of fully pattern matching, it might be necessary to try, and unpack a given object several times.
In fact, pattern matching should be possible without any side effects, as it is usually only an _attempt_ to match an object to a pattern.

From current unpacking, we could keep the notion that there is no distinction between lists, tuples, and other iterables.  The following two statements are fully equivalent (in particular, there is no test if source is a tuple, a list, or any other type):
```python
(a, b, c) = source
[a, b, c] = source
```

Apart from sequence unpacking, I have used the following basic rules for the syntax of patterns in _pyPMatch_:
- Names are assignment targets.  Unless a name/identifier is used with a trailer (i. e. part of a call, subscript, or attribute), it is always a target variable.  This is to say that `case pi:`, for instance, would not check if an object if a floating point with the value of `math.pi`, but simply assigns the object to the name `pi` (which is a pattern that always succeeds).  Note that the same is true for unpacking, i. e. `a, pi = 3, 4` simply overwrites any previous value of `pi`.
- The name `_` acts as a wildcard.  It is never effectively assigned something.  This is in contrast to Python, where `_` is a legal name, and could be used as a variable.  However, even in Python, there are various example of `_` being used to assign values, which are of no further interest.
- _A pattern is a proposition how the matched object could have been created, or constructed_.  This is explained below.


### Patterns Corresponds to Constructors

Note that there is a correspondence in unpacking, and packing.  The exact same syntax can be used for both target, and source.  While this example might not make much sense, it shows how `a, b, *c, d` occurs once as a target, and once as a source.  I believe this to be one of the strengths in Python's design.
```python
a, b, *c, d = [2, 3, 5, 7, 11, 13, 17, 19]
x, *y, z = a, b, *c, d
```

This similarity between construction, and de-construction should be upheld in the syntax for any pattern.  This means that the syntax for a pattern should reflect, as good as ever possible, the syntax that would be used to create the respective object.  Compare, for example:
```python
match x:
    case    BinOp(left, '+', right):
        y = BinOp(left, '+', right)
    case    [x, *rest]:
        y = [x, *rest]
assert x == y    # holds true
```

Another way to express this is by saying that a pattern is a proposed constructor for the object in question.  This proposed constructor might contain pieces, of which we do not know the value, expressed by variables, or wildcards `_`.  However, it goes only in one direction: a pattern should syntactically also be a valid constructor, whereas not every valid constructor should also be an allowed pattern.

For a more concrete discussion of how I implemented this relationship between patterns, and constructors, see the document on [deconstructors](https://github.com/Tobias-Kohn/pyPMatch/blob/master/doc/DECONSTRUCTOR.md) in _pyPMatch_.


### Type Checking

Pattern matching is often used for checking the types of values.  Scala, for instance, allows types to be specified with a colon as in `case x: int =>`.  In Python, the colon can be used in a similar capacity to annotate parameters in a function.  Yet, in case-statements, this is trickier.  The entire nature of case-statements suggests that they should be compound statements, where the colon is used to separate the head of the statement from the subsequent body.

However, recall that in Python, types also act as constructors.  For instance, `str(x)` creates a string (of type `str`), based on the value of `x`.  Due to the versatility of these constructors, it is almost impossible to give meaningful suggestions for an object, what the `x` in `str(x)` could be.  This is not strictly necessary, anyway, though, and we can simply allow types to be checked through `case str(_):`, or `case str():`, say.

It might then be handy to allow the constructor of the basic builtin types to contain further patterns.  Above, I have suggested that `case [1, *rest]:`, say, should not check if the object is of type list, but only if the first element in the sequence is `1`.  In case where we explicitly need to specify that the object must be a list, we could then write `case list([1, *rest]):`, for instance.

As an aside: pattern matching in Python should keep type checking to a minimum, and rather rely on _Duck Typing_ wherever possible.  Consequently, _pyPMatch_ does not interpret a pattern as in `case BinOp(left, op, right):` to exactly specify that the _type_ of the object should be `BinOp`.  Instead, `BinOp` is merely a selector of how to extract fields from the object, and it is the implementation of `BinOp`'s deconstructor that decides whether to accept, or reject a certain object based on type.  For more information see [deconstructors](https://github.com/Tobias-Kohn/pyPMatch/blob/master/doc/DECONSTRUCTOR.md) in _pyPMatch_.


### Constants and Alternatives

Matching constants is where pattern matching resembles switch-statements.  While matching a constants seems straight forward, there is a corner case to be considered, though: should a float with the value `2.0` match the pattern in `case 2:`?  While there are arguments for both sides, I would argue that `2.0` matching `2` is more consistent with Python in general.  Consider, for example, `2.0 in (1, 2, 3)`, which evaluated to true.

Whenever a pattern uses a constant value, it is convenient to allow for alternatives.  Using the binary Or-operator `|`, this can easily be expressed:
```python
match x:
    case 0 | 2 | 4 | 6 | 8:
        print("even")
    case 1 | 3 | 5 | 7 | 9:
        print("odd")
    case 0.5:
        print("somewhere in between")
```
Or as part of more complex patterns:
```python
match x:
    case BinOp(left, '+' | '-', right):
        print("Add or Sub")
    case BinOp(left, '*' | '/' | '//', right):
        print("Multiply or Divide")
```
However, it makes sense to restrict the use of alternatives to constant values, and, in particular, exclude names.  The problem with, e. g., `case x| (y,z):` is obviously that either `x`, or `y` and `z` would be defined, but not both.  This does not make sense for pattern matching as discussed in this article.


## Guards

How do you check if two parts in a pattern are equal?  We might, for instance, want to check if the first, and last element of a sequence are equal.  The obvious solution would be `case (x, *_, x):`, but this will not work.  Why?

Python happily reassigns a new value to an existing value.  So, even in the case of tuple unpacking, you can use a target variable several times.  After execution of the assignment with unpacking, the variable will contain the value assigned to it last.  Hence, after the following statement, `x` simply has a value of `7`:
```python
(x, *_, x) = [2, 3, 5, 7]
```
Staying consistent with existing Python means that `case (x, *_, x):` cannot be used to check if the first, and last elements are equal in pattern matching, either (it might be a good idea to restrict all variables to occur at most once as in function parameters, and raise a syntax error otherwise).

There is another way to address this issue.  We map the first, and last element of the sequence to different variables, and then check if both variables are equal.  This subsequent test could, in principle, be done in the body of the respective match-statement.  On the other hand, however, we might think of this requirement as being a part of the pattern - we were just unable to properly express it using the syntax provided by pattern otherwise.  Such conditions, or requirements, which are to be considered to be part of the pattern are called _guards_.

Here are a few examples of how guards might be used to specify an additional requirement for the pattern, which cannot be expressed through the pattern itself:
```python
match arg:
    case (x, *_, y) if x == y:
        print("The first, and last elements are equal")
    case (a, b, c, *rest) if a <= b <= c:
        print("The sequence might be in ascending order")
    case (p, *_) if p == math.pi:
        print("The first element is PI")
```


## Grammar

As an example, here is how a minimal grammar for pattern matching in Python could like (cf. [Python's grammar](https://docs.python.org/3/reference/grammar.html)).  For this grammar, I have chosen the variant with `match arg as pattern:`, but other variant can be realised just as easily.
```python
match_stmt:    'match' or_test match_trailer
match_trailer: 'as' guarded_pattern ':' suite
             | ':' match_suite
match_suite:   NEWLINE INDENT ('as' guarded_pattern ':' suite)* DEDENT

guard_pattern: pattern ['if' or_test]
pattern:       (NAME | '_') ['(' [pattern_args] ')']
             | '(' pattern_list ')'
             | '[' pattern_list ']'
             | const_pattern ('|' const_pattern)*
const_pattern: NUMBER | STRING | 'True' | 'False' | 'None'
             | NAME '(' [const_pattern (',' const_pattern)*] ')'
pattern_args:  (pattern (',' pattern)* | named_pattern) (',' named_pattern)* [',']
named_pattern: NAME '=' pattern
pattern_list:  (pattern | star_pattern) (',' (pattern|star_pattern))* [',']
star_pattern:  '*' pattern
```

Note that the pattern matching I implemented in _pyPMatch_ does not strictly implement this grammar.  Due to its [implementation via `with`-statements](https://tobiaskohn.ch/index.php/2018/09/12/implementing-pattern-matching/), it was necessary to find some compromises, and emphasise a syntax that can easily be detected, and replaced, within regular Python code.  Moreover, the possibility of assigning any subpattern to a variable through the `@`-operator is not integrated here.


## Concluding Remarks

That pattern matching, or switch statements have been constantly proposed over, and over again, during the past few years shows that there is a general interest.  While many of the proposals concerning pattern matching concentrate on a specific syntax, often borrowed from another programming language, I have tried a more abstract take on the matter.  Even though the concrete symbols used in this article are copied from Scala, and hence another programming language as well, the main focus is less on these symbols, and more on the question of how do we integrate pattern matching _well_ with Python.

When well done, pattern matching can highly increase the readability of code.  Together with the fact that Pyhton already supports a limited version of pattern matching in sequence unpacking, pattern matching could fit Python extremely well.  The primary obstacles in adopting pattern matching concern its syntax.  On the one hand, a block-based structure as typically seen in switch-statements might not be a good fit for Python, whereas something based on the notion of if/elif-chains might better reflect Python's current feel.  On the other hand, choosing a keyword for the statement(s) is difficult, and concerns big questions of backwarts compatibility.  The latter issue, however, has not been discussed in this article, but remains for future discussions.

