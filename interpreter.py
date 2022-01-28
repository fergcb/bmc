def interpret(tokens):
    stack = []
    ip = 0
    while ip < len(tokens):
        token = tokens[ip]
        if token["type"] == "num":
            stack.append(token["value"])
        elif token["type"] == "op":
            match token["value"]:
                case ("+",):
                    a = stack.pop()
                    b = stack.pop()
                    stack.append(a + b)
                case ("-",):
                    a = stack.pop()
                    b = stack.pop()
                    stack.append(a - b)
                case (".",):
                    print(stack.pop())
        ip += 1
    return stack