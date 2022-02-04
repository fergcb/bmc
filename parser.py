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
    
    def __and__(self, other):
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
    def __init__(self, *matchers):
        self.matchers = matchers

    def __add__(self, matcher):
        return Sequence(*self.matchers, matcher)

    def __call__(self, source):
        matches = []
        rest = source
        for matcher in self.matchers:
            match, rest = matcher(rest)
            if match is Fail:
                return (Fail, source)
            matches.append(match.value)
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
    def __init__(self, matcher):
        self.matcher = matcher
    
    def __call__(self, source):
        matches = []
        rest = source
        while len(rest) > 0:
            match, rest = self.matcher(rest)
            if match is Fail:
                break
            matches.append(match.value)
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


WS = RegExp(r"^[ \t]+") >> Entoken("nop")
Num = RegExp(r"^(0|([1-9][0-9]{,2}))") >> SimpleAction(int) >> Entoken("num")

Op = lambda op: Symbol(op) >> Entoken("op")
Operator = Op("+") | Op("-") | Op("*") | Op("/") | Op("%") | Op(".")


parser = Repeat(WS | Operator | Num)


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