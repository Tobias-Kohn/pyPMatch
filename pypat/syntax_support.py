#
# (c) 2018, Tobias Kohn
#
# Created: 16.08.2018
# Updated: 23.08.2018
#
# License: Apache 2.0
#
import datetime, io, os.path, tokenize, types
from . import pama_compiler


class CaseStatement(object):
    """
    A `case` statement represents a line of the form `case ...:`.

    During the "pre-compilation" process, we replace the `case` statement with a  `with` statement.  In order to
    successfully do that, we need the exact locations of the original statement within the text.  `start_pos` and
    `end_pos` give us the positions within the text, so that we can then cut it out, and put something else inside.

    The `case` statement always has a *pattern*.  If the statement is not inside a `match` statement, it also needs
    a *value*.  And it can have an additional *guard*.  The actual syntax looks as follows:
    ```
    case_stmt ::= 'case' [expr 'as'] expr ['if' test] ':' suite
    ```
    In a form like `case x as str():`, where both the *value* `x` and the *pattern* `str` are present, the value is
    tested against the pattern (the example given is equivalent to `if isinstance(x, str):`).  If the case statement
    is inside a `match`, no value must be given, and the above example is written simply as `case str():`.

    In addition to the (value and) pattern, it is possible to specify an additional *guard* after the `if`, which is
    any condition that must be satisfied for the entire pattern to evaluate to `True`.  This might be something like
    `case BinOp(Num(x), Add(), Num(y)) if x == y:`, which tests if both numbers in the binary operation are equal.
    """

    _name_index = 0

    def __init__(self,
                 compiler,
                 start_pos,
                 end_pos,
                 value: str,
                 pattern: str,
                 guard: str):
        self.__class__._name_index += 1
        self.compiler = compiler
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.value = value
        self.pattern = pattern
        self.guard = guard
        self.name = f"Case{self.__class__._name_index}"
        self.code = None

    def __repr__(self):
        return f"case ({self.value} as {self.pattern} if {self.guard}) @ {repr(self.start_pos)}"

    def apply(self, text: str):
        """
        Replace the original `case` statement in the source code by a `with` statement, and return the modified
        text/source code.
        """
        self.code = self.compiler.create_class(self.pattern, self.name, self.guard)
        targets = self.compiler.get_targets()
        value = '__matchvalue__' if self.value is None else f"[{self.value}, False]"
        if len(targets) > 0:
            dest_vars = '(__match__.Match.guard, ' + ', '.join(targets) + ')'
        else:
            dest_vars = '__match__.Match.guard'
        sources = ', '.join([key + '=' + key for key in self.compiler.sources])
        if sources != '':
            sources = ', ' + sources
        result = [
            text[:self.start_pos],
            f"with __match__.{self.name}({value}{sources}) as {dest_vars}:",
            text[self.end_pos:]
        ]
        return ''.join(result)


class MatchStatement(object):
    """
    A `match` statement represents a line of the form `match ...:`.

    As with the `case` statement, a `match` statement is later on replaced with a `with` statement.  We therefore
    need the exact position inside the text of the entire statement, which is given by the fields `start_pos`, and
    `end_pos`, respectively.  In addition to that, a `match` statement always has a value, against which the
    subsequent `case` statements are then tested.
    """

    def __init__(self,
                 start_pos,
                 end_pos,
                 value: str):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.value = value
        self.code = None

    def __repr__(self):
        return f"match @ {repr(self.start_pos)}({self.value})"

    def apply(self, text: str):
        """
        Replace the original `match` statement in the source code by a `with` statement, and return the modified
        text/source code.
        """
        result = [
            text[:self.start_pos],
            f"with __match__.Match([{self.value}]) as __matchvalue__:",
            text[self.end_pos:]
        ]
        return ''.join(result)


class TokenStream(object):
    """
    The `TokenStream` is basically a glorified iterator with look-ahead.  It allows you to peek at the next element
    through the `head` field, removes comments from the stream, and keeps track of the depth of brackets/parentheses
    and indentation.
    """

    def __init__(self, source):
        self.source = iter(source)
        self.bracket_depth = 0
        self.indent_depth = 0
        self._cache = None

    def _get_cache(self):
        if self._cache is None:
            try:
                token = next(self.source)
                if hasattr(token, 'type'):
                    if token.type == tokenize.COMMENT:
                        return self._get_cache()
                    elif token.type == tokenize.INDENT:
                        self.indent_depth += 1
                    elif token.type == tokenize.DEDENT:
                        self.indent_depth -= 1
                if hasattr(token, 'string'):
                    if token.string in ('(', '[', '{'):
                        self.bracket_depth += 1
                    elif token.string in (')', ']', '}'):
                        self.bracket_depth -= 1
                self._cache = token
            except StopIteration:
                pass
        return self._cache

    @property
    def has_next(self):
        return self._get_cache() is not None

    @property
    def head(self):
        return self._get_cache()

    def next(self):
        result = self._get_cache()
        self._cache = None
        return result


class TextScanner(object):
    """
    The `TextScanner` class takes a Python source code as input, tokenizes it, and searches for all the `match` and
    `case` statements.  If you call the `get_text` method, it will then replace those statements in the source code
    by `with` statement, and returns the modified source code, which can be processed by standard Python tools. The
    method `get_match_module()`, on the other hand, returns the module with the actual pattern matching code, already
    compiled, and ready to go.

    The process works in three steps.  As a first step, the scanner finds all occurrences of `match`, and `case`,
    respectively, and roughly parses the statements (it looks for `as` and `if` keywords, in particular).  As a
    second step, the `case` statements are compiled to perform the pattern matching (this is done in other modules
    and not here).  As a third and last step, the algorithm iterates over all found statements in reverse order, and
    replaces each one by an appropriate `with` statement.

    The compilation between steps one and three is necessary, because we need to know the names of variables defined
    by the pattern, as well as the local names used by the pattern.  If a pattern uses the names `foo` and `y`, and
    defines a variable `x`, then the translated code looks like:
    ```
    with __match__.guard(__matchvalue__, foo, y) as x:
    ```
    Note how `foo`, `y`, and `x`, all become part of the new `with` statement, so as to preserve exact semantics.
    """

    def __init__(self, filename: str, source_text: str):
        self.filename = filename
        self.source = source_text
        self.compiler = pama_compiler.Compiler(filename, source_text)
        self._token_list = list(tokenize.tokenize(io.BytesIO(self.source.encode('utf-8')).readline))
        self._statements = []
        self._line_starts = [0]
        for i, c in enumerate(self.source):
            if c == '\n':
                self._line_starts.append(i+1)
        self.find_statements()

    def get_text_position(self, pos):
        """
        Turn a tuple of the form `(row, col)` into a linear integer text position.  The first row is row `1`.
        """
        row, col = pos
        return self._line_starts[row-1] + col

    def parse_case(self, token_stream: TokenStream):
        case_token = token_stream.next()
        assert case_token.string == 'case'
        value = None
        pattern = None
        guard = None
        start = self.get_text_position(case_token.end)
        while token_stream.has_next:
            while token_stream.has_next and token_stream.bracket_depth > 0:
                token_stream.next()
            token = token_stream.next()
            if token.string == 'as' and value is None:
                value = self.source[start:self.get_text_position(token.start)].strip()
                start = self.get_text_position(token.end)

            elif token.string == 'if' and pattern is None:
                pattern = self.source[start:self.get_text_position(token.start)].strip()
                start = self.get_text_position(token.end)

            elif token.string == ':' and token_stream.head.type in (tokenize.NL, tokenize.NEWLINE):
                s = self.source[start:self.get_text_position(token.start)].strip()
                if pattern is None:
                    pattern = s
                else:
                    guard = s
                start_pos = self.get_text_position(case_token.start)
                end_pos = self.get_text_position(token.end)
                return CaseStatement(self.compiler, start_pos, end_pos, value, pattern, guard)

        raise SyntaxError("unexpected EOF while scanning 'case'")

    def parse_match(self, token_stream: TokenStream):
        match_token = token_stream.next()
        assert match_token.string == 'match'
        while token_stream.has_next:
            while token_stream.has_next and token_stream.bracket_depth > 0:
                token_stream.next()
            token = token_stream.next()
            if token.string == ':':
                start_pos = self.get_text_position(match_token.start)
                end_pos = self.get_text_position(token.end)
                value = self.source[self.get_text_position(match_token.end):self.get_text_position(token.start)].strip()
                return MatchStatement(start_pos, end_pos, value)

        raise SyntaxError("unexpected EOF while scanning 'match'")

    def find_statements(self):
        token_stream = TokenStream(self._token_list)
        # The `match_indent` is used to keep track if we are inside the suite of a `match`.  This is needed because the
        # `case` statement slightly vary in syntax and meaning, depending on whether they are inside a `match` or not.
        match_indent = -1
        while token_stream.has_next:
            token = token_stream.next()
            # We only look for `match` and `case` at the very beginning of a line.
            if token.type in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING):
                token = token_stream.head
                if token is None:
                    break

                elif token.string == 'match':
                    # At the moment, we cannot nest `match` because we need to store the value to match against in
                    # a local variable, which would be overriden by nested match-statements.
                    if match_indent != -1:
                        raise SyntaxError("'match' cannot be nested")
                    match_indent = token_stream.indent_depth
                    match = self.parse_match(token_stream)
                    self._statements.append(match)

                elif token.string == 'case':
                    indent = token_stream.indent_depth
                    case = self.parse_case(token_stream)
                    self._statements.append(case)
                    # The `case` statements must have a value exactly iff it is not inside a `match` suite.
                    if match_indent != indent-1 and case.value is None:
                        raise SyntaxError("'case' without value outside 'match'")
                    elif match_indent >= 0 and case.value is not None:
                        raise SyntaxError("'case' with value inside 'match'")

                elif token.type in (tokenize.DEDENT, tokenize.INDENT):
                    if token_stream.indent_depth <= match_indent:
                        match_indent = -1

    def get_match_code(self):
        """
        Returns the source code of the match module, if there is any.  Otherwise returns `None`.
        """
        if len(self._statements) > 0:
            result = [
                "# Auxiliary module for pattern matching (PyMa)\n"
                "# Created: " + str(datetime.datetime.now()),
            ]
            name = os.path.join(os.path.dirname(__file__), 'match_template.py')
            with open(name) as f:
                result.append(''.join(list(f.readlines())))
            for stmt in self._statements:
                if stmt.code is not None:
                    result.append(stmt.code)
            return '\n\n'.join(result)
        else:
            return None

    def get_match_module(self):
        """
        Returns the code where the actual pattern matching takes places, compiled to a module.  If not pattern
        matching is present, the function returns `None`.
        """
        code = self.get_match_code()
        if code is not None:
            mod = types.ModuleType()
            code = __builtins__.compile(code, '__match__', 'exec')
            exec(code, mod.__dict__)
            return mod
        else:
            return None

    def get_text(self):
        """
        Returns the source code text, where all the `match` and `case` statements have been replaced by appropriate
        `with` statements.
        """
        text = self.source
        for stmt in reversed(self._statements):
            text = stmt.apply(text)
        return text
