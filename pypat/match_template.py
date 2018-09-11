#
# (c) 2018, Tobias Kohn
#
# Created: 17.08.2018
# Updated: 27.08.2018
#
# License: Apache 2.0
#
import inspect


class MatchException(Exception): pass


_NO_VALUE_ = object()


def unapply(obj, cls):
    """
    Checks if the given object `obj` is an instance of class `cls`, and then tries to extract values for the fields.
    If the given object is an instance of the class, the returned value is a tuple (unless overriden by `__unapply__`),
    otherwise `unapply` returns `None`.

    If the class `cls` has an `__unapply__`-method, that method is called on the object, and its result is returned.
    An `__unapply__` method should either return a tuple, `None`, or `NotImplemented`.  If the returned value is
    `NotImplemented`, the function proceeds with other attempts to extract the fields' values.  Otherwise the value is
    returned.   It can be implemented as a normal instance method with `self` as the only parameter, or as a
    class-method that takes the object as an argument.

    If the class has an attribute `_fields`, which must be a `tuple`, then `_fields` is taken to specify the names of
    all fields, for which `unapply` should return a value.  The `_fields` attribute is, for instance, used by the AST.
    The `_fields` list of names is supposed to be accurate.  Hence, if an instance object is missing one or several
    fields, it will not be considered an instance of the class, and the function will return `None`.

    If the class has annotated variables, i. e. the attribute `__annotations__` is present and a non-empty dictionary,
    `unapply` will look for the fields as specified by the keys of `__annotations__`.  In that case, variables without
    annotation are ignored.  This is consistent with Data Classes as proposed in PEP 557.
    As with `_fields`, this list of field names is supposed to be accurate.  If an instance does not implement a field
    for each annotated variable, the function returns `None`.

    If, finally, there is an `__init__` method, `unapply` will extract the parameter names, and then return the value
    for all fields which have the same name as the parameters.  Since the arguments to `__init__` are not necessarily
    an accurate account of fields to be present, any missing fields are just returned as having a value of `None`.
    However, the instance object will still be recognised as an instance of the class.

    In any case, all fields whose name start with an underscore character are ignored.
    """
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


class SkipMatchException(Exception): pass


class MatchGuard(type):

    def __setattr__(self, key, value):
        if key == 'guard':
            if not value:
                raise SkipMatchException()
        else:
            super().__setattr__(key, value)


class Match(metaclass=MatchGuard):

    def __init__(self, value):
        if len(value) == 1:
            self.value = value[0]
        else:
            self.value = tuple(value)

    def __enter__(self):
        return [self.value, False]

    def __exit__(self, exc_type, exc_value, traceback):
        result = exc_type is SkipMatchException or exc_type is None
        if result:
            try:
                frame = inspect.currentframe().f_back
                value, handled = frame.f_locals['__matchvalue__']
            except:
                value, handled = None, True
            if not handled:
                raise MatchException(f"no matching pattern found for {repr(value)}")
        return result


class CaseManager(metaclass=MatchGuard):

    def __init__(self, value_item):
        self._value_item = value_item
        value, handled = value_item
        self._handled = handled
        self._guard = False
        self._value = value

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is SkipMatchException or exc_type is None:
            if self._guard:
                self._value_item[1] = True
            return True
        else:
            return False
