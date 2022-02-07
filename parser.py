import re

class Result():
    def __init__(self, value):
        self.value = value

Empty = Result(None)
Fail = Result(None)

class Matcher():
    def __call__(self, source):
        return None
    
    def __rshift__(self, action):
        return Process(self, action)
    
    def __add__(self, other):
        return Sequence(self, other)
    
    def __or__(self, other):
        return Alternate(self, other)


class Optional(Matcher):
    def __init__(self, matcher):
        self.matcher = matcher
    
    def __call__(self, source):
        match, rest = self.matcher(source)
        if match is not Fail:
            return (Result(match.value), rest)
        return (Empty, source)


class Sequence(Matcher):
    def __init__(self, *matchers, ignore_whitespace=True):
        self.matchers = matchers
        self.ignore_whitepace = ignore_whitespace

    def __add__(self, matcher):
        return Sequence(*self.matchers, matcher)

    def __call__(self, source):
        matches = []
        rest = source
        for matcher in self.matchers:
            if self.ignore_whitepace:
                rest = rest.lstrip()
            match, rest = matcher(rest)
            if match is Fail:
                return (Fail, source)
            matches.append(match.value)
        if self.ignore_whitepace:
            rest = rest.lstrip()
        return (Result(matches), rest)


class Alternate(Matcher):
    def __init__(self, *matchers):
        self.matchers = matchers
    
    def __or__(self, matcher):
        return Alternate(*self.matchers, matcher)

    def __call__(self, source):
        for matcher in self.matchers:
            match, rest = matcher(source)
            if match is not Fail:
                return (Result(match.value), rest)
        return (Fail, source)


class Repeat(Matcher):
    def __init__(self, matcher, ignore_whitespace=True):
        self.matcher = matcher
        self.ignore_whitespace = ignore_whitespace
    
    def __call__(self, source):
        matches = []
        rest = source
        while len(rest) > 0:
            if self.ignore_whitespace:
                rest = rest.lstrip()
            match, rest = self.matcher(rest)
            if match is Fail:
                break
            matches.append(match.value)
        if self.ignore_whitespace:
            rest = rest.lstrip()
        if len(matches) > 0:
            return (Result(matches), rest)
        return (Fail, source)


class Symbol(Matcher):
    def __init__(self, value):
        self.value = value

    def __call__(self, source):
        if source.startswith(self.value):
            match = self.value
            rest = source[len(match):]
            return (Result(match), rest)
        return (Fail, source)


class RegExp(Matcher):
    def __init__(self, expr):
        self.expr = expr
    
    def __call__(self, source):
        re_match = re.match(self.expr, source)
        if re_match is not None:
            match = re_match.group(0)
            rest = source[len(match):]
            return (Result(match), rest)
        return (Fail, source)


class Lazy(Matcher):
    def __init__(self, matcher_func):
        self.matcher_func = matcher_func
        self.matcher = None
    
    def __call__(self, source):
        if self.matcher is None:
            self.matcher = self.matcher_func()
        return self.matcher(source)


class Process(Matcher):
    def __init__(self, matcher, action):
        self.matcher = matcher
        self.action = action
    
    def __call__(self, source):
        match, rest = self.matcher(source)
        if match is Fail:
            return (Fail, source)
        processed = self.action(match.value)
        
        return (Result(processed), rest)


class Action():
    def __call__(self, match):
        return None


class SimpleAction(Action):
    def __init__(self, transformer):
        self.transformer = transformer
    
    def __call__(self, match):
        return self.transformer(match)


class Entoken(Action):
    def __init__(self, type):
        self.type = type
    
    def __call__(self, value):
        return {
            "type": self.type,
            "value": value
        }

class Select(Action):
    def __init__(self, *indices):
        self.indices = indices
    
    def __call__(self, values):
        if len(self.indices) == 1:
            return values[self.indices[0]]
        return [v for i, v in enumerate(values) if i in self.indices]

class Map(Action):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, values):
        return { key: values[index] for key, index in self.kwargs.items() }

def WS():
    return RegExp("^[ \t\r\n]+")

def Num():
    return RegExp(r"^(0|([1-9][0-9]{,2}))") >> SimpleAction(int)

def NumberLiteral():
    return Num() >> Entoken("num")

def Literal():
    return NumberLiteral()

Op =  lambda op: Symbol(op) >> Entoken("op")
def Operator():
    return Op("+") | Op("-") | Op("*") | Op("/") | Op("%") | Op("=") | Op(".") | Op("@") | Op("!") | Op("~") | Op("void")

def Name():
    return RegExp(r"[_a-zA-Z][_a-zA-Z0-9]*")

def Reference():
    return Name() >> Entoken("reference")

def ArgumentList():
    return Symbol("(") + Repeat(Name()) + Symbol(")") \
        >> Select(1)

def FuncStmt():
    return (Symbol("fn") + ArgumentList() + Block()) \
        >> Map(args=1, block=2) >> Entoken("function")

def ConstStmt():
    return Sequence(Symbol("is"), WS(), Name(), ignore_whitespace=False) \
        >> Select(2) >> Entoken("constant")

def IfStmt():
    return (Symbol("?") + Block()) \
        >> Select(1) >> Entoken("if")

def IfElseStmt():
    return (Symbol("?") + Block() + Symbol(":") + Block()) \
        >> Select(1, 3) >> Entoken("if-else")

def Statement():
    return Lazy(IfElseStmt) | Lazy(IfStmt) | Lazy(FuncStmt) | Lazy(ConstStmt)

def Segment():
    return Repeat(Statement() | Operator() | Literal() | Reference())

def Block():
    return (Symbol("{") + Segment() + Symbol("}")) \
        >> Select(1)

parser = Segment()


def tokenize(source):
    match, rest = parser(source)

    if match is Fail:
        col = len(source) - len(rest)
        raise Exception(f"No match found at col {col}.")

    if rest != "":
        col = len(source) - len(rest)
        raise Exception(f"Expected end of string, found '{rest[:1]}' at col {col}.")

    tokens = match.value

    return tokens