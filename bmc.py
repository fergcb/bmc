import argparse
import pathlib

from emulator import emulate
from parser import tokenize
from interpreter import interpret
from compiler import compile

ap = argparse.ArgumentParser(description="Compile or interpret BMC code.")
ap.add_argument("mode", choices=["compile", "interpret", "compare", "emulate"])
ap.add_argument("--file", "-f", required=True, type=pathlib.Path, help="Specify an input file of BMC (or LMC in emulate mode) code.")
ap.add_argument("--output", "-o", nargs="?", const=-1, action="store", type=pathlib.Path, help="Specify a file in which to dump compiled LMC code.")
ap.add_argument("--dump", "-d", action="store_true", help="Dump the contents of the stack/memory after execution.")
ap.add_argument("--exec", "-E", action="store_true", help="Emulate the compiled LMC code")

def main():
    args = ap.parse_args()
    mode = args.mode
    if mode not in ["compile", "compare"] and args.output is not None:
        ap.error("--output cannot be specified when there is no code to output.")
    if mode == "compile" and args.dump:
        ap.error("Cannot dump memory when no code is being executed.")
    if args.exec and mode != "compile":
        ap.error("--exec cannot be used outside of 'compile' mode.")

    code = None
    with open(args.file, "r") as file:
        code = file.read()

    compiled = None
    if mode in ["compile", "compare"]:
        tokens = tokenize(code)
        compiled = compile(tokens)

        if args.output is not None:
            in_path = str(args.file)
            file_name = args.output if args.output != -1 else in_path[:in_path.rindex(".")] + ".lmc"
            with open(file_name, "w") as out_file:
                out_file.write(compiled)
        elif mode != "compare":
            print(compiled)

    if mode in ["interpret", "compare"]:
        if mode == "compare":
            print("== INTERPRETED ==")
        
        tokens = tokenize(code)
        stack = interpret(tokens)
        
        if args.dump:
            print(stack)
        
    if mode == "compare" or args.exec:
        code = compiled

    if mode in ["emulate", "compare"] or args.exec:
        if mode == "compare":
            print("\n== COMPILED ==")
        
        memory = emulate(code)
        
        if args.dump:
            print(memory)


if __name__ == "__main__":
    main()
