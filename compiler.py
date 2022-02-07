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


def translate(token, args=None):
    type, value = token.values()
    
    if type == "nop":
        return []

    if type == "num":
        return [
            "PUSH #{}".format(value % 255)
        ]
    
    elif type == "function":
        lbl = next_ret()
        skip = next_ret()
        block = translate_sequence(value["block"], value["args"])
        return [
            f"BRA {skip}",
            f"{lbl} NOP",
            *block,
            "POP",
            "STA &_a",
            "POP",
            "STA &_b",
            "POP",
            "STA &_d",
            *(["POP"] * len(value["args"])),
            "LDA &_b",
            "STA &_bp",
            "PUSH &_a",
            "BRA &_d",
            f"{skip} PUSH #{lbl}"
        ]
    
    elif type == "constant":
        name = value
        skip = next_ret()
        return [
            f"BRA {skip}",
            f"{name} DAT",
            f"{skip} POP",
            f"STA &{name}"
        ]
    
    elif type == "reference":
        name = value
        if args is not None and name in args:
            index = len(args) - args.index(name) + 2
            return [
                f"LDA &_bp",
                f"SUB #{index}",
                "STA &_d",
                "LDA ~_d",
                "PUSHACC"
            ]
        else:
            return [
                f"PUSH &{name}"
            ]

    if type == "if":
        block = translate_sequence(value, args)
        end = next_ret()
        return [
            "POP",
            f"BRZ {end}",
            *block,
            f"{end} NOP"
        ]

    if type == "if-else":
        if_block = translate_sequence(value[0], args)
        else_block = translate_sequence(value[1], args)
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
        # EQUALS
        if op == "=":
            equal = next_ret()
            end = next_ret()
            return [
                "POP",
                "STA &_a",
                "POP",
                "SUB &_a",
                f"BRZ {equal}",
                "PUSH #0",
                f"BRA {end}",
                f"{equal} PUSH #1",
                f"{end} NOP"
            ]
        # NOT
        if op == "~":
            zero = next_ret()
            end = next_ret()
            return [
                "POP",
                f"BRZ {zero}",
                "PUSH #0",
                f"BRA {end}",
                f"{zero} PUSH #1",
                f"{end} NOP"
            ]
        # PRINT
        if op == ".":
            return [
                "POP",
                "OUT",
            ]
        # VOID
        if op == "void":
            return [
                "POP"
            ]
        # PEEK
        if op == "@":
            return [
                "POP",
                "STA &_a",
                "PEEK &_a",
                "PUSHACC"
            ]
        # CALL
        if op == "!":
            ret = next_ret()
            return [
                "POP",
                "STA &_d",
                f"PUSH #{ret}",
                f"PUSH &_bp",
                f"LDA &_sp",
                "STA &_bp",
                f"BRA &_d",
                f"{ret} NOP"
            ]
    

    raise Exception(f"Unknown token type '{type}'.")


def translate_sequence(tokens, args=None):
    asm = []
    for token in tokens:
        asm += translate(token, args)
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