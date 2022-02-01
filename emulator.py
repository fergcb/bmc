import re
import numpy as np

ws_expr = re.compile(r"[ \t]+")
label_expr = re.compile(r"[a-zA-Z_][a-zA-Z0-9]*")

# OOOOPPMM AAAAAAAA
# O = opcode / instruction
# P = opcode - mode/misc
# M = addressing mode
# A = address

opcodes = {
    "HLT": 0b0000_00,
    "DAT": 0b0000_00,
    "ADD": 0b0001_00,
    "SUB": 0b0010_00,
    "STA": 0b0011_00,
    "NOP": 0b0100_00,
    "LDA": 0b0101_00,
    "BRA": 0b0110_00,
    "BRZ": 0b0111_00,
    "BRP": 0b1000_00,
    "INP": 0b1001_00,
    "ITC": 0b1001_01,
    "OUT": 0b1001_10,
    "OTC": 0b1001_11,
}

address_modes = {
    "IMMEDIATE": 0b00,
            "#": 0b00,
       "DIRECT": 0b01,
            "&": 0b01,
     "INDIRECT": 0b10,
            "~": 0b10,
}


def strip_comments(lines):
    return list(map(lambda l: l.split("--")[0].strip(), lines))


def filter_empty(strings):
    return list(filter(lambda s: not re.match(r"^[ \t\r\n]*$", s), strings))


def explode_line(line):
    return tuple(filter(lambda s: len(s), map(lambda s: s.strip(), re.split(ws_expr, line))))


def parse_macros(lines):
    lines = lines[:]
    i = 0
    in_macro = False
    start = 0
    name = None
    regions = [] 
    while i < len(lines):
        line = lines[i]
        parts = explode_line(line)
        match(parts):
            case ("macro", x) if type(x) is str and re.match(r"[A-Z][A-Z0-9]*", x):
                if not in_macro:
                    in_macro = True
                    start = i
                    name = x
                else:
                    raise Exception(f"Cannot define a macro at line {i} inside a macro starting at {start}.")
            case ("end",):
                if in_macro:
                    in_macro = False
                    regions.append((name, start, i))
                else:
                    raise Exception(f"Unmatched macro end at line {i}.")
        i += 1
    
    macros = {}
    lines_to_delete = []
    for name, start, end in regions:
        macros[name] = lines[start+1:end]
        lines_to_delete += list(range(start, end + 1))
    
    lines = [line for i, line in enumerate(lines) if i not in lines_to_delete]

    return macros, lines


def match_macro(line, macros):
    parts = explode_line(line)
    label, name, address = None, None, None

    match(parts):
        case (l, n, a) if n in macros:
            label, name, address = l, n, a
        case (l, n) if n in macros:
            label, name = l, n
        case (n, a) if n in macros:
            name, address = n, a
        case (n,) if n in macros:
            name = n
        case _:
            return None
    
    return label, name, address


def expand_macro(macros, name, address="$", route=None):
    if route is None:
        route = []
    route.append(name)

    if address is None:
        address = ""

    macro = macros[name][:]

    i = 0
    while i < len(macro):
        line = macro[i]
        match = match_macro(line, macros)
        if match is not None:
            l2, n2, a2 = match
            if n2 in route:
                raise Exception("Detected cyclical macro definition: " + " > ".join(route + [n2]))
            expanded = expand_macro(macros, n2, a2, route)
            del macro[i]
            for j, line in enumerate(expanded):
                macro.insert(i + j, line)
            if l2 is not None:
                line[i] = l2 + "\t" + line[i]
            i += len(expanded)
        else:
            i += 1
    
    for i, line in enumerate(macro):
        macro[i] = line.replace("$", address)

    return macro

def expand_macros(macros):
    macros = {**macros}
    for name in macros:
        macros[name] = expand_macro(macros, name)
    return macros


def insert_macros(lines, macros):
    lines = list(lines)[:]
    i = 0
    while i < len(lines):
        line = lines[i]
        match = match_macro(line, macros)
        if match is None:
            i += 1
            continue
        del lines[i]
        label, name, address = match
        if address is None:
            address = ""
        macro = macros[name]
        for j, line in enumerate(macro):
            lines.insert(i + j, line.replace("$", address))
        if label is not None:
            lines[i] = label + "\t" + lines[i]
        i += len(macro)
    return lines


def match_op(line):
    parts = explode_line(line)
    label, mnemonic, address = None, None, None

    match(parts):
        case (l, m, a) if m in opcodes:
            label, mnemonic, address = l, m, a
        case (l, m) if m in opcodes:
            label, mnemonic = l, m
        case (m, a) if m in opcodes:
            mnemonic, address = m, a
        case (m,) if m in opcodes:
            mnemonic = m
        case _:
            return None
    
    return label, mnemonic, address


def parse_ops(lines):
    labels = {}
    operations = []
    for i, line in enumerate(lines):
        line = line.split("--")[0].strip()

        if len(line) == 0:
            continue

        op = match_op(line)
        if op is None:
            raise Exception(f"Malformed instruction at line {i}:\n  {line}")

        label, mnemonic, address = op

        if label is not None:
            if re.match(label_expr, label):
                labels[label] = len(operations)
            else:
                raise Exception(f"Invalid label '{label}'.")

        operations.append((opcodes[mnemonic], address))

    return labels, operations


def resolve_address(address, labels):
    if address is None:
        return (0, 0)

    mode = 0x00

    if address[0] in address_modes:
        mode = address_modes[address[0]]
        address = address[1:]

    if re.match(label_expr, address):
        if address in labels:
            address = labels[address]
        else:
            raise Exception(f"Unknown label '{address}'.")

    try:
        address = int(address)
    except:
        raise Exception(f"Invalid address '{address}'.")

    return mode, address
    

def resolve_addresses(operations, labels):
    resolved = []
    for op in operations:
        opcode, address = op
        mode, address = resolve_address(address, labels)
        resolved.append((opcode, mode, address))
    return resolved


def flatten(operations):
    return list(map(lambda op: np.uint16((((op[0] << 2) | op[1]) << 8) | op[2]), operations))


def assemble(code):
    lines = filter_empty(code.split("\n"))
    lines = strip_comments(lines)
    macros, lines = parse_macros(lines)
    macros = expand_macros(macros)
    lines = insert_macros(lines, macros)
    # print("\n".join(map(lambda l: f"{l[0]}\t{l[1]}", enumerate(lines))))
    labels, operations = parse_ops(lines)
    operations = resolve_addresses(operations, labels)
    instructions = flatten(operations)
    return instructions


def read(memory, address, mode):
    if mode == address_modes["IMMEDIATE"]:
        return address
    if mode == address_modes["DIRECT"]:
        return memory[address]
    if mode == address_modes["INDIRECT"]:
        next = memory[address]
        return memory[next]
    raise Exception(f"Invalid address mode {mode}.")


def write(memory, address, mode, value):
    if mode == address_modes["IMMEDIATE"]:
        raise Exception("Cannot write to an immediate address.")
    elif mode == address_modes["DIRECT"]:
        memory[address] = value
    elif mode == address_modes["INDIRECT"]:
        next = memory[address]
        memory[next] = value
    else:
        raise Exception(f"Invalid address mode {mode}.")


def execute(memory):
    pc = 0
    acc = 0

    while pc < len(memory):
        ci = pc
        op = memory[ci]
        opcode = int(op >> 10)
        mode = (op >> 8) & 0b11
        address = np.uint8(op & 0b11111111)
        # print("{}: {:06b}_{:02b} {:08b}".format(pc, opcode, mode, address))
        if opcode == opcodes["HLT"]:
            break
        elif opcode == opcodes["ADD"]:
            acc += read(memory, address, mode)
            pc = ci + 1
        elif opcode == opcodes["SUB"]:
            acc -= read(memory, address, mode)
            pc = ci + 1
        elif opcode == opcodes["STA"]:
            write(memory, address, mode, acc)
            pc = ci + 1
        elif opcode == opcodes["NOP"]:
            pc = ci + 1
        elif opcode == opcodes["LDA"]:
            acc = read(memory, address, mode)
            pc = ci + 1
        elif opcode == opcodes["BRA"]:
            pc = read(memory, address, mode)
        elif opcode == opcodes["BRZ"]:
            if acc == 0:
                pc = read(memory, address, mode)
            else:
                pc = ci + 1
        elif opcode == opcodes["BRP"]:
            if acc > 0:
                pc = read(memory, address, mode)
            else:
                pc = ci + 1
        elif opcode == opcodes["INP"]:
            acc = np.int16(input(" > "))
            pc = ci + 1
        elif opcode == opcodes["ITC"]:
            raise NotImplementedError()
        elif opcode == opcodes["OUT"]:
            print(acc)
            pc = ci + 1
        elif opcode == opcodes["OTC"]:
            raise NotImplementedError()
        else:
            raise Exception("Invalid instruction {0:06b}_{1:02b} {2:08b}. Unrecognised opcode.".format(opcode, mode, address))

        # print("{0:06b}_{1:02b} {2:08b}\t\t => pc: {3} > {4}\tacc: {5}\t{6}".format(opcode, mode, address, ci, pc, acc, memory))
                

def emulate(source, memsize=None):
    object = assemble(source)

    if memsize is None:
        memsize = len(object) + 32
    memory = [np.uint16(0)] * memsize
    memory[:len(object)] = object

    execute(memory)

    return memory


MEM_SIZE = 100

def main():
    code = ""
    object = assemble(code)
    memory = [np.uint16(0)] * MEM_SIZE
    memory[:len(object)] = object[:]
    execute(memory)
   

if __name__ == "__main__":    
    main()