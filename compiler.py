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

def compile(tokens):
    asm = []

    def get_ci():
        return len(asm)

    _ret_n = 0
    def next_ret():
        nonlocal _ret_n
        _ret_n += 1
        return "ret" + str(_ret_n).zfill(3)

    for token in tokens:
        if token["type"] == "num":
            asm.append("PUSH #{}".format(token["value"] % 255))
        elif token["type"] == "op":
            match token["value"]:
                case ("+",):
                    asm.append("POP")
                    asm.append("STA &_a")
                    asm.append("POP")
                    asm.append("ADD &_a")
                    asm.append("PUSHACC")
                case ("-",):
                    asm.append("POP")
                    asm.append("STA &_a")
                    asm.append("POP")
                    asm.append("SUB &_a")
                    asm.append("PUSHACC")
                case ("*",):
                    ret = next_ret()
                    asm.append(f"PUSH #{ret}")
                    asm.append("BRA std_mul")
                    asm.append(f"{ret} PUSHACC")
                case (".",):
                    asm.append("POP")
                    asm.append("OUT")

    stdlib = load_stdlib() 
    return "\n".join([
        stdlib["macros"],
        *asm,
        stdlib["functions"],
        stdlib["data"]
    ])