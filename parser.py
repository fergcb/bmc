import re

class Matcher():
    def __call__(self, source):
        return None
    
    def __rshift__(self, action):
        return Process(self, action)
    
    def __and__(self, other):
        return Sequence(self, other)
    
    def __or__(self, other):
        return Alternate(self, other)


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
            if match is None:
                return (None, source)
            matches.append(match)
        return (matches, rest)


class Alternate(Matcher):
    def __init__(self, *matchers):
        self.matchers = matchers
    
    def __or__(self, matcher):
        return Alternate(*self.matchers, matcher)

    def __call__(self, source):
        for matcher in self.matchers:
            match, rest = matcher(source)
            if match is not None:
                return (match, rest)
        return (None, source)


class Symbol(Matcher):
    def __init__(self, value):
        self.value = value

    def __call__(self, source):
        if source.startswith(self.value):
            match = self.value
            rest = source[len(match):]
            return (match, rest)
        return (None, source)


class RegExp(Matcher):
    def __init__(self, expr):
        self.expr = expr
    
    def __call__(self, source):
        re_match = re.match(self.expr, source)
        if re_match is not None:
            match = re_match.group(0)
            rest = source[len(match):]
            return (match, rest)
        return (None, source)


class Process(Matcher):
    def __init__(self, matcher, action):
        self.matcher = matcher
        self.action = action
    
    def __call__(self, source):
        match, rest = self.matcher(source)
        if match is None:
            return (None, source)
        return (self.action(match), rest)


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


def ZeroOrMore(matcher):
    def match_zero_or_more(source):
        matches = []
        match, rest = {}, source
        while len(rest) > 0:
            match, rest = matcher(rest)
            if match is None:
                return (None, rest)
            matches.append(match)
        return (matches, rest)
    return match_zero_or_more

WS = RegExp(r"^[ \t]+") >> Entoken("nop")
Num = RegExp(r"^(0|([1-9][0-9]{,2}))") >> SimpleAction(int) >> Entoken("num")

Op = lambda op: Symbol(op) >> Entoken("op")
Operator = Op("+") | Op("-") | Op("*") | Op("/") | Op("%") | Op(".")


parser = ZeroOrMore(WS | Operator | Num)


def tokenize(source):
    tokens, rest = parser(source)

    if tokens is None:
        col = len(source) - len(rest)
        raise Exception(f"No match found at col {col}.")

    if rest != "":
        col = len(source) - len(rest)
        raise Exception(f"Expected end of string, found '{rest[:1]}' at col {col}.")

    return tokens