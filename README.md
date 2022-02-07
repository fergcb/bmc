# BMC
**A simple stack-based language that compiles to [LMC](https://www.peterhigginson.co.uk/LMC/help.html).**

## BMC Basics
BMC is stack-based, meaning that values are stored in a first-in-first-out data structure. When an expression is executed, it takes zero or more values from the top of the stack and does something with them. If the operation has a resulting value, it is added back to the top of the stack.

### Literals
When BMC encounters an integer literal, the value of the literal is added to the top of the stack.

The following code pushes three numbers to the stack (`[1, 2, 3]`). When referring to the stack using square brackets (`[]`), the end right-most element represents the top of the stack, i.e. the last element added.

```
1 2 3
```

### Operations
When BMC encounters a symbol that doesn't look like an integer literal, it tries to find a corresponding operation to execute on the stack. If the symbol doesn't correspond to an operation, it'll throw an error.

The following code pushes three values to the stack, `[1, 2, 3]`, then the `+` (addition) operator pops the top two values and pushes their sum (`[1, 5]`). Finally, the `.` (output) operator pops one value and prints it to the screen (`"5"`, `[1]`).

```
1 2 3 + .
```

## Usage
Before following any of the instructions below, you need to obtain a copy of the files in the repository:
```sh
git clone https://github.com/fergcb/bmc.git
cd ./bmc
```

This project contains three tools: a BMC->LMC compiler, a BMC interpreter and an LMC emulator. Each of them can be accessed from the command line. For full usage instructions, type `python bmc.py -h`.

### Interpreter
The following command executes the BMC code contained in the file `test.bmc`
```sh
python bmc.py interpret -f test.bmc
```
To see the contents of the stack after execution, add the `--dump` flag:
```sh
python bmc.py interpret -f test.bmc --dump
```

### Compiler
The following command compiles the BMC code contianed in the file `test.bmc` into LMC assembly code. By default, it will output the compiled code to the console:
```sh
python bmc.py compile -f test.bmc
```
To write the compiled code to a file, specify a file path using the `-o` flag. If the flag is given without a path, the input path will be used to generate an output path automatically:
```
python bmc.py compile -f test.bmc -o output.lmc
```

### Emulator
The following command executes LMC code (e.g. produced by the compiler) in the emulator. The `--dump` command can also be used here to display the contents of the emulator's memory after executing the code.
```sh
python bmc.py emulate -f output.lmc
```
To save having to run two commands, you can specify the `--exec` flag when compiling to run the compiled code straight away:
```sh
python bmc.py compile -f test.bmc -o --exec
```
The single above command is equivalent to the following:
```sh
python bmc.py compile -f test.bmc -o test.lmc
python bmc.py emulate -f test.lmc
```
To compare the results of interpreting and compiling/emulating the same code, you can use the "compare" tool. This is useful for testing for parity between the interpreter and compiler. The following command will first interpret some BMC code, then compile it to LMC and emulate the resulting LMC code:
```sh
python bmc.py compare -f test.bmc
```

## Instruction Set

| Instruction | Name | Description |
|:-----------:|:---- |:----------- |
| 0...999 | Integer Literal | Push the given integer to the stack. |
| + | Add | Pop two values and push their sum. |
| - | Subtract | Pop two values and push their difference. |
| * | Multiply | Pop two values and push their product. |
| % | Divide | Pop two values and push their quotient. |
| = | Equals | Pop two values. Push 1 if they are equal, or 0 if they are not. |
| ~ | Not | Pop one value. Push 1 if it is 0, or 0 if it is anything else. |
| . | Output | Pop one value and print it to the screen. |
| @ | Peek | Pop one value and use it to index the stack. `0` is the top of the stack. | 
| void | Void | Pop one value and discard it. |
| ! | Call | Pop one value and call the function at that address. |

## Language Constructs
### Constants
A constant is a named value that cannot change after it is defined. The `is` keyword is used to pop a value from the stack and give it a name so that it can be used later in the program. For example, after the code `10 is n` is executed, the token `n` will now push `10` to the stack every time it is executed. For more examples, see the [`"const"` example snippet](https://github.com/fergcb/bmc/blob/main/examples/const.bmc). 

### Control Flow (If/Else)
The `? {...}` construct represents an "if" statement. A value is popped from the stack. If it is truthy (i.e. non-zero), the code inside the curly braces (`{}`) is executed.

If the popped value is falsy, nothing happens and the next instruction is executed. If we want something to happen, we can use the `? {...} : {...}` construct, or the "if-else" statement. This statement works as previously described, but executes the code in the _second_ set of curly braces only if the popped value is falsy.

### Functions
Functions can be defined using the `fn () {}` construct. Symbols in the round brackets (`()`) identify the arguments to the function, and the code in the curly braces will be executed when the function is called. Inside the function, the symbols specified in the argument list can be used to push values from lower down to the top of the stack so that they can be used inside the function.

When a function is defined, some memory is allocated for the function body's code to live in, and then the address of that memory slot is pushed to the stack. This means we can use the `is` keyword to store a reference to the function so that we can call it later, e.g. `fn () {} is my_func`.

To call a function, we use the identifier to fetch its address, and then use the `!` operator to jump to that address. Before calling the function, we need to make sure the values at the top of the stack are the arguments to the function. 

For examples of functions in action, see the [`"add"`](https://github.com/fergcb/bmc/blob/main/examples/add.bmc), [`"count"`](https://github.com/fergcb/bmc/blob/main/examples/count.bmc) and [`"fib"`](https://github.com/fergcb/bmc/blob/main/examples/fib.bmc) example snippets.

## Background
[Little Man Computer (LMC)](https://en.wikipedia.org/wiki/Little_man_computer) is a model of a simple computer with 100 memory locations and a simple von Neumann architecture. I used LMC while teaching CPU architecture and assembly language to A-level Computer Science students during my PGCE placement.

While playing with LMC myself, I noticed that the stored-program design of the simple von Neumann architecture allowed a stack data structure to be implemented by abusing the `DAT` instruction and using arithmetic operations to write to arbitrary memory locations. As a small side-project during that time, I decided to write a higher-level, stack-based toy language that compiles to LMC's assembly language.

I implemented an LMC emulator to test the compiled code. My version of LMC builds on [Peter Higginson's fantastic web-based implementation](https://www.peterhigginson.co.uk/LMC/help.html) with two new features: addressing modes, and macros. The three addressing modes are "immediate" (`#`), "direct" (`&`), and "indirect" (`~`):

```
LDA #42 // Load the number 42 into the accumulator
LDA &42 // Load the value stored at memory location 42
LDA ~42 // Load the value from the address stored in memory location 42
```

Macros are named sections of code that are not executed, but can be inserted at any point throughout the rest of the code. For example, the BMC standard library includes [several macros](https://github.com/fergcb/bmc/blob/main/stdlib/macros.lmc) which allow stack operations to be written more easily.

In addition to these new features, my LMC has an arbitrary number of 32-bit memory cells, rather than the 100 8-bit or 3-digit cells as seen in other implementations. This allows the address portion of an instruction to be 24 bits in length, facilitating the creation of much larger programs.