from collections import deque

def execute(token, stack, ip, queue):
    if token["type"] == "num":
        stack.append(token["value"])
    elif token["type"] == "if":
        condition = stack.pop()
        if condition:
            queue.extend(token["value"])
    elif token["type"] == "if-else":
        condition = stack.pop()
        if condition:
            queue.extend(token["value"][0])
        else:
            queue.extend(token["value"][1])
    elif token["type"] == "op":
        op = token["value"]
        if op == "+":
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
        elif op == ".":
            print(stack.pop())
    else:
        type = token["type"]
        raise Exception(f"Unknown token type '{type}'.")


def interpret(tokens):
    stack = []
    ip = 0
    queue = deque()

    while ip < len(tokens) or len(queue) > 0:
        if len(queue) > 0:
            token = queue.popleft()
        else:
            token = tokens[ip]
            ip += 1
        execute(token, stack, ip, queue)

    return stack