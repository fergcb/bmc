import re

def WS(source):
    re_match = re.match(r"^[ \t]+", source)
    if re_match is not None:
        match = re_match.group(0)
        rest = source[len(match):]
        return ({ "type": "nop", "value": "_" }, rest)
    return (None, source)

def Num(source):
    re_match = re.match(r"^(0|([1-9][0-9]{,2}))", source)
    if re_match is not None:
        match = re_match.group(0)
        rest = source[len(match):]
        return ({ "type": "num", "value": int(match) }, rest)
    return (None, source)


def Op(source):
    if source[0] in "+-*/%.":
        match = source[0]
        rest = source[1:]
        return ({ "type": "op", "value": (match,) }, rest)
    return (None, source)


def Sequence(*matchers):
    def match_sequence(source):
        matches = []
        rest = source
        for matcher in matchers:
            match, rest = matcher(rest)
            if match is None:
                return (None, source)
            matches.append(match)
        return (matches, rest)
    return match_sequence
        

def Option(*matchers):
    def match_option(source):
        for matcher in matchers:
            match, rest = matcher(source)
            if match is None:
                continue
            return (match, rest)
        return (None, source)
    return match_option
        

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


parser = ZeroOrMore(Option(WS, Op, Num))


def strip_whitespace(source):
    return re.sub(r"[ \t\r\n]", "", source)


def tokenize(source):
    tokens, rest = parser(source)

    if tokens is None:
        col = len(source) - len(rest)
        raise Exception(f"No match found at col {col}.")

    if rest != "":
        col = len(source) - len(rest)
        raise Exception(f"Expected end of string, found '{rest[:1]}' at col {col}.")

    return tokens