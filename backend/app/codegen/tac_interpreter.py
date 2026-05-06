"""
TAC INTERPRETER: Executes Three-Address Code directly.

This interpreter takes TAC instructions and executes them sequentially,
maintaining a runtime state including variables, temporaries, and a call stack.

Key features:
- Symbol table for variables with type information
- Temporary variables (t0, t1, t2...)
- Label resolution and jumps
- Function definitions and calls with parameter stacks
- Dynamic arrays (grow on out-of-bounds access)
- Built-in I/O functions (nova, lumen, input)
- Input validation for each type
"""

import re
import asyncio
from typing import Any, Dict, List, Optional, Callable


class SolunaList(list):
    """
    Dynamic list that grows on out-of-bounds access.
    Mirrors the behavior of arrays in the Soluna language.
    """
    def __setitem__(self, key, value):
        if key >= len(self):
            self.extend([0] * (key - len(self) + 1))
        super().__setitem__(key, value)
    
    def __getitem__(self, key):
        if key >= len(self):
            self.extend([0] * (key - len(self) + 1))
        return super().__getitem__(key)
    
class SolunaObject(dict):
    """
    Dynamic dictionary that acts as a Soluna object.
    Allows property access and handles missing properties gracefully.
    """
    pass


class TACInterpreter:
    """
    Executes Three-Address Code (TAC) instructions.
    
    TAC is a low-level intermediate representation where each instruction
    does at most one operation:
    - t0 = a + b  (one operation)
    - x = t0      (assignment)
    - ifFalse cond goto L0  (conditional jump)
    """
    
    def __init__(self, tac_code: str, input_callback: Optional[Callable] = None, 
                 output_callback: Optional[Callable] = None, getch_callback: Optional[Callable] = None):
        """
        Initialize the TAC interpreter.
        
        Args:
            tac_code: String containing TAC instructions (one per line)
            input_callback: Async function to call for input(expected_type) -> value
            output_callback: Async function to call for output(value, newline=True)
            getch_callback: Async function to call for single character input
        """

        self.param_stack: List[Any] = []
        self.break_flag = False
        
        self.step_count = 0
        self.MAX_STEPS = 50000

        self.tac_code = tac_code
        self.instructions = [line.strip() for line in tac_code.split('\n') if line.strip() and not line.strip().startswith(';')]
        
        # State
        self.variables: Dict[str, Any] = {}  # User-defined variables
        self.temporaries: Dict[str, Any] = {}  # Temporary variables (t0, t1, ...)
        self.types: Dict[str, str] = {}  # Variable type tracking (kai, flux, lani, let)
        self.pc = 0  # Program counter
        self.labels: Dict[str, int] = {}  # Label -> instruction index
        self.functions: Dict[str, Dict] = {}  # Function definitions {name -> {params, start_pc, ...}}
        self.call_stack: List[Dict] = []  # Call stack for nested function calls
        self.param_stack: List[Any] = []  # Parameter stack for function calls
        self.break_flag = False  # For break statements in loops

        self.this_stack: List[dict] = []
        
        # I/O callbacks
        self.input_callback = input_callback
        self.output_callback = output_callback
        self.getch_callback = getch_callback
        
        # Pre-process labels and functions
        self._build_label_map()
        self._build_function_map()
    
    def _build_label_map(self):
        """Find all labels and their instruction indices."""
        for i, inst in enumerate(self.instructions):
            if inst.endswith(':') and not inst.startswith('func '):
                label = inst[:-1]
                self.labels[label] = i
    
    def _build_function_map(self):
        """Find all function definitions and their locations."""
        i = 0
        while i < len(self.instructions):
            inst = self.instructions[i]
            if inst.startswith('func '):
                # Parse: func name(param1, param2, ...):
                match = re.match(r'func\s+([\w.]+)\(([^)]*)\):', inst)
                if match:
                    func_name = match.group(1)
                    params_str = match.group(2).strip()
                    params = [p.strip() for p in params_str.split(',')] if params_str else []
                    
                    # Find corresponding endfunc
                    j = i + 1
                    while j < len(self.instructions):
                        if self.instructions[j].startswith('endfunc'):
                            self.functions[func_name] = {
                                'params': params,
                                'start_pc': i + 1,
                                'end_pc': j
                            }
                            break
                        j += 1
            i += 1
    
    async def run(self):
        """Execute all TAC instructions sequentially."""
        while self.pc < len(self.instructions):
            # ---> NEW: Failsafe checks
            self.step_count += 1
            if self.step_count > self.MAX_STEPS:
                raise RuntimeError("Execution Limit Exceeded: Infinite loop detected.")
            
            # Yield control back to the laptop every 500 instructions
            if self.step_count % 500 == 0:
                await asyncio.sleep(0)

            inst = self.instructions[self.pc]
            
            # Fast-forward over function bodies during global execution!
            if inst.startswith('func '):
                match = re.match(r'func\s+([\w.]+)\(', inst)
                if match:
                    func_name = match.group(1)
                    if func_name in self.functions:
                        self.pc = self.functions[func_name]['end_pc'] + 1
                        continue
            
            if inst.endswith(':') or inst.startswith('endfunc'):
                self.pc += 1
                continue
            
            await self._execute_instruction(inst)
            
            if self.break_flag:
                self.break_flag = False
            
            self.pc += 1
    
    async def _execute_instruction(self, inst: str):
        """Execute a single TAC instruction."""
        inst = inst.strip()
        
        # Handle different instruction types
        if inst.startswith('param '):
            self._handle_param(inst)
        elif inst.startswith('type '):
            parts = inst.split()
            if len(parts) == 3:
                self.types[parts[1]] = parts[2]
        elif inst.startswith('call '):
            await self._handle_call(inst)
        elif inst.startswith('return'):
            self._handle_return(inst)
        elif inst.startswith('if'):
            self._handle_conditional_jump(inst)
        elif inst.startswith('goto '):
            self._handle_jump(inst)
        elif inst.startswith('break'):
            self._handle_break()
        elif '=' in inst:
            await self._handle_assignment(inst)
    
    def _handle_param(self, inst: str):
        """Push a parameter onto the parameter stack."""
        # param <value>
        value_str = inst[6:].strip()
        value = self._eval_expr(value_str)
        self.param_stack.append(value)
    
    async def _handle_call(self, inst: str):
        """Handle function call: temp = call func_name, argcount"""
        # Note the updated regex allowing dots in the function name!
        match = re.match(r'(?:([\w.]+)\s*=\s*)?call\s+([a-zA-Z0-9_.]+),\s*(\d+)', inst)
        if not match: return
        
        result_var = match.group(1)
        func_name = match.group(2)
        arg_count = int(match.group(3))
        
        args = self.param_stack[-arg_count:] if arg_count > 0 else []
        self.param_stack = self.param_stack[:-arg_count] if arg_count > 0 else self.param_stack
        
        if func_name == 'nova':
            if args: await self.output_callback(str(args[0]) + '\n') if self.output_callback else print(args[0])
        elif func_name == 'lumen':
            if args: await self.output_callback(str(args[0])) if self.output_callback else print(args[0], end='')
        elif func_name == 'input':
            result = await self.input_callback('let') if self.input_callback else input()
            if result_var: self._set_value(result_var, result)
        elif func_name == 'getch':
            result = await self.getch_callback() if self.getch_callback else input()
            if result_var: self._set_value(result_var, result)
        else:
            # OOP Method Execution
            if '.' in func_name:
                obj_name, method_name = func_name.split('.', 1)
                obj = self._get_value(obj_name)
                
                if isinstance(obj, (dict, SolunaObject)):
                    class_name = obj.get('__class__')
                    actual_func_name = f"{class_name}.{method_name}"
                    
                    if actual_func_name in self.functions:
                        self.this_stack.append(obj)
                        result = await self._call_function(actual_func_name, args)
                        self.this_stack.pop()
                        
                        if result_var: self._set_value(result_var, result)
                        return
                        
            # Standard Function Execution
            if func_name in self.functions:
                result = await self._call_function(func_name, args)
                if result_var: self._set_value(result_var, result)
    
    async def _call_function(self, func_name: str, args: List[Any]) -> Any:
        """Call a user-defined function."""
        func_info = self.functions[func_name]
        params = func_info['params']
        
        # Save current state
        saved_vars = self.variables.copy()
        saved_temps = self.temporaries.copy()
        saved_pc = self.pc
        
        # Bind parameters
        for param, arg in zip(params, args):
            self.variables[param] = arg
        
        # Execute function body
        self.pc = func_info['start_pc']
        return_value = None
        
        while self.pc < func_info['end_pc']:
            # ---> NEW: Failsafe checks for functions
            self.step_count += 1
            if self.step_count > self.MAX_STEPS:
                raise RuntimeError(f"Execution Limit Exceeded: Infinite loop detected inside function '{func_name}'.")
                
            if self.step_count % 500 == 0:
                await asyncio.sleep(0)

            inst = self.instructions[self.pc]
            
            if inst.startswith('return'):
                if inst == 'return':
                    return_value = None
                else:
                    value_str = inst[7:].strip()
                    if value_str:
                        return_value = self._eval_expr(value_str)
                break
            
            if inst.endswith(':') or inst.startswith('func ') or inst.startswith('endfunc'):
                self.pc += 1
                continue
            
            await self._execute_instruction(inst)
            self.pc += 1
        
        # Restore state
        self.variables = saved_vars
        self.temporaries = saved_temps
        self.pc = saved_pc
        
        return return_value
    
    async def _handle_return(self, inst: str) -> Any:
        """Handle return instruction: return [value]"""
        if inst == 'return':
            return None
        
        # return <value>
        value_str = inst[7:].strip()
        if value_str:
            return self._eval_expr(value_str)
        return None
    
    def _handle_conditional_jump(self, inst: str):
        """Handle conditional jump: ifFalse <cond> goto <label>"""
        match = re.match(r'ifFalse\s+(\S+)\s+goto\s+([\w.]+)', inst)
        if match:
            cond_var = match.group(1)
            label = match.group(2)
            
            cond_value = self._eval_expr(cond_var)
            if not self._is_truthy(cond_value):
                if label in self.labels:
                    self.pc = self.labels[label] - 1  # -1 because pc will be incremented after
    
    def _handle_jump(self, inst: str):
        """Handle unconditional jump: goto <label>"""
        match = re.match(r'goto\s+([\w.]+)', inst)
        if match:
            label = match.group(1)
            if label in self.labels:
                self.pc = self.labels[label] - 1  # -1 because pc will be incremented after
    
    def _handle_break(self):
        """Handle break statement."""
        self.break_flag = True
    
    async def _handle_assignment(self, inst: str):
        """Handle assignment: variable = expression or temp = expression"""
        if ' = ' not in inst: return
        
        parts = inst.split(' = ', 1)
        lhs = parts[0].strip()
        rhs = parts[1].strip()
        
        if rhs.startswith('call '):
            await self._handle_call(inst)
            return
        
        value = await self._eval_expr_async(rhs)
        
        # ---> Handle array indexing on LHS
        if '[' in lhs:
            match = re.match(r'^([\w.]+)\[(.*)\]$', lhs)
            if match:
                arr_name = match.group(1)
                idx_str = match.group(2)
                
                try: idx = int(idx_str)
                except ValueError: idx = int(self._eval_expr(idx_str))
                
                arr = self._get_value(arr_name)
                actual_idx = idx - 1
                
                if isinstance(arr, (list, SolunaList)):
                    if arr_name in self.types:
                        base_type = self.types[arr_name]
                        if base_type.startswith('hubble_'): base_type = base_type[7:]
                        value = self._cast_value(value, base_type)
                    arr[actual_idx] = value
                return
                
        # ---> Handle dot notation (Object Property) assignment
        if '.' in lhs and not lhs.replace('.', '', 1).isdigit():
            match = re.match(r'^([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)$', lhs)
            if match:
                obj_name = match.group(1)
                prop_name = match.group(2)
                
                obj = self._get_value(obj_name)
                if isinstance(obj, (dict, SolunaObject)):
                    obj[prop_name] = value
                else:
                    raise RuntimeError(f"Runtime Error: Cannot set property '{prop_name}' on non-object '{obj_name}'")
                return

        # Regular assignment
        self._set_value(lhs, value)

    async def _eval_expr_async(self, expr: str) -> Any:
        """Evaluate expression that might contain async calls."""
        # For now, delegate to sync version
        # TODO: Handle lumina (input) calls
        if 'call input' in expr:
            # Handle input call
            result = await self.input_callback('let') if self.input_callback else input()
            return result
        
        return self._eval_expr(expr)
    
    def _eval_expr(self, expr: str) -> Any:
        expr = expr.strip()
        if not expr: return ""
        while expr.startswith('(') and expr.endswith(')'):
            expr = expr[1:-1].strip()
        
        # 1. Unary '#' Operator (Length)
        if expr.startswith('#'):
            var_name = expr[1:].strip()
            var = self._get_value(var_name)
            if isinstance(var, (list, SolunaList, str)):
                return len(var)
            return 0
        
        if expr == 'newarray':
            return SolunaList()
            
        if expr == 'newobject':
            return SolunaObject()
            
        # 2. Literals (True/False/Strings)
        if expr in ['True', 'iris']: return True
        if expr in ['False', 'sage']: return False


        if expr.startswith('"') and expr.endswith('"') and len(expr) > 1:
            return self._process_escapes(expr[1:-1])
            
        if expr.startswith("'") and expr.endswith("'") and len(expr) > 1:
            return self._process_escapes(expr[1:-1])
        
        # 3. Unary NOT and Negation
        if expr.startswith('NOT '): ...
        if expr.startswith('-') and len(expr) > 1 and expr[1] not in '><!=': ...

        # ---> 4. BINARY OPERATIONS MUST BE HERE <---
        for op in [' OR ', ' AND ', ' == ', ' != ', ' <= ', ' >= ', ' < ', ' > ', 
                   ' CONCAT ', ' + ', ' - ', ' ** ', ' * ', ' // ', ' / ', ' % ', ' POW ']:
            if op in expr:
                idx = self._find_op_outside_blocks(expr, op)
                if idx != -1:
                    left = self._eval_expr(expr[:idx].strip())
                    right = self._eval_expr(expr[idx + len(op):].strip())
                    return self._apply_operator(op.strip(), left, right)

        # ---> 5. ARRAY ACCESS MUST BE AT THE VERY BOTTOM <---
        if '[' in expr and ']' in expr:
            match = re.match(r'^([\w.]+)\[(.*)\]$', expr)
            if match:
                arr_name = match.group(1)
                idx_str = match.group(2)
                try:
                    idx = int(idx_str)
                except ValueError:
                    idx = int(self._eval_expr(idx_str))
                
                arr = self._get_value(arr_name)
                actual_idx = idx - 1
                
                if isinstance(arr, (list, SolunaList)):
                    return arr[actual_idx] if 0 <= actual_idx < len(arr) else 0
                elif isinstance(arr, str):
                    return arr[actual_idx] if 0 <= actual_idx < len(arr) else ""
                return 0
            
        if '.' in expr and not expr.replace('.', '', 1).isdigit():
            # Match patterns like obj_name.property_name
            match = re.match(r'^([a-zA-Z_]\w*)\.([a-zA-Z_]\w*)$', expr)
            if match:
                obj_name = match.group(1)
                prop_name = match.group(2)
                
                obj = self._get_value(obj_name)
                
                if isinstance(obj, (dict, SolunaObject)):
                    return obj.get(prop_name, 0)  # Default to 0 if undefined
                raise RuntimeError(f"Runtime Error: Cannot read property '{prop_name}' of non-object '{obj_name}'")
        
        # 6. Fallback Variable Lookup
        return self._get_value(expr)
    
    def _apply_operator(self, op: str, left: Any, right: Any) -> Any:
        """Apply an operator to two values."""
        if op == '+':
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            if right == 0:
                raise RuntimeError("Division by zero")
            return left / right
        elif op == '//':
            if right == 0:
                raise RuntimeError("Division by zero")
            return int(left // right)
        elif op == '%':
            if right == 0:
                raise RuntimeError("Division by zero")
            return left % right
        elif op == 'POW' or op == '^':
            return left ** right
        elif op == '<':
            return left < right
        elif op == '>':
            return left > right
        elif op == '<=':
            return left <= right
        elif op == '>=':
            return left >= right
        elif op == '==':
            return left == right
        elif op == '!=':
            return left != right
        elif op == 'AND':
            return self._is_truthy(left) and self._is_truthy(right)
        elif op == 'OR':
            return self._is_truthy(left) or self._is_truthy(right)
        elif op == 'CONCAT':
            return str(left) + str(right)
        else:
            return left
    
    def _is_truthy(self, value: Any) -> bool:
        """Check if a value is truthy."""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, (list, tuple)):
            return len(value) > 0
        return bool(value)
    
    def _get_value(self, name: str) -> Any:
        """Get value of a variable, temporary, or implicit 'this' property."""
        # 1. Check if we are inside a method, and if the object owns this property
        if self.this_stack and name in self.this_stack[-1]:
            return self.this_stack[-1][name]
            
        # 2. Check variables and temporaries
        if name in self.variables:
            return self.variables[name]
        if name in self.temporaries:
            return self.temporaries[name]
        
        # 3. Fallback to parsing as literal
        try:
            if '.' in name:
                return float(name)
            return int(name)
        except ValueError:
            return name
    
    def _set_value(self, name: str, value: Any):
        """Set value of a variable, temporary, or implicit 'this' property."""
        if name in self.types:
            value = self._cast_value(value, self.types[name])
            
        # 1. If we are inside a method and the object owns this property, update it!
        if self.this_stack and name in self.this_stack[-1]:
            self.this_stack[-1][name] = value
            return
            
        # 2. Otherwise, update variables/temporaries as normal
        if name.startswith('t'):
            self.temporaries[name] = value
        else:
            self.variables[name] = value

    def _cast_value(self, value: Any, expected_type: str) -> Any:
        """Mimics _cast_lumina from the Python transpiler to enforce types."""
        try:
            # Allow both Arrays and Objects to pass through freely
            if expected_type.startswith('hubble_'):
                if not isinstance(value, (list, SolunaList, dict, SolunaObject)):
                    raise ValueError(f"Expected array or object, got {type(value)}")
                return value
            
            # Separate String Input from Internal Math
            if isinstance(value, str):
                val_str = value.strip()
                # Reject forced scientific notation explicitly for numerical string inputs
                if expected_type in ['kai', 'flux'] and ('e' in val_str.lower()):
                    raise RuntimeError(f"Runtime Error: Invalid input for '{expected_type}'.")
            
            elif isinstance(value, float):
                # Force internal math floats out of scientific notation to check limits properly
                val_str = f"{value:.15f}".rstrip('0').rstrip('.')
                if not val_str or val_str == '-0': 
                    val_str = '0'
            else:
                val_str = str(value).strip()
                
            clean_str = val_str.lstrip('-')
                
            if expected_type == 'kai':
                parts = clean_str.split('.')
                
                # STRICT LIMIT: Enforce 15 whole digits
                if len(parts[0]) > 15:
                    raise RuntimeError("Runtime Error: Integer 'kai' exceeds 15 whole digit limit.")
                
                # TRUNCATE: Convert to float first (to handle decimal strings), then truncate to int
                return int(float(value)) if isinstance(value, str) else int(value)
            
            elif expected_type == 'flux': 
                parts = clean_str.split('.')
                
                # STRICT LIMIT: 15 whole digits
                if len(parts[0]) > 15:
                    raise RuntimeError("Runtime Error: Float 'flux' exceeds 15 whole digit limit.")
                    
                # TRUNCATE fractional part
                if len(parts) > 1 and len(parts[1]) > 8:
                    frac_part = parts[1][:8]
                    is_neg = val_str.startswith('-')
                    truncated_str = f"{'-' if is_neg else ''}{parts[0]}.{frac_part}"
                    return float(truncated_str)
                    
                return float(val_str)
            
            elif expected_type == 'lani':
                if isinstance(value, str):
                    return value.lower() in ['iris', 'true']
                return bool(value)
            elif expected_type in ['selene', 'let']: 
                return str(value)
            elif expected_type == 'blaze':
                s = str(value)
                if len(s) != 1:
                    raise ValueError("Char must be of length 1")
                return s
        except (ValueError, TypeError):
            raise RuntimeError(f"Runtime Error: Cannot cast '{value}' to type {expected_type}")
        
        return value
    
    def _format_output(self, val: Any) -> str:
        """Format numbers to restrict limits and truncate decimals."""
        if isinstance(val, float):
            # Prevent scientific notation from bypassing output length checks
            str_val = f"{val:.15f}".rstrip('0').rstrip('.')
            if not str_val or str_val == '-0': 
                str_val = '0'
            
            is_neg = str_val.startswith('-')
            parts = str_val.lstrip('-').split('.')
            whole_part = parts[0]
            
            # Throw runtime error if float whole digits are too big
            if len(whole_part) > 15:
                raise RuntimeError("Runtime Error: Float 'flux' output exceeds 15 whole digits limit.")
                
            if len(parts) > 1:
                frac_part = parts[1][:8]  # Strictly truncate fractional parts
                formatted = f"{whole_part}.{frac_part}".rstrip('0').rstrip('.')
                return f"-{formatted}" if is_neg and formatted != "0" else formatted
                
            return f"-{whole_part}" if is_neg and whole_part != "0" else whole_part
            
        elif isinstance(val, int) and not isinstance(val, bool):
            # Throw runtime error if integer is too big
            val_str = str(abs(val))
            if len(val_str) > 15:
                raise RuntimeError("Runtime Error: Integer 'kai' output exceeds 15 whole digits limit.")
            return str(val)
            
        return str(val)
    
    def _process_escapes(self, text: str) -> str:
        """Process standard string escape sequences."""
        # Replace double backslashes with a temporary placeholder to protect them
        text = text.replace('\\\\', '\x00')
        
        # Process all the standard escapes from the Soluna specification
        text = text.replace('\\a', '\a')    # Bell
        text = text.replace('\\b', '\b')    # Backspace
        text = text.replace('\\f', '\f')    # Formfeed
        text = text.replace('\\n', '\n')    # Newline
        text = text.replace('\\r', '\r')    # Carriage return
        text = text.replace('\\t', '\t')    # Tab
        text = text.replace('\\v', '\v')    # Vertical tab
        text = text.replace('\\"', '"')     # Double quote
        text = text.replace("\\'", "'")     # Single quote
        
        # Restore the protected literal backslashes
        text = text.replace('\x00', '\\')
        
        return text
    
    def _find_op_outside_blocks(self, expr: str, op: str) -> int:
        """Finds operator ignoring those inside strings, parens, or brackets."""
        in_string = False
        string_char = None
        bracket_depth = 0
        paren_depth = 0
        
        for i in range(len(expr) - len(op) + 1):
            char = expr[i]
            if char in '"\'':
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
            
            if not in_string:
                if char == '[': bracket_depth += 1
                elif char == ']': bracket_depth -= 1
                elif char == '(': paren_depth += 1
                elif char == ')': paren_depth -= 1
            
            # Match operator only if we are at base depth
            if not in_string and bracket_depth == 0 and paren_depth == 0 and expr[i:i+len(op)] == op:
                return i
        return -1
    
    def _find_op_outside_strings(self, expr: str, op: str) -> int:
        """Finds the index of an operator only if it's not inside quotes."""
        in_string = False
        string_char = None
        
        for i in range(len(expr) - len(op) + 1):
            char = expr[i]
            if char in '"\'':
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
            
            if not in_string and expr[i:i+len(op)] == op:
                return i
        return -1
