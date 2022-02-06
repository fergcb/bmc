from os import listdir
from os.path import isfile, join as join_path, split as split_path, splitext

def load_stdlib():
    stdlib = {}

    dir = "./stdlib"
    paths = listdir(dir)
    filepaths = [path for path in paths if isfile(join_path(dir, path))]

    for path in filepaths:
        _, tail = split_path(path)
        name, ext = splitext(tail)
        if ext != ".lmc":
            continue
        with open(join_path(dir, path), "r") as file:
            stdlib[name] = file.read()

    return stdlib


_ret_n = 0
def next_ret():
    global _ret_n
    _ret_n += 1
    return "ret" + str(_ret_n).zfill(3)


def translate(token):
    type, value = token.values()
    
    if type == "nop":
        return []

    if type == "num":
        return [
            "PUSH #{}".format(value % 255)
        ]

    if type == "if":
        block = translate_sequence(value)
        end = next_ret()
        return [
            "POP",
            f"BRZ {end}",
            *block,
            f"{end} NOP"
        ]

    if type == "if-else":
        if_block = translate_sequence(value[0])
        else_block = translate_sequence(value[1])
        elze = next_ret()
        end = next_ret()
        return [
            "POP",
            f"BRZ {elze}",
            *if_block,
            f"BRA {end}",
            f"{elze} NOP",
            *else_block,
            f"{end} NOP"
        ]

    if type == "op":
        op = value
        # ADD
        if op == "+":
            return [
                "POP",
                "STA &_a",
                "POP",
                "ADD &_a",
                "PUSHACC",
            ]
        # SUBTRACT
        if op == "-":
            return [
                "POP",
                "STA &_a",
                "POP",
                "SUB &_a",
                "PUSHACC",
            ]
        # MULTIPLY
        if op == "*":
            ret = next_ret()
            return [
                f"PUSH #{ret}",
                "BRA std_mul",
                f"{ret} PUSHACC",
            ]
        # DIVIDE
        if op == "/":
            ret = next_ret()
            return [
                f"PUSH #{ret}",
                "BRA std_div",
                f"{ret} PUSHACC",
            ]
        # MODULO
        if op == "%":
            ret = next_ret()
            return [
                f"PUSH #{ret}",
                "BRA std_div",
                f"{ret} LDA &_b",
                "PUSHACC",
            ]
        # PRINT
        if op == ".":
            return [
                "POP",
                "OUT",
            ]
    

    raise Exception(f"Unknown token type '{type}'.")


def translate_sequence(tokens):
    asm = []
    for token in tokens:
        asm += translate(token)
    return asm


def compile(tokens):
    asm = translate_sequence(tokens)

    stdlib = load_stdlib()
    return "\n".join([
        stdlib["macros"],
        *asm,
        "HLT",
        stdlib["functions"],
        stdlib["data"]
    ])