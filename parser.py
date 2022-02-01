import re

def parse_num(source):
    re_match = re.match(r"^(0|([1-9][0-9]{,2}))", source)
    if re_match is not None:
        match = re_match.group(0)
        rest = source[len(match):]
        return ({ "type": "num", "value": int(match) }, rest)
    return (None, source)


def parse_op(source):
    if source[0] in "/+-*.":
        match = source[0]
        rest = source[1:]
        return ({ "type": "op", "value": (match,) }, rest)
    return (None, source)


parse_funcs = [parse_num, parse_op]


def strip_whitespace(source):
    return re.sub(r"[ \t\r\n]", "", source)


def tokenize(source):
    tokens = []
    rest = source
    while len(rest) > 0:
        rest = rest.lstrip()
        for parse in parse_funcs:
            match, rest = parse(rest)
            if match is not None:
                tokens.append(match)
                break
        else:
            col = len(source) - len(rest)
            raise Exception(f"No match found at col {col}.")
    return tokens