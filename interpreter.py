def interpret(tokens):
    stack = []
    ip = 0
    while ip < len(tokens):
        token = tokens[ip]
        if token["type"] == "num":
            stack.append(token["value"])
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
        ip += 1
    return stack