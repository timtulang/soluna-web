# Soluna Three-Address Code (TAC) Instructions

Based on the `tacgen.py` and `tac_interpreter.py` implementations, here is the complete list of Three-Address Code (TAC) instructions used in the Soluna compiler.

## 1. Variables & Types
* **`type <var_name> <data_type>`**: Registers a variable or parameter with the interpreter's type system (e.g., `kai`, `flux`, `hubble_kai`). This instructs the runtime to cast values appropriately.
* **`<var_name> = <value>`**: Standard assignment. Can be a literal, a temporary variable, or a resolved expression.

## 2. Operations & Expressions
* **`<temp> = <left> <OP> <right>`**: Binary operations. Supported operators: `+`, `-`, `*`, `/`, `//`, `%`, `POW` (or `^`), `<`, `>`, `<=`, `>=`, `==`, `!=`, `AND`, `OR`, and `CONCAT`.
* **`<temp> = NOT <expr>`** or **`<temp> = -<expr>`**: Unary negation (logical and arithmetic).
* **`<temp> = #<var_name>`**: Length operator for strings and arrays.

## 3. Control Flow
* **`<Label>:`**: Defines a jump target (e.g., `L0:`, `L1:`).
* **`goto <Label>`**: Unconditional jump to a specific label.
* **`ifFalse <cond> goto <Label>`**: Conditional jump. If the `<cond>` evaluates to falsy, the program counter jumps to the label; otherwise, it proceeds to the next line.
* **`break`**: Immediately flags the interpreter to exit the current loop structure.

## 4. Functions
* **`func <name>(<param1>, ...):`**: Declares the start of a function block.
* **`endfunc`**: Marks the end of a function block.
* **`param <value>`**: Pushes an argument onto the interpreter's parameter stack right before a function call.
* **`call <func_name>, <arg_count>`**: Executes a function using the specified number of arguments from the parameter stack. Used for void functions or built-in outputs (e.g., `call nova, 1`).
* **`<temp> = call <func_name>, <arg_count>`**: Executes a function and captures its return value into a temporary variable (e.g., `t0 = call input, 0`).
* **`return`** / **`return <value>`**: Exits the current function, optionally passing a value back to the caller.

## 5. Arrays & Objects (Hubble / Let)
* **`<temp> = newarray`**: Instantiates a new dynamic list (`SolunaList`) in memory.
* **`<temp> = newobject`**: Instantiates a new dictionary-based object (`SolunaObject`) in memory.
* **`<arr_name>[<index>] = <value>`**: Assigns a value to a specific array index. (Note: The interpreter expects 1-based indexing from the Soluna language and converts it to 0-based internally).
* **`<temp> = <arr_name>[<index>]`**: Reads a value from an array into a temporary variable.
* **`<obj_name>.<property> = <value>`**: Sets a property on an object. The generator uses this to stamp class names (`__class__`) and initialize default properties. 
* **`<temp> = <obj_name>.<property>`**: Reads a property from an object.
