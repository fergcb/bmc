from collections import deque

class SymbolTable():
    def __init__(self):
        self.scopes = [{}]
    
    def push_scope(self, symbols=None):
        if symbols is None:
            symbols = {}
        self.scopes.append(symbols)
    
    def pop_scope(self):
        self.scopes.pop()
        if len(self.scopes) == 0:
            self.scopes.append({})

    def get(self, key):
        for scope in reversed(self.scopes):
            if key in scope:
                return scope[key]
    
    def set(self, key, value):
        self.scopes[-1][key] = value
    
    def __getitem__(self, key):
        return self.get(key)
    
    def __setitem__(self, key, value):
        return self.set(key, value)

    def __contains__(self, key):
        return any(key in scope for scope in reversed(self.scopes))


def execute(ip, token, stack, queue, symbols, funcs):
    # print(token, stack, "=> ", end="")
    if token["type"] == "num":
        stack.append(token["value"])
    elif token["type"] == "function":
        func = token["value"]
        funcs.append(func)
        addr = len(funcs) - 1
        stack.append(addr)
    elif token["type"] == "return":
        return_value = stack.pop()
        stack.pop() # Pop the base pointer for parity
        return_addr = stack.pop()
        for i in range(token["arg_count"]):
            stack.pop()
        ip = return_addr
        stack.append(return_value)
        symbols.pop_scope()
    elif token["type"] == "constant":
        name = token["value"]
        value = stack.pop()
        symbols[name] = value
    elif token["type"] == "reference":
        name = token["value"]
        if name in symbols:
            stack.append(symbols[name])
        else:
            raise Exception(f"Label '{name}' is undefined.")
    elif token["type"] == "if":
        condition = stack.pop()
        if condition:
            queue.extendleft(reversed(token["value"]))
    elif token["type"] == "if-else":
        condition = stack.pop()
        if condition:
            queue.extendleft(reversed(token["value"][0]))
        else:
            queue.extendleft(reversed(token["value"][1]))
    elif token["type"] == "op":
        op = token["value"]
        if op == "@":
            a = stack.pop()
            stack.append(stack[-(a+1)])
        elif op == "void":
            stack.pop()
        elif op == "!":
            addr = stack.pop()
            func = funcs[addr]
            args = { name: stack[-(i+1)] for i, name in enumerate(reversed(func["args"])) }
            symbols.push_scope(args)
            stack.append(ip)
            stack.append(len(stack))
            queue.extendleft(reversed([*func["block"], { "type": "return", "arg_count": len(func["args"]) }]))
        elif op == "+":
            a = stack.pop()
            b = stack.pop()
            stack.append(a + b)
        elif op == "-":
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)
        elif op == "*":
            a = stack.pop()
            b = stack.pop()
            stack.append(a * b)
        elif op == "/":
            b = stack.pop()
            a = stack.pop()
            stack.append(a // b)
        elif op == "%":
            b = stack.pop()
            a = stack.pop()
            stack.append(a % b)
        elif op == "=":
            a = stack.pop()
            b = stack.pop()
            stack.append(1 if a == b else 0)
        elif op == "~":
            a = stack.pop()
            stack.append(1 if a == 0 else 0)
        elif op == ".":
            print(stack.pop())
        else:
            raise Exception(f"Unrecognised operator '{op}'.")
    else:
        type = token["type"]
        raise Exception(f"Unknown token type '{type}'.")
    # print(stack)
    return ip


def interpret(tokens):
    stack = []
    ip = 0
    queue = deque()

    symbols = SymbolTable()
    funcs = []

    while ip < len(tokens) or len(queue) > 0:
        if len(queue) > 0:
            token = queue.popleft()
        else:
            token = tokens[ip]
            ip += 1
        ip = execute(ip, token, stack, queue, symbols, funcs)

    return stack