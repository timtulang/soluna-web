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
                match = re.match(r'func\s+(\w+)\(([^)]*)\):', inst)
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
            inst = self.instructions[self.pc]
            
            if inst.endswith(':') or inst.startswith('func ') or inst.startswith('endfunc'):
                # Skip labels, function headers, and endfunc
                self.pc += 1
                continue
            
            await self._execute_instruction(inst)
            
            if self.break_flag:
                # Break out of loop - handled by jump logic
                self.break_flag = False
            
            self.pc += 1
    
    async def _execute_instruction(self, inst: str):
        """Execute a single TAC instruction."""
        inst = inst.strip()
        
        # Handle different instruction types
        if inst.startswith('param '):
            self._handle_param(inst)
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
        # Pattern: [temp =] call func_name, argcount
        match = re.match(r'(?:(\w+)\s*=\s*)?call\s+(\w+),\s*(\d+)', inst)
        if not match:
            return
        
        result_var = match.group(1)
        func_name = match.group(2)
        arg_count = int(match.group(3))
        
        # Pop arguments from parameter stack
        args = self.param_stack[-arg_count:] if arg_count > 0 else []
        self.param_stack = self.param_stack[:-arg_count] if arg_count > 0 else self.param_stack
        
        # Handle built-in functions
        if func_name == 'nova':
            if args:
                await self.output_callback(str(args[0]) + '\n') if self.output_callback else print(args[0])
        elif func_name == 'lumen':
            if args:
                await self.output_callback(str(args[0])) if self.output_callback else print(args[0], end='')
        elif func_name == 'input':
            # Input function - expects a type parameter
            result = await self.input_callback('let') if self.input_callback else input()
            if result_var:
                self._set_value(result_var, result)
        else:
            # User-defined function
            if func_name in self.functions:
                func_info = self.functions[func_name]
                result = await self._call_function(func_name, args)
                if result_var:
                    self._set_value(result_var, result)
    
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
            inst = self.instructions[self.pc]
            if inst.startswith('return'):
                # Parse return value if present
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
        match = re.match(r'ifFalse\s+(\S+)\s+goto\s+(\w+)', inst)
        if match:
            cond_var = match.group(1)
            label = match.group(2)
            
            cond_value = self._eval_expr(cond_var)
            if not self._is_truthy(cond_value):
                if label in self.labels:
                    self.pc = self.labels[label] - 1  # -1 because pc will be incremented after
    
    def _handle_jump(self, inst: str):
        """Handle unconditional jump: goto <label>"""
        match = re.match(r'goto\s+(\w+)', inst)
        if match:
            label = match.group(1)
            if label in self.labels:
                self.pc = self.labels[label] - 1  # -1 because pc will be incremented after
    
    def _handle_break(self):
        """Handle break statement."""
        self.break_flag = True
    
    async def _handle_assignment(self, inst: str):
        """Handle assignment: variable = expression or temp = expression"""
        # Handle different cases
        if ' = ' not in inst:
            return
        
        parts = inst.split(' = ', 1)
        lhs = parts[0].strip()
        rhs = parts[1].strip()
        
        # Handle function calls: temp = call func_name, argcount
        if rhs.startswith('call '):
            match = re.match(r'call\s+(\w+),\s*(\d+)', rhs)
            if match:
                func_name = match.group(1)
                arg_count = int(match.group(2))
                
                # Pop arguments from parameter stack
                args = self.param_stack[-arg_count:] if arg_count > 0 else []
                self.param_stack = self.param_stack[:-arg_count] if arg_count > 0 else self.param_stack
                
                # Call function
                if func_name in self.functions:
                    result = await self._call_function(func_name, args)
                    self._set_value(lhs, result)
                return
        
        # Evaluate RHS
        value = await self._eval_expr_async(rhs)
        
        # Handle array indexing on LHS
        if '[' in lhs:
            match = re.match(r'(\w+)\[(\d+)\]', lhs)
            if match:
                arr_name = match.group(1)
                idx = int(match.group(2))
                arr = self._get_value(arr_name)
                if isinstance(arr, (list, SolunaList)):
                    arr[idx] = value
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
        """Evaluate an expression to a value."""
        expr = expr.strip()
        
        # Handle empty expressions
        if not expr:
            return ""
        
        # Handle literals FIRST - before trying to split on operators
        if expr == 'True':
            return True
        if expr == 'False':
            return False
        if expr == 'iris':
            return True
        if expr == 'sage':
            return False
        
        # Try to parse as number
        try:
            if '.' in expr and expr.count('.') == 1 and not expr.startswith('"'):
                return float(expr)
            if not expr.startswith('"') and not expr.startswith("'"):
                return int(expr)
        except ValueError:
            pass
        
        # Handle string literals (must be before operator splitting!)
        if expr.startswith('"') and expr.endswith('"') and len(expr) > 1:
            return expr[1:-1]
        if expr.startswith("'") and expr.endswith("'") and len(expr) > 1:
            return expr[1:-1]
        
        # Handle array literals: newarray
        if expr == 'newarray':
            return SolunaList()
        
        # Handle array access: arr[idx]
        if '[' in expr and ']' in expr:
            match = re.match(r'(\w+)\[(\w+)\]', expr)
            if match:
                arr_name = match.group(1)
                idx_str = match.group(2)
                try:
                    idx = int(idx_str)
                except ValueError:
                    idx = self._eval_expr(idx_str)
                    if not isinstance(idx, int):
                        idx = int(idx)
                
                arr = self._get_value(arr_name)
                if isinstance(arr, (list, SolunaList)):
                    return arr[idx] if idx < len(arr) else 0
                return 0
        
        # Handle function calls: len(var)
        if expr.startswith('len(') and expr.endswith(')'):
            var_name = expr[4:-1].strip()
            var = self._get_value(var_name)
            if isinstance(var, (list, str)):
                return len(var)
            return 0
        
        # Handle unary operations BEFORE binary operations
        if expr.startswith('NOT '):
            val = self._eval_expr(expr[4:].strip())
            return not self._is_truthy(val)
        
        if expr.startswith('-') and len(expr) > 1 and expr[1] not in '><!=':
            # Check if this is a negative number literal
            try:
                val = float(expr) if '.' in expr else int(expr)
                return val
            except ValueError:
                # It's a negation operator
                val = self._eval_expr(expr[1:].strip())
                try:
                    return -val
                except:
                    return val
        
        # Handle binary operations: a op b
        # Order matters! Check from lowest precedence to highest
        # But only if not inside a string literal
        for op in [' OR ', ' AND ', ' == ', ' != ', ' < ', ' > ', ' <= ', ' >= ', 
                   ' CONCAT ', ' + ', ' - ', ' * ', ' / ', ' % ', ' // ', ' POW ']:
            # Find operator not inside string literals
            pos = 0
            in_string = False
            string_char = None
            while pos < len(expr):
                char = expr[pos]
                if char in '"\'':
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char and (pos == 0 or expr[pos-1] != '\\'):
                        in_string = False
                pos += 1
            
            # Simple split (not inside string) - look for operator
            if op in expr and not (expr.startswith('"') and expr.endswith('"')):
                # Check if operator is outside of strings
                idx = expr.find(op)
                if idx > 0:
                    # Make sure we're not inside a string literal
                    before = expr[:idx]
                    after = expr[idx+len(op):]
                    
                    # Quick check: count quotes before this position
                    quote_count_before = before.count('"') + before.count("'")
                    if quote_count_before % 2 == 0:  # Even number of quotes = outside string
                        parts = [before, after]
                        if len(parts) == 2:
                            left = self._eval_expr(parts[0].strip())
                            right = self._eval_expr(parts[1].strip())
                            return self._apply_operator(op.strip(), left, right)
        
        # Variable or temporary lookup
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
        """Get value of a variable or temporary."""
        if name in self.variables:
            return self.variables[name]
        if name in self.temporaries:
            return self.temporaries[name]
        
        # Try to parse as literal if not found
        try:
            if '.' in name:
                return float(name)
            return int(name)
        except ValueError:
            return name
    
    def _set_value(self, name: str, value: Any):
        """Set value of a variable or temporary."""
        if name.startswith('t'):
            self.temporaries[name] = value
        else:
            self.variables[name] = value
