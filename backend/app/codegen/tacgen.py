class TACGenerator:
    """
    THREE-ADDRESS CODE (TAC) GENERATOR
    
    This class generates "Three-Address Code" - an intermediate representation
    of the Soluna program between the high-level language and the final machine code.
    
    Think of it like this:
    - High-level code: x = (a + b) * c
    - TAC: 
        t0 = a + b
        t1 = t0 * c
        x = t1
    
    Each instruction does at most ONE operation (t0 = t1 OP t2).
    This makes it easy to optimize and convert to machine code later.
    
    Key concepts:
    - Temporary variables (t0, t1, t2...): Store intermediate results
    - Labels (L0, L1, L2...): Jump targets for control flow (if, while, etc)
    - Code emission: Building up instructions line by line
    - Visitor pattern: Walking the parse tree and converting each node to TAC
    """
    
    def __init__(self):
        """
        Initialize the TAC generator.
        
        Instance variables:
        - code: List of TAC instructions (strings)
        - temp_count: Counter for generating unique temporary variable names
        - label_count: Counter for generating unique labels for control flow
        - symbol_table: Maps variable names to their types
        """
        self.code = []
        self.temp_count = 0
        self.label_count = 0
        self.symbol_table = {}

    def new_temp(self):
        """
        Generate a new temporary variable name.
        
        Each time we need to store an intermediate result, we create a new temp.
        Example: t0, t1, t2, t3, ...
        
        Returns: A string like "t0", "t1", etc.
        """
        name = f"t{self.temp_count}"
        self.temp_count += 1
        return name

    def new_label(self):
        """
        Generate a new label for control flow.
        
        Labels are jump targets used in if/else, while loops, and function calls.
        Example: L0, L1, L2, ...
        
        TAC uses jumps like: "ifFalse condition goto L0"
        (If condition is false, jump to label L0)
        
        Returns: A string like "L0", "L1", etc.
        """
        name = f"L{self.label_count}"
        self.label_count += 1
        return name

    def emit(self, instruction):
        """
        Add an instruction to the TAC code.
        
        This is the basic building block - every TAC operation uses this
        to add one line of code.
        
        Args:
            instruction: A string representing one TAC instruction
        
        Example:
            self.emit("t0 = 5")
            self.emit("t1 = t0 + 3")
            self.emit("x = t1")
        """
        self.code.append(instruction)

    def generate(self, tree):
        """
        Main entry point: Generate TAC code from the parse tree.
        
        Steps:
        1. Visit the entire parse tree (convert each node to TAC)
        2. Join all instructions with newlines
        3. Return the complete TAC program
        
        Args:
            tree: The parse tree from the parser
        
        Returns:
            A string containing the complete TAC program, one instruction per line
        """
        self.visit(tree)
        return "\n".join(self.code)

    def visit(self, node, *args, **kwargs):
        """
        Universal visitor: Dispatch to the right handler based on node type.
        
        This is the VISITOR PATTERN - a way to handle different types of objects
        with different methods, without one giant if/else block.
        
        Algorithm:
        1. If node is None, return empty
        2. If node is a TOKEN (leaf node):
           - Convert special values: "iris" → "True", "sage" → "False"
           - Otherwise, return the token's value as-is
        3. If node is a parse tree node:
           - Get its type (e.g., "expression", "statement", "var_dec")
           - Call the corresponding visit method (e.g., visit_expression, visit_statement)
           - Return the result of that method
        
        Args:
            node: A parse tree node or TOKEN
            *args, **kwargs: Additional arguments to pass to visitor methods
        
        Returns:
            The result of the visitor method (usually a string or empty)
        """
        if not node: return ""
        if isinstance(node, dict) and node.get("type") == "TOKEN":
            val = node.get("value")
            if val == "iris": return "True"
            if val == "sage": return "False"
            return str(val)
        
        node_type = node.get("type")
        method_name = f"visit_{node_type}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, *args, **kwargs)

    def generic_visit(self, node, *args, **kwargs):
        """
        Default visitor for nodes that don't have a specific visit method.
        
        Simply recursively visit all children.
        This handles tree nodes we don't have special logic for - we just
        traverse deeper to find the actual data.
        
        Args:
            node: A parse tree node
            *args, **kwargs: Additional arguments to pass to children
        
        Returns:
            Concatenated results from all children
        """
        if not node or "children" not in node: return ""
        results = []
        for child in node["children"]:
            res = self.visit(child, *args, **kwargs)
            if res: results.append(res)
        return "".join(results)

    # --- Expression Logic ---
    
    def _flatten_and_build_expr(self, first_operand_str, tail_node):
        """
        Convert an expression into a sequence of three-address instructions.
        
        Problem we're solving:
        High-level: x = a + b * c - d
        Can't do this in one instruction. Need to break it down.
        
        Solution - TAC (three-address code):
        t0 = b * c
        t1 = a + t0
        t2 = t1 - d
        x = t2
        
        Algorithm:
        1. Parse the expression into parts: [left, op, right, op, right, ...]
        2. Process left-to-right:
           - Take the first two operands and operator
           - Create a temporary variable for the result
           - Emit: temp = operand1 OP operand2
           - Use the temporary for the next operation
        3. Standardize operators for the IR:
           - "&&" or "and" → "AND"
           - "||" or "or" → "OR"
           - ".." → "CONCAT" (string concatenation)
           - "^" → "POW" (exponentiation)
        
        Args:
            first_operand_str: The first operand (as a string)
            tail_node: The rest of the expression (recursive structure)
        
        Returns:
            The name of the temporary variable with the final result
        """
        parts = [first_operand_str]
        curr_tail = tail_node
        
        while curr_tail and curr_tail.get("children"):
            op_node = self._find_child(curr_tail, "general_op")
            op_token = self._find_token(op_node)
            op_val = op_token["value"] if op_token else ""
            
            factor_node = self._find_child(curr_tail, "expr_factor")
            factor_str = self.visit(factor_node)
            
            parts.append(op_val)
            parts.append(factor_str)
            curr_tail = self._find_child(curr_tail, "expr_tail")
            
        if len(parts) == 1:
            return parts[0]

        # Left-to-right sequential evaluation into temporaries
        result = parts[0]
        for i in range(1, len(parts), 2):
            op = parts[i]
            right = parts[i+1]
            
            # Standardize logic/concat operators and exponentiation
            if op in ["&&", "and"]: op = "AND"
            elif op in ["||", "or"]: op = "OR"
            elif op == "..": op = "CONCAT"
            elif op == "^": op = "POW"
                
            temp = self.new_temp()
            self.emit(f"{temp} = {result} {op} {right}")
            result = temp
            
        return result

    def visit_simple_expr(self, node):
        """
        Handle a simple expression (no negation).
        
        Example: a + b * c
        (Not: -(a + b) with negation)
        
        Steps:
        1. Find the first factor (operand)
        2. Find the tail (remaining operators and operands)
        3. Flatten and build into TAC
        """
        factor_node = self._find_child(node, "expr_factor")
        factor_str = self.visit(factor_node)
        tail_node = self._find_child(node, "expr_tail")
        return self._flatten_and_build_expr(factor_str, tail_node)

    def visit_multi_expr(self, node):
        """
        Handle an expression with unary negation.
        
        Example: -(a + b) or NOT(condition)
        
        Steps:
        1. Check if there's a unary operator (! or NOT)
        2. Get the expression to negate
        3. If there is negation, create a temporary: temp = operator + expression
        4. Continue with flattening
        """
        unary_node = self._find_child(node, "unary_negation")
        unary_str = self.visit(unary_node) if unary_node else ""
        
        expr_node = self._find_child(node, "expression")
        expr_str = self.visit(expr_node)
        
        first_operand = expr_str
        if unary_str:
            temp = self.new_temp()
            self.emit(f"{temp} = {unary_str}{expr_str}")
            first_operand = temp
            
        tail_node = self._find_child(node, "expr_tail")
        return self._flatten_and_build_expr(first_operand, tail_node)

    def visit_unary_negation(self, node):
        """
        Handle unary negation: ! (logical NOT) and - (arithmetic negation)
        
        Returns the operator string for use in expressions.
        
        Examples:
        - "!" → "NOT "
        - "not" → "NOT "
        - "-" → "-"
        
        The space after "NOT" is important so "NOT" doesn't get
        concatenated with the operand.
        """
        if not node or "children" not in node: 
            return ""
        
        results = []
        for child in node["children"]:
            if child.get("type") == "TOKEN":
                val = child.get("value")
                # Translate both '!' and 'not' to TAC's 'NOT ' with trailing space
                if val in ["!", "not"]:
                    results.append("NOT ")
            else:
                results.append(self.visit(child))
                
        return "".join(results)

    # --- Statements ---

    def visit_var_dec(self, node):
        """
        Handle variable declaration: kai x = 5;
        
        Steps:
        1. Extract the type (kai, flux, let, etc.)
        2. Extract the variable name and initial value
        3. Add the variable to the symbol table
        4. Emit TAC assignment: x = <value>
        """
        data_type_node = self._find_child(node, "data_type")
        data_type = self._find_token(data_type_node)["value"] if data_type_node else ""
        
        var_init = self._find_child(node, "var_init")
        if not var_init: return ""
        
        ident_node = self._find_token(var_init, "identifier")
        init_node = self._find_child(var_init, "value_init")
        
        if ident_node and init_node:
            var_name = ident_node["value"]
            self.symbol_table[var_name] = data_type
            val_temp = self.visit(init_node)
            self.emit(f"{var_name} = {val_temp}")
        return ""

    def visit_assignment_statement(self, node):
        """
        Handle assignment: x = 5; or x += 3;
        
        Two cases:
        1. Regular assignment (x = value)
           - Simply: x = value
        
        2. Compound assignment (x += value, x -= value, etc.)
           - Break into two TAC instructions:
             temp = x op value
             x = temp
           - This standardizes compound operators to basic three-address form
        
        3. Unary operators (++, --)
           - x++ becomes: temp = x + 1; x = temp
           - x-- becomes: temp = x - 1; x = temp
        """
        ident_node = self._find_token(node, "identifier")
        if not ident_node: return ""
        var_name = ident_node["value"]
        
        assign_val = self._find_child(node, "assignment_value")
        unary_op = self._find_child(node, "unary_op")
        
        if assign_val:
            op_node = self._find_child(assign_val, "assignment_op")
            op = self.visit(op_node).strip() if op_node else "="
            val_node = self._find_child(assign_val, "value")
            val_temp = self.visit(val_node)
            
            if op == "=":
                self.emit(f"{var_name} = {val_temp}")
            else:
                base_op = op[0] # e.g., '+=' becomes '+'
                temp = self.new_temp()
                self.emit(f"{temp} = {var_name} {base_op} {val_temp}")
                self.emit(f"{var_name} = {temp}")
                
        elif unary_op:
            op_token = self._find_token(unary_op)
            if op_token:
                temp = self.new_temp()
                op = "+" if op_token["value"] == "++" else "-"
                self.emit(f"{temp} = {var_name} {op} 1")
                self.emit(f"{var_name} = {temp}")
        return ""

    def visit_output_statement(self, node):
        """
        Handle output statements: nova() for line output, lumen() for no newline.
        
        TAC representation uses a parameter stack:
        1. Push the value onto the parameter stack with 'param'
        2. Call the appropriate output function (nova or lumen)
        
        Example:
            nova("Hello");
        Becomes:
            param "Hello"
            call nova, 1
        
        The "1" means 1 parameter.
        """
        out_type_node = self._find_child(node, "output_type")
        out_type = self.visit(out_type_node).strip() if out_type_node else "nova"
        
        arg = self._find_child(node, "output_arg")
        arg_temp = self.visit(arg)
        
        self.emit(f"param {arg_temp}")
        # Distinguish between nova (newline) and lumen (no newline)
        if out_type == "lumen":
            self.emit("call lumen, 1")
        else:
            self.emit("call nova, 1")
        return ""

    def visit_value(self, node):
        """
        Handle a value (literal, variable, function call, or input).
        
        Special case: lumina() for input
        - Emits a call to the input function
        - Returns the temporary variable holding the result
        
        Regular case:
        - Returns the value as-is (token value or expression result)
        """
        if self._has_token(node, "lumina"):
            temp = self.new_temp()
            self.emit(f"{temp} = call input, 0")
            return temp
            
        # If it's a simple value, generic_visit will find the token and return it
        val = self.generic_visit(node)
        return val

    # --- Control Flow ---

    def visit_conditional_statement(self, node, end_label=None):
        """
        Handle if/else statements with TAC labels and conditional jumps.
        
        The key insight: conditionals in TAC use labels to jump over code sections.
        
        Structure in TAC:
            1. Evaluate condition -> conditional_temp
            2. ifFalse conditional_temp goto false_label
            3. <emit true branch code>
            4. goto end_label
            5. false_label:
            6. <emit else branch code>
            7. end_label:
        
        Example Soluna code:
            selene (x > 5) {
                nova("big");
            } flux {
                nova("small");
            }
        
        TAC output:
            t0 = x > 5
            ifFalse t0 goto L2
            param "big"
            call nova, 1
            goto L3
            L2:
            param "small"
            call nova, 1
            L3:
        
        Args:
            node: AST node for the conditional
            end_label: Optional label to jump to (used when nested in loops)
        """
        cond_node = self._find_child(node, "conditions")
        cond_temp = self.visit(cond_node)
        
        l_false = self.new_label()
        l_end = end_label or self.new_label()
        
        self.emit(f"ifFalse {cond_temp} goto {l_false}")
        
        statements = self._find_child(node, "statements") or self._find_child(node, "loop_statements")
        if statements: self.visit(statements)
        self.emit(f"goto {l_end}")
        
        self.emit(f"{l_false}:")
        
        tail = self._find_child(node, "conditional_tail") or self._find_child(node, "conditional_tail_in_loop")
        if tail:
            self.visit(tail, end_label=l_end)
            
        if not end_label:
            self.emit(f"{l_end}:")
        return ""

    def visit_conditional_statement_in_loop(self, node):
        """Wrapper for conditional statements inside loops - uses same logic as regular conditionals."""
        return self.visit_conditional_statement(node)

    def visit_ifelse(self, node, end_label=None):
        """Wrapper for if-else statements - delegates to visit_conditional_statement."""
        return self.visit_conditional_statement(node, end_label=end_label)

    def visit_ifelse_in_loop(self, node, end_label=None):
        """Wrapper for if-else statements inside loops."""
        return self.visit_ifelse(node, end_label=end_label)

    def visit_else(self, node, end_label=None):
        """
        Handle else block in a conditional.
        
        Simply processes the statements in the else block.
        The control flow (labels, jumps) is handled by visit_conditional_statement.
        """
        statements = self._find_child(node, "statements") or self._find_child(node, "loop_statements")
        if statements: self.visit(statements)
        return ""

    def visit_else_in_loop(self, node, end_label=None):
        """Wrapper for else blocks inside loops."""
        return self.visit_else(node, end_label=end_label)

    def visit_loop_while_statement(self, node):
        """
        Handle while loops with TAC labels and conditional jumps.
        
        The key insight: loops use labels for both the start (to jump back) and end (to jump out).
        
        Structure in TAC:
            1. loop_start:
            2. Evaluate condition -> conditional_temp
            3. ifFalse conditional_temp goto loop_end
            4. <emit loop body code>
            5. goto loop_start
            6. loop_end:
        
        This creates an infinite jump pattern until the condition becomes false.
        
        Example Soluna code:
            blaze (x < 10) {
                nova(x);
                x++;
            }
        
        TAC output:
            L0:
            t0 = x < 10
            ifFalse t0 goto L1
            param x
            call nova, 1
            t1 = x + 1
            x = t1
            goto L0
            L1:
        
        The loop is essentially:
        - Jump to L0
        - At L0: Check if x < 10
        - If false (x >= 10), jump to L1 (exit)
        - Otherwise, run loop body
        - Jump back to L0
        - At L1: Continue after loop
        """
        l_start = self.new_label()
        l_end = self.new_label()
        
        self.emit(f"{l_start}:")
        cond_node = self._find_child(node, "conditions")
        cond_temp = self.visit(cond_node)
        
        self.emit(f"ifFalse {cond_temp} goto {l_end}")
        
        statements = self._find_child(node, "loop_statements")
        if statements: self.visit(statements)
        
        self.emit(f"goto {l_start}")
        self.emit(f"{l_end}:")
        return ""

    def visit_loop_for_statement(self, node):
        """
        Handle for loops with initialization, condition, and increment.
        
        For loops combine three elements into one control structure:
        1. Initialize the loop variable
        2. Check the condition
        3. Increment after each iteration
        
        Structure in TAC:
            1. <emit initialization code: i = 0>
            2. loop_start:
            3. Evaluate condition -> conditional_temp
            4. ifFalse conditional_temp goto loop_end
            5. <emit loop body code>
            6. <emit increment code: i = i + 1>
            7. goto loop_start
            8. loop_end:
        
        Example Soluna code:
            lani (kai i = 0; i < 5; i++) {
                nova(i);
            }
        
        TAC output:
            i = 0              <- initialization
            L0:                <- loop start
            t0 = i < 5         <- condition check
            ifFalse t0 goto L1 <- exit if false
            param i            <- loop body
            call nova, 1
            t1 = i + 1         <- increment
            i = t1
            goto L0            <- back to loop start
            L1:                <- loop end
        
        This is equivalent to a while loop with init before and incr at the end.
        """
        params = self._find_child(node, "for_loop_params")
        if not params: return ""
        
        start_node = self._find_child(params, "for_start")
        limit_node = self._find_child(params, "for_limit")
        step_node = self._find_child(params, "for_step")
        
        ident = self._find_token(start_node, "identifier")
        var_name = ident["value"] if ident else "i"
        
        start_factor = self._find_child(start_node, "expr_factor")
        start_val = self.visit(start_factor) if start_factor else "0"
        self.emit(f"{var_name} = {start_val}")
        
        limit_factor = self._find_child(limit_node, "expr_factor")
        limit_val = self.visit(limit_factor) if limit_factor else "0"
        
        step_factor = self._find_child(step_node, "expr_factor")
        step_val = self.visit(step_factor) if step_factor else "1"

        l_start = self.new_label()
        l_end = self.new_label()
        
        self.emit(f"{l_start}:")
        
        cond_temp = self.new_temp()
        self.emit(f"{cond_temp} = {var_name} < {limit_val}") # Assumes standard counting up
        self.emit(f"ifFalse {cond_temp} goto {l_end}")
        
        statements = self._find_child(node, "loop_statements")
        if statements: self.visit(statements)
            
        step_temp = self.new_temp()
        self.emit(f"{step_temp} = {var_name} + {step_val}")
        self.emit(f"{var_name} = {step_temp}")
        self.emit(f"goto {l_start}")
        
        self.emit(f"{l_end}:")
        return ""

    # --- Functions ---

    def visit_func_def(self, node):
        """
        Handle function definition: func_name(params) { statements }
        
        TAC representation of functions:
        Functions in TAC include a declaration header and body, similar to assembly:
        
        Structure:
            1. func name(param1, param2, ...):
            2. <emit function body instructions>
            3. endfunc
        
        Example Soluna code:
            flux greet(flux name) {
                nova(name);
            }
        
        TAC output:
            func greet(name):
            param name           <- parameters available in function scope
            call nova, 1
            endfunc
        
        The function parameters are added to the symbol table so they can be 
        referenced in the function body.
        """
        ident_node = self._find_token(node, "identifier")
        if not ident_node: return ""
        func_name = ident_node["value"]
        
        # Extract parameters
        params_node = self._find_child(node, "func_params")
        params = []
        if params_node:
            self._collect_params(params_node, params)
        
        # Emit function header with parameters
        params_str = ", ".join([p["name"] for p in params]) if params else ""
        self.emit(f"func {func_name}({params_str}):")
        
        # Process function body
        statements = self._find_child(node, "statements")
        if statements: self.visit(statements)
            
        self.emit(f"endfunc")
        return ""

    def _collect_params(self, node, param_list):
        """
        Recursively collect function parameters from the parse tree.
        
        Parameters are stored as dictionaries with 'name' and 'type' keys:
        [{"name": "x", "type": "kai"}, {"name": "y", "type": "flux"}, ...]
        
        This allows TAC generation to understand parameter types when needed.
        """
        if not node: return
        param_node = self._find_child(node, "param")
        if param_node:
            type_node = self._find_child(param_node, "data_type")
            p_type = self._extract_type_name(type_node)
            ident = self._find_token(param_node, "identifier")
            if ident:
                param_list.append({
                    "name": ident["value"],
                    "type": p_type
                })
        tail = self._find_child(node, "param_tail")
        if tail:
            self._collect_params(tail, param_list)

    def _extract_type_name(self, type_node):
        """
        Extract type name from a data_type node.
        
        Example:
        - If type_node contains "kai", returns "kai"
        - If type_node contains "flux", returns "flux"
        - If type_node is None, returns "void"
        
        Used when parsing function parameters to preserve type information.
        """
        if not type_node: return 'void'
        token = self._find_token_in_tree(type_node)
        return token["token_type"] if token else "unknown"


    def _find_token_in_tree(self, node):
        """
        Recursively search for the first TOKEN in a tree (depth-first search).
        
        Used to find type keywords (kai, flux, let, etc.) nested in AST nodes.
        Unlike _find_token which only looks at direct children, this searches
        through the entire subtree.
        
        Example: If node is a complex data_type structure with nested children,
        this finds the first actual token (keyword) anywhere in that structure.
        
        Args:
            node: AST node to search
        
        Returns:
            The first TOKEN node found, or None if no tokens exist
        """
        if not node: return None
        if node.get("type") == "TOKEN": return node
        if "children" in node:
            for child in node["children"]:
                if child:
                    res = self._find_token_in_tree(child)
                    if res: return res
        return None

    def visit_func_call(self, node):
        """
        Handle function calls: func_name(arg1, arg2, ...)
        
        Function calls in TAC follow the parameter-stack calling convention:
        1. Push each argument onto the parameter stack with 'param'
        2. Call the function with 'call func_name, argcount'
        3. The result (if any) goes into a temporary variable
        
        Structure in TAC:
            param arg1
            param arg2
            param arg3
            result_temp = call func_name, 3
        
        Example Soluna code:
            kai sum = add(5, 3);
        
        TAC output:
            param 5
            param 3
            t0 = call add, 2
            sum = t0
        
        The 'result_temp' captures the function's return value.
        If the function returns nothing (void), the temp is still created
        but the return value is ignored.
        """
        ident = self._find_token(node, "identifier")
        func_name = ident["value"] if ident else ""
        
        args_node = self._find_child(node, "func_call_args")
        args_list = []
        
        if args_node:
            first_arg = self.visit(self._find_child(args_node, "expression"))
            if first_arg: args_list.append(first_arg)
                
            tail = self._find_child(args_node, "func_call_args_tail")
            if tail:
                # Assuming visit_func_call_args_tail is implemented to return a list of temps
                args_list.extend(self.visit_func_call_args_tail(tail))
                
        for arg in args_list:
            self.emit(f"param {arg}")
            
        temp = self.new_temp()
        self.emit(f"{temp} = call {func_name}, {len(args_list)}")
        return temp

    def visit_func_call_in_expr(self, node):
        """Wrapper for function calls in expressions - uses same logic as regular function calls."""
        return self.visit_func_call(node)

    def visit_func_call_args_tail(self, node):
        """
        Helper method to extract additional function call arguments after the first one.
        
        Returns a list of temporary variables holding the argument values.
        """
        args = []
        for child in node.get("children", []):
            if child.get("type") == "expression":
                args.append(self.visit(child))
        return args

    def visit_func_return(self, node):
        """
        Handle function returns: return value; or return;
        
        TAC representation:
        - If there's a value, emit: return value_temp
        - If no value (void return), emit: return
        
        The return instruction exits the function and passes control back to the caller.
        
        Example Soluna code:
            flux double(kai x) {
                kai result = x * 2;
                return result;
            }
        
        TAC output:
            func double(x):
            result = x * 2
            return result
            endfunc
        
        When calling: t0 = call double, 1
        The t0 receives the returned value from the function.
        """
        val_node = self._find_child(node, "return_val")
        val_temp = self.visit(val_node)
        if val_temp:
            self.emit(f"return {val_temp}")
        else:
            self.emit("return")
        return ""

    def visit_table_dec(self, node):
        """
        Handle table (array) declaration: hubble type name = {elem1, elem2, ...}
        
        Arrays in TAC are created with 'newarray' and initialized element-by-element.
        
        Structure in TAC:
            1. arr_temp = newarray
            2. temp1 = arr_temp[0]
            3. temp1 = value1
            4. temp2 = arr_temp[1]
            5. temp2 = value2
            6. ... (repeat for each element)
            7. array_name = arr_temp
        
        Example Soluna code:
            hubble kai numbers = {10, 20, 30};
        
        TAC output:
            t0 = newarray
            t1 = t0[0]
            t1 = 10
            t2 = t0[1]
            t2 = 20
            t3 = t0[2]
            t3 = 30
            numbers = t0
        
        This approach uses temporaries to track array elements and initializes them
        in a sequence that a simple interpreter can handle.
        """
        ident = self._find_token(node, "identifier")
        if not ident: return ""
        var_name = ident["value"]
        
        # Create array temporary
        arr_temp = self.new_temp()
        self.emit(f"{arr_temp} = newarray")
        
        # Collect and initialize elements
        elems_node = self._find_child(node, "hubble_elements")
        if elems_node:
            self._emit_array_elements(arr_temp, elems_node, 0)
        
        tail_node = self._find_child(node, "hubble_element_tail")
        if tail_node:
            elem_count = self._count_elements(elems_node) if elems_node else 0
            self._emit_array_elements(arr_temp, tail_node, elem_count)
        
        # Assign array to variable
        self.emit(f"{var_name} = {arr_temp}")
        return ""

    def _emit_array_elements(self, arr_temp, node, start_idx):
        """
        Emit TAC instructions for initializing array elements.
        
        For each element in the array:
        1. Get the element from the array at the current index
        2. Assign the value to that element
        3. Increment the index and recurse
        
        This is done recursively to handle nested array declarations.
        """
        if not node: return
        
        if node.get("type") in ["hubble_elements", "hubble_element_tail"]:
            expr_node = self._find_child(node, "expression")
            if expr_node:
                val_temp = self.visit(expr_node)
                idx_temp = self.new_temp()
                self.emit(f"{idx_temp} = {arr_temp}[{start_idx}]")
                self.emit(f"{idx_temp} = {val_temp}")
                start_idx += 1
        
        # Process next elements recursively
        if "children" in node:
            for child in node["children"]:
                if child and child.get("type") in ["hubble_elements", "hubble_element_tail"]:
                    self._emit_array_elements(arr_temp, child, start_idx)

    def _count_elements(self, node):
        """
        Count the number of elements in a hubble_elements node.
        
        This is used to track the current index when initializing arrays,
        so we can append new elements at the correct position.
        
        Example: For {10, 20, 30}, after processing the first 2 elements,
        we know the next element should go at index 2.
        """
        if not node: return 0
        count = 0
        if node.get("type") == "hubble_elements":
            if self._find_child(node, "expression"):
                count = 1
        if "children" in node:
            for child in node["children"]:
                if child and child.get("type") == "hubble_element_tail":
                    count += self._count_elements(child)
        return count

    def visit_table_nav(self, node):
        """
        Handle table access and assignment: arr[idx], arr[idx] = value
        
        Two cases:
        
        1. Reading from array:
           arr[0] returns the value at index 0
           TAC: temp = arr[0]
        
        2. Assigning to array:
           arr[0] = value assigns the value to index 0
           TAC: arr[0] = value
        
        Example Soluna code:
            hubble kai numbers = {10, 20, 30};
            kai first = numbers[0];  <- Read
            numbers[1] = 25;         <- Write
        
        TAC output:
            t0 = newarray
            ... (initialize array)
            numbers = t0
            t1 = numbers[0]
            first = t1
            numbers[1] = 25
        """
        ident = self._find_token(node, "identifier")
        if not ident: return ""
        var_name = ident["value"]
        
        # Get index
        idx_node = self._find_child(node, "table_index")
        if idx_node:
            idx_val_node = self._find_child(idx_node, "index_val")
            idx_val = self.visit(idx_val_node) if idx_val_node else "0"
            
            # Check if this is an assignment
            if self._has_token(node, "="):
                expr_node = self._find_child(node, "expression")
                if expr_node:
                    val_temp = self.visit(expr_node)
                    self.emit(f"{var_name}[{idx_val}] = {val_temp}")
            else:
                # Just a read access - return temporary with the value
                result_temp = self.new_temp()
                self.emit(f"{result_temp} = {var_name}[{idx_val}]")
                return result_temp
        return ""

    def visit_string_or_table_len(self, node):
        """
        Handle len() function: returns length of string or table.
        
        TAC representation:
            temp = len(array_or_string)
        
        Returns a temporary variable holding the length, which can then be
        used in expressions or assignments.
        
        Example Soluna code:
            kai length = len("hello");
            kai arr_size = len(numbers);
        
        TAC output:
            t0 = len("hello")
            length = t0
            t1 = len(numbers)
            arr_size = t1
        """
        ident = self._find_token(node, "identifier")
        if ident:
            temp = self.new_temp()
            self.emit(f"{temp} = len({ident['value']})")
            return temp
        return ""

    # --- Helpers ---
    
    def _find_child(self, node, type_name):
        """
        Find the first child node of a given type.
        
        Used to navigate the parse tree and extract specific components.
        
        Example: _find_child(node, "identifier") finds the first identifier token
        
        Args:
            node: AST node to search in
            type_name: Type of child to find (e.g., "identifier", "expression")
        
        Returns:
            The first child node with matching type, or None if not found
        """
        if not node or "children" not in node: return None
        for child in node.get("children", []):
            if child and child.get("type") == type_name: return child
        return None

    def _find_token(self, node, token_type=None):
        """
        Find a token in a node's children.
        
        Tokens are leaf nodes in the parse tree (variable names, operators, etc.).
        
        Example: _find_token(node, "identifier") finds an identifier token like "x"
        
        Args:
            node: AST node to search in
            token_type: Optional token type to filter by
        
        Returns:
            The first token matching the criteria, or None if not found
        """
        if not node or "children" not in node: return None
        for child in node.get("children", []):
            if child and child.get("type") == "TOKEN":
                if not token_type or child.get("token_type") == token_type:
                    return child
        return None

    def _has_token(self, node, value):
        """
        Check if a node contains a token with a specific value.
        
        Useful for checking for operators like "=" or keywords like "hubble".
        
        Args:
            node: AST node to search in
            value: Token value to look for (e.g., "=", "+", "kai")
        
        Returns:
            True if the token is found, False otherwise
        """
        if not node or "children" not in node: return False
        for child in node.get("children", []):
            if child and child.get("type") == "TOKEN" and child.get("value") == value:
                return True
        return False