from .symbol_table import SymbolTable
from .errors import SemanticError

class SemanticAnalyzer:
    """
    SEMANTIC ANALYZER: Checking if Code Makes Sense
    
    The parser built a parse tree showing the STRUCTURE of the code.
    The semantic analyzer checks if the code is MEANINGFUL:
    
    - Do all variables exist before being used?
    - Are variable types correct? (can't assign string to integer)
    - Are functions defined before being called?
    - Are break statements only in loops?
    - Are all declared variables actually used?
    - Do function calls have the right number of arguments?
    
    WORKFLOW:
    1. Pre-pass: Find all function declarations first
       (So functions can call other functions defined later)
    2. Main pass: Visit each node in the parse tree
       (Validate variables, types, statements, etc.)
    3. Check unused: Report warnings for unused variables
    
    The analyzer uses a symbol table to track what's been declared and what types they are.
    """
    
    def __init__(self):
        """Initialize the semantic analyzer with empty symbol table and no context."""
        # The symbol table tracks all declared variables and functions
        self.symbols = SymbolTable()
        # List of warning messages (unused variables, type mismatches, etc.)
        self.warnings = []
        # When inside a function, what type should it return? (None if not in function)
        self.current_return_type = None
        # Flag to know if we're in a 'local' declaration (vs global)
        self.is_inside_local_decl = False

    def analyze(self, tree):
        """
        Main entry point: Analyze the entire parse tree.
        
        Args:
            tree: The parse tree produced by the parser
        
        Raises:
            SemanticError if any semantic problems are found
        """
        # Reset state (fresh analysis)
        self.symbols = SymbolTable()
        self.warnings = []
        self.current_return_type = None
        self.is_inside_local_decl = False
        
        # STEP 1: Pre-pass - declare all functions first
        # This allows functions to reference other functions defined later in the file
        self._declare_all_functions(tree)
        
        # STEP 2: Main pass - visit the entire tree to validate everything
        if tree:
            self.visit(tree)
            
        # STEP 3: Post-pass - check for unused global variables
        self._check_unused(self.symbols.scopes[0])

    def visit(self, node):
        """
        Universal visitor: Dispatch to the right visit method based on node type.
        
        This is a design pattern called "Visitor Pattern" - instead of one big 
        if/else block, we have separate methods for each node type (visit_statement, 
        visit_expression, etc).
        
        Args:
            node: A tree node (dictionary with "type" and "children")
        
        Returns:
            Result of the appropriate visit method
        """
        if not node: return None
        # Get the node type (e.g., "statement", "expression", "var_dec")
        node_type = node.get("type")
        # Build method name: "visit_statement", "visit_expression", etc.
        method_name = f"visit_{node_type}" if node_type else "generic_visit"
        
        # Get the method (or use generic_visit if no specific method exists)
        visitor = getattr(self, method_name, self.generic_visit)
        # Call the method with the node
        return visitor(node)

    def generic_visit(self, node):
        """
        Default visitor for nodes that don't have a specific visit method.
        
        Just recursively visit all children (traverse the tree).
        """
        if not node: return
        if "children" in node:
            for child in node["children"]:
                if child: self.visit(child)

    def _declare_all_functions(self, node):
        """
        Pre-pass: Find all function declarations and add them to the symbol table.
        
        This is called BEFORE the main analysis pass.
        It allows functions to be mutually recursive (function A calls B, B calls A).
        
        Without this pre-pass, if function B is defined after A, then A couldn't 
        call B (it wouldn't exist yet). With the pre-pass, both are declared first.
        
        Args:
            node: A tree node to search recursively
        """
        if not node: return
        
        # Check if this node is a function declaration
        if node.get("type") == "func_dec":
            func_def = self._find_child(node, "func_def")
            if func_def:
                # Extract function info
                func_type_node = self._find_child(func_def, "func_data_type")
                return_type = self._extract_type_name(func_type_node)
                
                func_name_token = self._find_token(func_def, "identifier")
                
                # Collect parameter types
                params = []
                func_params_node = self._find_child(func_def, "func_params")
                if func_params_node:
                    self._collect_params(func_params_node, params)
                
                if func_name_token:
                    func_name = func_name_token["value"]
                    param_types = [p["type"] for p in params]
                    
                    # Check for redeclaration
                    if self.symbols.lookup(func_name):
                        raise SemanticError(f"Function '{func_name}' is already declared.", func_name_token["line"], func_name_token["col"])
                    
                    # Declare the function in the symbol table
                    self.symbols.declare(func_name, {
                        "category": "function",
                        "return_type": return_type,
                        "params": param_types
                    }, func_name_token["line"], func_name_token["col"], is_local=False)

        # Recursively search children for more function declarations
        if "children" in node:
            for child in node["children"]:
                self._declare_all_functions(child)

    # ==========================================
    # 1. IDENTIFIERS & VARIABLES
    # ==========================================
    
    def visit_local_dec(self, node):
        """
        Rule: local_dec -> 'local' dec_and_init
        This wrapper tells us the inner declaration is LOCAL.
        """
        self.is_inside_local_decl = True
        self.generic_visit(node)
        self.is_inside_local_decl = False

    def visit_var_dec(self, node):
        is_local = self.is_inside_local_decl or self.symbols.current_scope_level > 0
        
        is_const = self._has_token_recursive(node, "zeta")
        
        type_node = self._find_child(node, "data_type")
        declared_type = self._extract_type_name(type_node)

        init_node = self._find_child(node, "var_init")
        if init_node:
            self._process_variable_initialization(init_node, declared_type, is_const, is_local)

    def _process_variable_initialization(self, node, declared_type, is_const, is_local):
        identifiers = []
        first_ident = self._find_token(node, "identifier")
        if first_ident: identifiers.append(first_ident)
        
        multi_node = self._find_child(node, "multi_identifiers")
        self._collect_identifiers(multi_node, identifiers)

        values = []
        value_init_node = self._find_child(node, "value_init")
        self._collect_values(value_init_node, values)

        if values and len(values) > len(identifiers):
            err_line = identifiers[0]["line"] if identifiers else 0
            err_col = identifiers[0]["col"] if identifiers else 0
            raise SemanticError(f"Too many values ({len(values)}) for the number of variables ({len(identifiers)}).", err_line, err_col)

        for i, ident_token in enumerate(identifiers):
            var_name = ident_token["value"]
            line, col = ident_token["line"], ident_token["col"]

            val_node = values[i] if i < len(values) else None
            final_type = declared_type
            
            is_lumina = val_node and val_node.get("type") == "value" and self._has_token(val_node, "lumina")
            static_val = None

            if is_const and is_lumina:
                raise SemanticError(f"Constant variable '{var_name}' cannot be initialized with runtime input 'lumina()'.", line, col)

            if declared_type == 'let':
                if val_node:
                    if is_lumina:
                        final_type = 'let'
                    else:
                        final_type = self._get_expression_type(val_node)
                        static_val = self._evaluate_static_string(val_node)
                        if final_type == 'unknown': final_type = 'zeru' 
                else:
                    final_type = 'zeru'
            elif val_node and not is_lumina:
                expr_type = self._get_expression_type(val_node)
                static_val = self._evaluate_static_string(val_node)
                if not self._check_coercion(declared_type, expr_type, val_node):
                     raise SemanticError(f"Type Mismatch: Cannot assign '{expr_type}' to '{declared_type}'.", line, col)

            self.symbols.declare(var_name, {
                "category": "variable",
                "type": final_type,
                "is_const": is_const,
                "static_value": static_val,
                "is_initialized": val_node is not None or is_lumina # NEW
            }, line, col, is_local=is_local)

    # ==========================================
    # 2. TYPE COERCION: Checking Type Compatibility
    # ==========================================
    # Type coercion determines if one type can be assigned to another.
    # Example: Can you assign a 'kai' (int) to a 'flux' (float)? Yes!
    #          Can you assign a 'let' (string) to a 'kai' (int)? No!
    # 
    # This section defines the coercion rules for Soluna types.
    
    def _check_coercion(self, target, source, expr_node=None):
        """
        Check if a value of 'source' type can be assigned to 'target' type.
        
        COERCION RULES:
        - 'let' (string) is flexible: accepts any type
        - Same types are always compatible
        - 'zeru' (unknown) is assumed compatible for inference
        - 'selene' (double) → 'kai'/'flux' requires static value check
        - 'kai' (int) can become 'flux'/'lani', or vice versa
        - 'lani' (bool) is flexible
        
        Args:
            target: The type we're assigning TO (e.g., "kai")
            source: The type we're assigning FROM (e.g., "flux")
            expr_node: Optional - the actual expression for static value checking
        
        Returns:
            True if coercion is allowed, False otherwise
        """
        # Rule 1: String type is flexible, same types are ok, unknown is ok
        if target == 'let' or target == source or source == 'zeru': 
            return True

        # Rule 2: Narrowing from double requires static value check
        # (Can't safely narrow double to int/float at runtime)
        if target in ['kai', 'flux'] and source == 'selene':
            if expr_node:
                val_str = self._evaluate_static_string(expr_node)
                if val_str is not None:
                    try:
                        if target == 'kai':
                            int(val_str)
                        elif target == 'flux':
                            float(val_str)
                        return True
                    except ValueError:
                        return False
            return False

        # Rule 3: Int and Float are interchangeable
        if target == 'kai' and source in ['flux', 'lani']: 
            return True
        if target == 'flux' and source in ['kai', 'lani']: 
            return True
        # Rule 4: Bool is flexible
        if target == 'lani': 
            return True 
        # No other coercions allowed
        return False

    # ==========================================
    # 3. STATEMENTS: Handling code blocks and control flow
    # ==========================================
    # This section validates statements (assignments, conditionals, loops, etc.)
    # Key checks:
    # - Variables exist before use
    # - Types match in assignments
    # - Break statements are only in loops
    # - Function returns match return type
    
    def visit_assignment_statement(self, node):
        """
        Handle assignment: x = 5; or arr[0] = x + 1;
        
        For table assignments (arr[0] = ...):
        - Look up the variable
        - Get the type from the right side
        - Check type compatibility
        
        For regular assignments (x = ...):
        - Check variable exists
        - Check it's not const
        - Validate type match
        """
        # Check if this is a table assignment (arr[0] = value)
        table_nav = self._find_child(node, "table_nav")
        if table_nav:
            self.visit_table_nav(table_nav)
            assign_val = self._find_child(node, "assignment_value")
            if assign_val:
                val_wrapper = self._find_child(assign_val, "value") 
                if val_wrapper and not self._has_token(val_wrapper, "lumina"):
                    val_node = self._find_child(val_wrapper, "expression")
                    if val_node:
                        self._get_expression_type(val_node)
            return

        # Regular variable assignment (x = value)
        ident_token = self._find_token(node, "identifier")
        if ident_token:
            var_name = ident_token["value"]
            line, col = ident_token["line"], ident_token["col"]

            # Look up the variable in symbol table
            symbol = self.symbols.lookup(var_name)
            if not symbol:
                raise SemanticError(f"Variable '{var_name}' not declared.", line, col)
            # Can't reassign const variables
            if symbol.get("is_const"):
                raise SemanticError(f"Cannot reassign constant variable '{var_name}'.", line, col)
            
            # Mark variable as now initialized (has been assigned a value)
            symbol["is_initialized"] = True

            # Check type compatibility of assigned value
            assign_val = self._find_child(node, "assignment_value")
            val_wrapper = self._find_child(assign_val, "value") 
            
            if val_wrapper and not self._has_token(val_wrapper, "lumina"):
                val_node = self._find_child(val_wrapper, "expression")
                if val_node:
                    expr_type = self._get_expression_type(val_node)
                    # Verify the assigned type can be coerced to the variable type
                    if not self._check_coercion(symbol["type"], expr_type, val_node):
                        raise SemanticError(f"Type Mismatch: Cannot assign '{expr_type}' to '{symbol['type']}'.", line, col)
                    symbol["static_value"] = self._evaluate_static_string(val_node)

    def visit_statements(self, node):
        """
        Handle a block of statements.
        
        Just recursively visit all children (statements are processed in order).
        """
        self.generic_visit(node)

    def visit_conditional_statement(self, node):
        """
        Handle if-else statements: sol ... mos soluna ... mos luna ... mos
        
        Important: We scope each if/else block separately so variables declared
        in the if block don't leak to the else block.
        
        Example:
            sol x > 0 cos
                kai y = 5;  (y is local to this block)
            mos
            luna cos
                kai y = 10; (different y, local to this block)
            mos
            // y is not accessible here
        """
        if not node or "children" not in node: 
            return

        # Check condition doesn't end with semicolon (common syntax error)
        statements_node = self._find_child(node, "statements")
        self._check_no_starting_semicolon(statements_node, "Condition cannot be followed by a semicolon.")

        for child in node["children"]:
            if not child: 
                continue
            
            # When we encounter a 'statements' block, scope it
            # The grammar structures this as: sol -> conditions -> statements -> mos
            if child.get("type") == "statements":
                self.symbols.enter_scope()
                self.visit(child)
                popped = self.symbols.exit_scope()
                self._check_unused(popped)
            else:
                self.visit(child)

    def visit_conditions(self, node):
        """
        Handle condition expressions (in if, while, etc.)
        
        Validates that:
        - Conditions don't have semicolons (common error)
        - Expression types are valid (resolving variable types)
        """
        if not node: 
            return

        # Check for common mistake: semicolon in condition
        tokens = self._get_all_tokens(node)
        for t in tokens:
            if t.get("value") == ";":
                raise SemanticError("Conditions cannot contain a semicolon.", t.get("line", 0), t.get("col", 0))
        
        # Check if the condition directly contains an expression
        expr_node = self._find_child(node, "expression")
        if expr_node:
            # Validate the expression's type
            self._get_expression_type(expr_node)
        else:
            # If it is a nested condition like ( conditions ), keep traversing
            self.generic_visit(node)

    def visit_loop_repeat_until_statement(self, node):
        """
        Handle repeat-until loop: wax ... wane condition
        
        This is a do-while loop (executes body at least once).
        Scopes the loop body so loop variables don't leak out.
        Tracks that we're inside a loop (validates 'break' statements).
        """
        # Mark: we're entering a loop
        self.symbols.enter_loop()
        # Mark: create new scope for loop variables
        self.symbols.enter_scope()
        # Visit the loop body
        self.generic_visit(node)
        # Check for unused variables in loop scope
        popped = self.symbols.exit_scope()
        self._check_unused(popped)
        # Mark: we're exiting the loop
        self.symbols.exit_loop()

    def visit_loop_while_statement(self, node):
        """
        Handle while loop: orbit condition cos ... mos
        
        Scopes the loop body and tracks loop context.
        """
        self.symbols.enter_loop()
        self.symbols.enter_scope()
        self.generic_visit(node)
        popped = self.symbols.exit_scope()
        self._check_unused(popped)
        self.symbols.exit_loop()

    def visit_loop_for_statement(self, node):
        """
        Handle for loop: phase kai i = start, limit, step cos ... mos
        
        For loops have TWO scopes:
        1. Outer scope: For loop parameters (i variable)
        2. Inner scope: Loop body (can declare variables inside)
        
        Structure:
            phase kai i = 1, 10, 1 cos
                kai sum = 0;  // Inner scope
            mos
            // i and sum are not accessible here
        """
        # Mark: we're entering a loop
        self.symbols.enter_loop()
        # Scope 1: Parameters scope (where loop variable i lives)
        self.symbols.enter_scope()

        # Validate and declare the loop variable
        params_node = self._find_child(node, "for_loop_params")
        if params_node:
            # Start: Initialize loop variable (kai i = 1)
            for_start = self._find_child(params_node, "for_start")
            if for_start:
                self._validate_for_start(for_start)
            
            # Limit: Upper bound (i < 10 or i <= limit)
            # Must be an integer type
            for_limit = self._find_child(params_node, "for_limit")
            if for_limit:
                limit_expr = self._find_child(for_limit, "expr_factor")
                if limit_expr:
                    limit_type = self._get_expression_type(limit_expr)
                    if limit_type not in ['kai', 'unknown']:
                        raise SemanticError(f"For loop limit must evaluate to 'kai', got '{limit_type}'.", 0, 0)
            
            # Step: Increment amount (i += step)
            # Must be an integer type
            for_step = self._find_child(params_node, "for_step")
            if for_step:
                step_expr = self._find_child(for_step, "expr_factor")
                if step_expr:
                    step_type = self._get_expression_type(step_expr)
                    if step_type not in ['kai', 'unknown']:
                        raise SemanticError(f"For loop step must evaluate to 'kai', got '{step_type}'.", 0, 0)

        # Scope 2: Loop body scope (inner variables like sum)
        loop_statements = self._find_child(node, "loop_statements")
        if loop_statements:
            self.symbols.enter_scope()
            self.visit(loop_statements)
            popped_body = self.symbols.exit_scope()
            self._check_unused(popped_body)
        
        # Exit parameters scope
        popped_params = self.symbols.exit_scope()
        self._check_unused(popped_params)
        # Mark: exiting loop
        self.symbols.exit_loop()

    def _validate_for_start(self, for_start_node):
        """
        Validate the initialization part of a for loop: i = 1 or kai i = 1
        
        Case 1: kai i = 1      (new variable, must declare)
        Case 2: i = 1          (reuse existing variable, must exist)
        Case 3: i             (implicit initialization, variable must exist)
        """
        ident_token = self._find_token(for_start_node, "identifier")
        if not ident_token: 
            return
        
        var_name = ident_token["value"]
        line, col = ident_token["line"], ident_token["col"]

        # Check if this is a declaration (kai i = ...) or reuse
        is_declaration = self._has_token(for_start_node, "kai")
        has_assignment = self._has_token(for_start_node, "=")

        if is_declaration:
            # Case 1: kai i = 1 (new loop variable)
            expr_node = self._find_child(for_start_node, "expr_factor")
            if expr_node:
                expr_type = self._get_expression_type(expr_node)
                # Loop variables must be integers
                if expr_type not in ['kai', 'unknown']:
                    raise SemanticError(f"Type Mismatch in loop init: Cannot assign '{expr_type}' to 'kai'.", line, col)
            
            # Declare the loop variable (it's always local to the loop)
            self.symbols.declare(var_name, {
                "category": "variable",
                "type": "kai",
                "is_const": False,
                "is_initialized": True
            }, line, col, is_local=True)
            
        else:
            # Case 2 & 3: i = 1 OR i (reuse existing variable)
            # The variable must already exist
            sym = self.symbols.lookup(var_name)
            if not sym:
                raise SemanticError(f"Variable '{var_name}' not declared in for loop initialization.", line, col)
            
            # Loop variables must be integers
            if sym.get("type") != "kai":
                raise SemanticError(f"For loop variable '{var_name}' must be of type 'kai', but is '{sym.get('type')}'.", line, col)

            # If there's an assignment, validate the type
            if has_assignment:
                expr_node = self._find_child(for_start_node, "expr_factor")
                if expr_node:
                    expr_type = self._get_expression_type(expr_node)
                    if expr_type not in ['kai', 'unknown']:
                        raise SemanticError(f"Type Mismatch in loop init: Cannot assign '{expr_type}' to 'kai'.", line, col)

    def visit_break_statements(self, node):
        """
        Handle break statement: warp;
        
        Break can ONLY be used inside a loop (while, for, repeat-until).
        Using break outside a loop is a semantic error.
        """
        # Check: are we currently inside a loop?
        if not self.symbols.is_inside_loop():
             raise SemanticError("Statement 'warp' can only be used inside a loop.", 0, 0)

    # ==========================================
    # 4. FUNCTIONS: Handling function definitions and calls
    # ==========================================
    # This section validates function definitions, parameters, returns, and calls.
    # Key checks:
    # - Functions are declared before use (done in pre-pass)
    # - Parameters are properly typed
    # - Return statements match function return type
    # - Function calls have correct number and types of arguments
    
    def visit_func_dec(self, node):
        """
        Handle function declaration: kai func(kai x, flux y) cos ... mos
        
        Steps:
        1. Extract function signature (name, parameters, return type)
        2. Declare function (if not already done in pre-pass)
        3. Enter function scope
        4. Declare parameters as local variables
        5. Visit function body
        6. Check for unused variables in function
        """
        # Get the actual function definition
        func_def = self._find_child(node, "func_def")
        if not func_def:
            self.generic_visit(node)
            return
        
        # Check for syntax error: semicolon after function signature
        statements_node = self._find_child(func_def, "statements")
        self._check_no_starting_semicolon(statements_node, "Function definition cannot be followed by a semicolon.")

        # Extract function metadata
        func_type_node = self._find_child(func_def, "func_data_type")
        return_type = self._extract_type_name(func_type_node)
        
        func_name_token = self._find_token(func_def, "identifier")
        
        # Collect parameter information
        params = []
        func_params_node = self._find_child(func_def, "func_params")
        if func_params_node:
            self._collect_params(func_params_node, params)
        
        if func_name_token:
            func_name = func_name_token["value"]
            param_types = [p["type"] for p in params]
            
            # Function should already be declared from pre-pass, but double-check
            if not self.symbols.lookup(func_name):
                self.symbols.declare(func_name, {
                    "category": "function",
                    "return_type": return_type,
                    "params": param_types,
                    "is_initialized": True
                }, func_name_token["line"], func_name_token["col"], is_local=False)

        # Now enter function scope and analyze the body
        self.current_return_type = return_type  # Track return type for return statements
        self.symbols.enter_scope()  # New scope for function body
        
        # Declare parameters as local variables
        for p in params:
            self.symbols.declare(p["name"], {
                "category": "variable",
                "type": p["type"],
                "is_const": False,
                "is_initialized": True
            }, p["line"], p["col"], is_local=True)
        
        # Analyze function body
        statements = self._find_child(func_def, "statements")
        if statements:
            self.visit(statements)
        
        # Check for unused variables in function scope
        popped = self.symbols.exit_scope()
        self._check_unused(popped)
        # Clear return type (we're exiting function)
        self.current_return_type = None

        # Process any remaining siblings (for nested function declarations)
        for child in node.get("children", []):
            if child and child.get("type") != "func_def":
                self.visit(child)
                
    def visit_func_return(self, node):
        """
        Handle return statement: zara value;
        
        Validates that:
        - Return is inside a function (current_return_type is set)
        - Return value matches function's declared return type
        - Void functions don't return values
        - Non-void functions always return values
        """
        # Check: are we inside a function?
        if self.current_return_type is None:
            raise SemanticError("'zara' used outside of function.", 0, 0)

        # Check if return has a value
        expr_node = self._find_child(node, "return_val")
        has_value = self._find_child(expr_node, "expression") is not None
        
        # Void functions can't return values
        if self.current_return_type == 'void' and has_value:
             raise SemanticError("Void function cannot return a value.", 0, 0)
        
        # Non-void functions must return values
        if self.current_return_type != 'void' and not has_value:
             raise SemanticError(f"Function must return a value of type '{self.current_return_type}'.", 0, 0)

        if has_value:
            val_node = self._find_child(expr_node, "expression")
            val_type = self._get_expression_type(val_node)
            if not self._check_coercion(self.current_return_type, val_type, val_node):
                 raise SemanticError(f"Invalid return type. Expected '{self.current_return_type}', got '{val_type}'.", 0, 0)
    
    def _collect_params(self, node, param_list):
        """
        Recursively collect function parameters from the parse tree.
        
        Parameters can be declared as: func(kai x, flux y, let name)
        This method recursively walks through the parameter list and extracts:
        - Parameter name
        - Parameter type (kai, flux, let, etc.)
        - Line and column for error reporting
        
        The grammar for parameters is recursive:
            func_params -> param param_tail?
            param_tail -> COMMA param param_tail?
        
        So we recurse through param_tail to find all parameters.
        
        Args:
            node: A func_params node from the parse tree
            param_list: A list to append parameter dictionaries to
        
        Example:
            For function: kai add(kai x, flux y) cos ... mos
            param_list becomes: [
                {"name": "x", "type": "kai", "line": 5, "col": 10},
                {"name": "y", "type": "flux", "line": 5, "col": 18}
            ]
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
                    "type": p_type,
                    "line": ident["line"],
                    "col": ident["col"]
                })
        tail = self._find_child(node, "param_tail")
        if tail:
            self._collect_params(tail, param_list)

    def visit_func_call(self, node):
        """
        Validate a function call: func(arg1, arg2, ...)
        
        Steps:
        1. Extract function name from the parse tree
        2. Check if it's a built-in function (nova for output, lumen for input)
        3. Look up the function in the symbol table
        4. Collect all arguments
        5. Validate argument count matches parameter count
        6. Validate each argument's type matches the parameter type
        
        Example: If you call add(5, 3.5) where add(kai x, kai y)
        - Look up "add" in symbol table
        - Get expected params: [kai, kai]
        - Evaluate arg 1: 5 → kai ✓
        - Evaluate arg 2: 3.5 → flux, but expected kai
        - Check coercion: Can flux coerce to kai? Yes! ✓
        - If it couldn't coerce, raise SemanticError
        
        Args:
            node: A func_call node from the parse tree
        
        Raises:
            SemanticError if function doesn't exist, wrong arg count, or type mismatch
        """
        ident = self._find_token(node, "identifier")
        if ident:
            func_name = ident["value"]
            
            # Built-in check: nova (output) and lumen (input) are special
            if func_name in ["nova", "lumen"]:
                args_node = self._find_child(node, "func_call_args")
                args = []
                if args_node:
                    self._collect_args(args_node, args)
                for arg_expr in args:
                    self._get_expression_type(arg_expr)
                return
            
            # Look up the function in the symbol table
            sym = self.symbols.lookup(func_name)
            if not sym:
                raise SemanticError(f"Function '{func_name}' not declared.", ident["line"], ident["col"])
            
            # Make sure it's actually a function (not a variable with the same name)
            if sym.get("category") != "function":
                raise SemanticError(f"'{func_name}' is not callable.", ident["line"], ident["col"])
            
            # Collect all arguments
            args_node = self._find_child(node, "func_call_args")
            args = []
            if args_node:
                self._collect_args(args_node, args)
            
            # Get the expected parameter types from the function definition
            expected_params = sym.get("params", [])
            
            # Check argument count
            if len(args) != len(expected_params):
                raise SemanticError(f"Function '{func_name}' expects {len(expected_params)} arguments, got {len(args)}.", ident["line"], ident["col"])
            
            # Check each argument's type
            for i, arg_expr in enumerate(args):
                arg_type = self._get_expression_type(arg_expr)
                expected_type = expected_params[i]
                if not self._check_coercion(expected_type, arg_type, arg_expr):
                    raise SemanticError(f"Argument {i+1} of '{func_name}' expects '{expected_type}', got '{arg_type}'.", ident["line"], ident["col"])

    def visit_func_call_in_expr(self, node):
        """
        Handle a function call when it appears inside an expression.
        
        Function calls can appear in two contexts:
        1. As statements: nova("Hello");
        2. In expressions: kai x = add(5, 3);
        
        When a function call appears in an expression, we need to get its return type
        so we can validate the assignment or operation it's part of.
        
        Example:
            kai result = add(x, y);
            The result's type depends on add's return type.
        
        This method delegates to visit_func_call() which does all the validation.
        """
        self.visit_func_call(node)

    def _collect_args(self, node, arg_list):
        """
        Recursively collect function call arguments from the parse tree.
        
        Function calls can have multiple arguments: func(arg1, arg2, arg3)
        The grammar is recursive:
            func_call_args -> expression func_call_args_tail?
            func_call_args_tail -> COMMA expression func_call_args_tail?
        
        This method walks the tree and extracts each expression argument.
        
        Args:
            node: A func_call_args or func_call_args_tail node
            arg_list: A list to append expression nodes to
        
        Example:
            For call: add(5, x + 3, y)
            arg_list becomes: [<expr: 5>, <expr: x+3>, <expr: y>]
        """
        if not node: return
        expr_node = self._find_child(node, "expression")
        if expr_node:
            arg_list.append(expr_node)
        tail = self._find_child(node, "func_call_args_tail")
        if tail:
            self._collect_args(tail, arg_list)
            
    # ==========================================
    # 5. EXPRESSIONS & TABLES
    # ==========================================

    def _validate_expr_components(self, node):
        """
        Validate all components of an expression recursively.
        
        This method ensures that all parts of an expression are valid:
        - Function calls use correct argument types
        - Table accesses use correct index types
        - Variables are declared before use
        
        Steps:
        1. Check if this is a table access (arr[0])
        2. Check if this is a table assignment (arr[0] = value)
        3. Check if this is a function call
        4. Recursively check all children
        
        Example:
            In expression: arr[i] + func(x, y)
            - Validate arr is a table and i is initialized
            - Validate func exists and x, y types are correct
        
        Args:
            node: A parse tree node
        """
        if not node: return
        
        node_type = node.get("type")
        if node_type == "table_nav":
            self.visit_table_nav(node)

        if node_type == "factor_value":
            ident = self._find_token(node, "identifier")
            tail = self._find_child(node, "identifier_tail")
            if ident and tail and self._find_child(tail, "table_index"):
                sym = self.symbols.lookup(ident["value"])
                
                if not sym:
                    raise SemanticError(f"Variable '{ident['value']}' not declared.", ident["line"], ident["col"])
                
                # Check if it's a table (hubble)
                if sym.get("category") == "table":
                    sym["name"] = ident["value"] 
                    self._validate_table_indices(tail, sym)
                # Check if it's a string variable being indexed (allowed)
                elif sym.get("type") == "selene":
                    # String indexing is allowed and returns a character (blaze)
                    self._validate_string_indices(tail, sym)
                else:
                    raise SemanticError(f"Cannot index non-table, non-string variable '{ident['value']}'.", ident["line"], ident["col"])
            
        if node_type in ["func_call", "func_call_in_expr"]:
            self.visit_func_call(node)
            return
            
        if "children" in node:
            for child in node["children"]:
                self._validate_expr_components(child)
    
    def _get_expression_type(self, node):
        """
        Determine the type of an expression.
        
        This is a KEY method that figures out what type an expression evaluates to.
        Used in assignments, returns, function calls, and type checking.
        
        ALGORITHM:
        1. Collect all literal types in the expression (kai, flux, lani, selene)
        2. Check for special operators that change the type:
           - ".." (string concatenation) → selene (string)
           - Comparison operators (==, !=, <, >, <=, >=) → lani (bool)
        3. Determine the "highest" type (type hierarchy):
           - flux (float) > kai (int)
           - selene (double) > others
           - Other types as found
        4. Return that type
        
        Examples:
            5 + 3             → kai (integer literals)
            5.0 + 3           → flux (float+int = float)
            5 < 3             → lani (comparison = bool)
            "hello" .. x      → selene (string concat = string)
            func(5)           → depends on func's return type
        
        Args:
            node: An expression parse tree node
        
        Returns:
            A type string: 'kai', 'flux', 'selene', 'blaze', 'lani', 'let', 'zeru'
        """
        if not node: return 'zeru'

        # Pre-checks: validate division/modulo by zero and string math
        self._check_division_by_zero(node)
        self._check_string_math(node)
        # Validate components like function calls and table accesses
        self._validate_expr_components(node)

        # Collect all types appearing in the expression
        types_in_expr = self._collect_types_in_expr(node)

        # Special case: String concatenation operator ".." always returns string
        if self._has_token_recursive(node, ".."): return 'selene'
        # Special case: Comparisons always return bool
        if self._has_any_token_recursive(node, ['==', '!=', '<', '>', '<=', '>=']): return 'lani'
        
        # Determine highest type: flux > kai (float > int)
        if 'flux' in types_in_expr: return 'flux'
        if 'kai' in types_in_expr: return 'kai'
        if 'selene' in types_in_expr: return 'selene'
        if 'lani' in types_in_expr: return 'lani'
        
        # If only one type found, return it
        if len(types_in_expr) == 1:
            return list(types_in_expr)[0]
            
        # Unknown type (no literals or variables found)
        return 'unknown'

    def visit_table_dec(self, node):
        """
        Validate a table (hubble) declaration: hubble kai my_table = {1, 2, 3}
        
        Soluna supports arrays called "tables" or "hubbles":
        - hubble kai arr = {1, 2, 3}     (array of integers)
        - hubble flux nums = {1.5, 2.5}  (array of floats)
        - hubble let obj = {x: 5, y: 10} (object with string keys)
        
        Steps:
        1. Extract element type (kai, flux, let, etc.)
        2. Extract table name
        3. Declare table in symbol table with metadata
        4. For 'let' tables, track property names (keys)
        5. Validate all elements match the element type
        
        Args:
            node: A table_dec parse tree node
        
        Example:
            hubble kai scores = {95, 87, 92}
            - Element type: kai (integers)
            - Table name: scores
            - Validate 95, 87, 92 are all kai
            - Track that scores is a table with kai elements
        """
        type_node = self._find_child(node, "data_type")
        elem_type = self._extract_type_name(type_node)
        
        ident = self._find_token(node, "identifier")
        is_local = self.is_inside_local_decl or self.symbols.current_scope_level > 0
        
        if ident:
            table_keys = set()
            line, col = ident["line"], ident["col"]
            self.symbols.declare(ident["value"], {
                "category": "table",
                "type": "hubble",
                "element_type": elem_type,
                "is_initialized": True,
                "keys": table_keys
            }, line, col, is_local=is_local)

            # Validate elements in the table
            elems_node = self._find_child(node, "hubble_elements")
            if elems_node:
                self._validate_hubble_elements(elems_node, elem_type, line, col, table_keys)

            tail_node = self._find_child(node, "hubble_element_tail")
            if tail_node:
                self._validate_hubble_elements(tail_node, elem_type, line, col, table_keys)

    def _validate_hubble_elements(self, node, elem_type, line, col, table_keys=None):
        """
        Validate all elements in a table (hubble) match the declared element type.
        
        Tables can contain:
        1. Expressions: hubble kai arr = {1, 2, 3}
        2. Functions: hubble let obj = {add: func, subtract: func}
        3. Variables: hubble let obj = {x: 5, y: 10}
        
        Validation rules:
        - For typed tables (kai, flux, selene): All elements must match type
        - For 'let' tables: Can contain functions and variables (object properties)
        - Track property names in 'let' tables (needed for table.property access)
        
        Args:
            node: A hubble_elements or hubble_element_tail node
            elem_type: The declared element type (kai, flux, let, etc.)
            line, col: Error location info
            table_keys: For 'let' tables, a set to collect property names
        """
        if not node: return

        if node.get("type") in ["hubble_elements", "hubble_element_tail"]:
            expr_node = self._find_child(node, "expression")
            func_def_node = self._find_child(node, "func_def")
            table_var_dec_node = self._find_child(node, "table_var_dec")

            # Validate expression element: hubble kai arr = {1, 2, 3}
            if expr_node:
                expr_type = self._get_expression_type(expr_node)
                if not self._check_coercion(elem_type, expr_type, expr_node):
                    raise SemanticError(f"Type Mismatch: Cannot assign '{expr_type}' to table of '{elem_type}'.", line, col)

            # Validate function element: hubble let obj = {func: ...}
            # Functions can only be in 'let' (object) tables
            if func_def_node:
                if elem_type != 'let':
                    raise SemanticError(f"Cannot declare functions inside a strictly typed '{elem_type}' table.", line, col)
                if table_keys is not None:
                    ident = self._find_token(func_def_node, "identifier")
                    if ident: table_keys.add(ident["value"])
                
                # Nested variable declarations in function: hubble let obj = {func: (kai x, ...)}
                if table_var_dec_node:
                    if elem_type != 'let':
                        raise SemanticError(f"Cannot declare variables inside a strictly typed '{elem_type}' table.", line, col)
                    # Track variable names as object keys
                    if table_keys is not None:
                        var_init_node = self._find_child(table_var_dec_node, "var_init_no_semi")
                        if var_init_node:
                            idents = []
                            first_ident = self._find_token(var_init_node, "identifier")
                            if first_ident: idents.append(first_ident)
                            multi_node = self._find_child(var_init_node, "multi_identifiers")
                            self._collect_identifiers(multi_node, idents)
                            for itok in idents:
                                table_keys.add(itok["value"])

        if "children" in node:
            for child in node["children"]:
                if child and child.get("type") in ["hubble_elements", "hubble_element_tail"]:
                    self._validate_hubble_elements(child, elem_type, line, col, table_keys)

    def visit_table_nav(self, node):
        """
        Validate table access and assignment: arr[0], obj["name"], arr[0] = 5
        
        Table navigation handles:
        1. Reading from a table: kai x = arr[0]
        2. Writing to a table: arr[0] = x + 1
        3. Numeric indexing: arr[0], arr[i]
        4. String indexing (for objects): obj["key"], obj[prop_name]
        
        Steps:
        1. Look up the table variable
        2. Validate it's actually a table (not a regular variable)
        3. Validate index types are appropriate:
           - Numeric tables: indices must be numbers
           - Object tables ('let'): indices can be strings
        4. If assignment, validate RHS type matches element type
        
        Args:
            node: A table_nav parse tree node
        
        Raises:
            SemanticError if table not found, isn't a table, or types don't match
        """
        ident = self._find_token(node, "identifier")
        if ident:
            sym = self.symbols.lookup(ident["value"])
            line, col = ident["line"], ident["col"]
            
            if not sym:
                raise SemanticError(f"Variable '{ident['value']}' not declared.", line, col)
            
            if sym.get("category") != "table":
                raise SemanticError(f"Cannot index non-hubble variable '{ident['value']}'.", line, col)
            
            # Store table name for error messages
            sym["name"] = ident["value"]
            # Validate indices (arr[0], arr[i], obj["key"])
            self._validate_table_indices(node, sym)
            
            # If this is an assignment: arr[0] = value
            if self._has_token(node, "="):
                expr_node = self._find_child(node, "expression")
                if expr_node:
                    expr_type = self._get_expression_type(expr_node)
                    elem_type = sym.get("element_type", "unknown")
                    if not self._check_coercion(elem_type, expr_type, expr_node):
                        raise SemanticError(f"Type Mismatch: Cannot assign '{expr_type}' to table of '{elem_type}'.", line, col)
                    
    def _visit_table_navs_in_expr(self, node):
        """
        (Deprecated) Recursively find and validate all table accesses in an expression.
        
        Note: This method is no longer used directly. Its functionality has been
        integrated into _validate_expr_components() which is called from
        _get_expression_type().
        
        Kept for backwards compatibility.
        """
        if not node: return
        if node.get("type") == "table_nav":
            self.visit_table_nav(node)
        if "children" in node:
            for child in node["children"]:
                self._visit_table_navs_in_expr(child)
    # ==========================================
    # HELPER METHODS (Guarded): Tree Navigation & Type Collection
    # ==========================================
    # These helpers traverse the parse tree and extract useful information
    # They are "guarded" to safely handle None values and missing structure

    def _check_unused(self, scope):
        """
        Check for unused variables in a scope and log warnings.
        
        When a scope closes (function body, block, etc.), check if any variables
        declared in that scope were never actually used. This helps find dead code.
        
        Example:
            kai x = 5;     // x is declared
            // x is never used
            // → Warning: 'x' is declared but never used
        
        Args:
            scope: A dictionary mapping variable names to their symbol info
        """
        for name, info in scope.items():
            if info.get("category") in ["variable", "table"] and not info.get("is_used", False):
                self.warnings.append(f"Warning: '{name}' is declared but never used (Line {info.get('line', '?')}).")

    def _find_child(self, node, type_name):
        """
        Find the first child node of a given type.
        
        Parse trees are nested structures. This helper finds the first child
        with a specific type, returning None if not found.
        
        Analogy: Think of the parse tree as a file system, and this looks for
        the first folder of a given name in the current folder.
        
        Args:
            node: A parse tree node
            type_name: The type we're looking for (e.g., "expression", "statements")
        
        Returns:
            The first child with matching type, or None
        
        Example:
            expr = self._find_child(node, "expression")
            If found: expr is a node with type="expression"
            If not found: expr is None
        """
        if not node or "children" not in node: return None
        for child in node.get("children", []):
            if child and child.get("type") == type_name: return child
        return None

    def _find_token(self, node, token_type):
        """
        Find the first TOKEN child with a specific token type.
        
        Tokens are leaf nodes from the lexer: identifiers, keywords, operators, etc.
        This looks for the first token of a given type.
        
        Args:
            node: A parse tree node
            token_type: The token type we want (e.g., "identifier", "kai", "=")
        
        Returns:
            A TOKEN node with {type: "TOKEN", token_type: ..., value: ..., ...}
            or None if not found
        
        Example:
            ident_token = self._find_token(node, "identifier")
            If found: ident_token["value"] is the variable name
        """
        if not node or "children" not in node: return None
        for child in node.get("children", []):
            if child and child.get("type") == "TOKEN" and child.get("token_type") == token_type: return child
        return None

    def _has_token(self, node, token_type):
        """
        Quick check: does this node contain a token of this type?
        
        Returns True if _find_token() would find something, False otherwise.
        
        Args:
            node: A parse tree node
            token_type: The token type to look for
        
        Returns:
            True if token found, False otherwise
        
        Example:
            if self._has_token(node, "="):
                # This is an assignment statement
        """
        return self._find_token(node, token_type) is not None

    def _extract_type_name(self, type_node):
        """
        Extract the type name from a data_type node.
        
        A data_type node contains a token representing the type.
        This extracts the token type (e.g., "kai", "flux", "let").
        
        Args:
            type_node: A parse tree node representing a type declaration
        
        Returns:
            The type name string (e.g., "kai", "flux", "selene", "let")
            Returns 'void' if no type found (for functions with no return)
        
        Example:
            For "kai x = 5":
            type_node points to the "kai" part
            Returns: "kai"
        """
        if not type_node: return 'void'
        token = self._find_token_in_tree(type_node)
        return token["token_type"] if token else "unknown"

    def _find_token_in_tree(self, node):
        """
        Recursively search for the first TOKEN in a tree.
        
        Sometimes a token is nested deep in a tree (data_type → token).
        This recursively descends until it finds a TOKEN node.
        
        Args:
            node: A parse tree node
        
        Returns:
            The first TOKEN node found, or None
        
        Example:
            data_type node might have structure:
            {type: "data_type", children: [{type: "TOKEN", token_type: "kai", ...}]}
            This would return the TOKEN node.
        """
        if not node: return None
        if node.get("type") == "TOKEN": return node
        if "children" in node:
            for child in node["children"]:
                if child:
                    res = self._find_token_in_tree(child)
                    if res: return res
        return None

    def _collect_identifiers(self, node, list_ref):
        """
        Recursively collect all identifier tokens from a tree.
        
        When you write: kai x, y, z = 1, 2, 3
        The parser creates a recursive structure with multiple identifiers.
        This collects all of them into one list.
        
        Grammar:
            multi_identifiers -> COMMA identifier multi_identifiers?
        
        So _collect_identifiers walks through this recursive structure.
        
        Args:
            node: A multi_identifiers or similar node
            list_ref: A list to append identifier tokens to
        
        Example:
            For "x, y, z":
            list_ref becomes: [token(x), token(y), token(z)]
        """
        if not node: return
        ident = self._find_token(node, "identifier")
        if ident: list_ref.append(ident)
        next_multi = self._find_child(node, "multi_identifiers")
        if next_multi: self._collect_identifiers(next_multi, list_ref)

    def _collect_values(self, node, list_ref):
        """
        Recursively collect all value expressions from an initialization.
        
        When you write: kai x, y, z = 1, 2, 3
        The parser creates a recursive structure with values: 1, 2, 3
        This collects all of them into one list.
        
        Grammar:
            value_init -> value value_init_tail?
            value_init_tail -> COMMA value value_init_tail?
        
        Each value can be:
        - A literal: 5, 3.14, "hello"
        - A variable: x, y, z
        - A function call: rand(), get_value()
        - A special input: lumina() (user input)
        
        Args:
            node: A value_init or value_init_tail node
            list_ref: A list to append expression/value nodes to
        
        Example:
            For "1, 2, 3":
            list_ref becomes: [<expr: 1>, <expr: 2>, <expr: 3>]
        """
        if not node: return
        val = self._find_child(node, "value")
        if val: 
            expr = self._find_child(val, "expression")
            if expr: 
                list_ref.append(expr)
            elif self._has_token(val, "lumina"):
                list_ref.append(val) # Captures the lumina() call
        next_tail = self._find_child(node, "value_init_tail")
        if next_tail: self._collect_values(next_tail, list_ref)

    def _collect_types_in_expr(self, node):
        """
        Collect all types that appear in an expression.
        
        An expression like "5 + x" contains:
        - Literal 5: type kai (integer)
        - Variable x: type depends on what x was declared as
        
        So _collect_types_in_expr returns: {kai, ...x's type...}
        
        This is used to determine the overall expression type.
        Algorithm in _get_expression_type:
        1. Collect all types
        2. Pick the "highest" type (flux > kai)
        3. Handle special operators that override this (.. = string, == = bool)
        
        Special handling for indexing:
        - When a string is indexed (str[i]), the result type is 'blaze' (character)
        - When a table is indexed (arr[i]), the result type is the element type
        
        Args:
            node: A parse tree node
        
        Returns:
            A set of type strings: {'kai'}, {'flux', 'kai'}, etc.
        
        Special cases:
        - Function calls: Get return type from symbol table
        - Table indices: Stop descending into identifier_tail but return element type
        - String indices: Return character type (blaze)
        - Uninitialized variables: Raise SemanticError
        """
        types = set()
        if not node: return types
        
        node_type = node.get("type")
        
        # For function calls, return type is the function's return type
        if node_type in ["func_call", "func_call_in_expr"]:
            ident = self._find_token(node, "identifier")
            if ident:
                sym = self.symbols.lookup(ident["value"])
                if sym: types.add(sym.get("type", sym.get("return_type", "unknown")))
            return types 
            
        # Handle indexing: when identifier is followed by identifier_tail with table_index
        if node_type == "factor_value":
            ident = self._find_token(node, "identifier")
            tail = self._find_child(node, "identifier_tail")
            if ident and tail and self._find_child(tail, "table_index"):
                sym = self.symbols.lookup(ident["value"])
                if sym:
                    # String indexing returns character type
                    if sym.get("type") == "selene":
                        return {"blaze"}
                    # Table indexing returns element type
                    elif sym.get("category") == "table":
                        elem_type = sym.get("element_type", "unknown")
                        return {elem_type} if elem_type else types
            # If no indexing, continue with normal type collection
            
        # Stop traversing into brackets - we don't need types from indices
        # (only from the array element type)
        if node_type == "identifier_tail":
            return types 
        
        # Handle literal tokens and variable references
        if node_type == "TOKEN":
            tt = node.get("token_type")
            if tt == 'integer': types.add('kai')
            elif tt == 'float': types.add('flux')
            elif tt == 'string': types.add('selene')
            elif tt == 'char': types.add('blaze')
            elif tt in ['iris', 'sage']: types.add('lani')  # true/false
            elif tt == 'identifier':
                sym = self.symbols.lookup(node.get("value"))
                if not sym: 
                    raise SemanticError(f"Undefined variable '{node.get('value')}'", node.get('line'), node.get('col'))
                
                # Function names must be called with parentheses
                if sym.get("category") == "function":
                    raise SemanticError(f"Function '{node.get('value')}' must be called with parentheses ().", node.get('line'), node.get('col'))
                
                # Variables must be initialized before use
                if sym.get("category") == "variable" and not sym.get("is_initialized", False):
                    raise SemanticError(f"Variable '{node.get('value')}' is uninitialized and cannot be used.", node.get('line'), node.get('col'))
                else:
                    types.add(sym.get("type", sym.get("return_type", "unknown")))
                    
        # Recursively collect types from children
        if "children" in node:
            for child in node["children"]:
                if child: types.update(self._collect_types_in_expr(child))
        return types
    
    def _has_token_recursive(self, node, token_type):
        """
        Recursively search: does this subtree contain a specific token type?
        
        Unlike _find_token (which only looks at direct children),
        this searches the entire subtree recursively.
        
        Useful for checking if an expression contains a specific operator:
        - Does it have ".." (string concatenation)?
        - Does it have any comparison operators?
        
        Args:
            node: A parse tree node
            token_type: Token type to search for
        
        Returns:
            True if found anywhere in the subtree, False otherwise
        
        Example:
            if self._has_token_recursive(expr_node, ".."):
                # This expression concatenates strings
        """
        if not node: return False
        if node.get("type") == "TOKEN" and node.get("token_type") == token_type: return True
        if "children" in node:
            for child in node["children"]:
                if self._has_token_recursive(child, token_type): return True
        return False

    def _has_any_token_recursive(self, node, token_list):
        """
        Recursively search: does this subtree contain ANY token from a list?
        
        Extension of _has_token_recursive for checking multiple tokens.
        Useful for checking if expression contains any comparison operator.
        
        Args:
            node: A parse tree node
            token_list: A list of token types to search for
        
        Returns:
            True if any token from the list is found, False otherwise
        
        Example:
            if self._has_any_token_recursive(node, ['==', '!=', '<', '>']):
                # This is a comparison expression (returns bool)
        """
        if not node: return False
        if node.get("type") == "TOKEN" and node.get("token_type") in token_list: return True
        if "children" in node:
            for child in node["children"]:
                if self._has_any_token_recursive(child, token_list): return True
        return False
    
    def _evaluate_static_string(self, node):
        """
        Evaluate an expression to a static string value if possible.
        
        For type narrowing (double → int), we need to know if a value is
        statically known at compile time. This extracts that value.
        
        Can extract:
        - String literals: "hello" → "hello"
        - Numeric literals: 5 → "5", 3.14 → "3.14"
        - Variable constants: if x was const 5, returns "5"
        
        Cannot evaluate:
        - Function calls (runtime only)
        - Non-const variables (values not known)
        - Complex expressions
        
        Returns None if value cannot be determined statically.
        
        Args:
            node: A parse tree node (often a literal or variable)
        
        Returns:
            A string representation of the value, or None if not static
        
        Example:
            For: kai x = 5.0  (where 5.0 is a flux literal)
            Returns: "5.0"
            Later, _check_coercion can verify 5.0 can be converted to kai
        """
        if not node: return ""
        
        if node.get("type") == "TOKEN":
            tt = node.get("token_type")
            if tt in ["string", "char"]:
                return node.get("value", "").strip("\"'")
            if tt in ["integer", "float"]:
                return str(node.get("value"))
            if tt == "identifier":
                sym = self.symbols.lookup(node.get("value"))
                if sym and sym.get("static_value") is not None:
                    return str(sym["static_value"])
                return None
            return ""
        
        result = ""
        if "children" in node:
            for child in node["children"]:
                val = self._evaluate_static_string(child)
                if val is None:
                    return None
                result += val
        return result
    
    def _check_division_by_zero(self, node):
        """
        Detect potential division or modulo by zero at compile time.
        
        If we see code like: x / 0 or y % 0
        We can catch this immediately rather than waiting for runtime.
        
        Checks for these operators:
        - "/" (integer division)
        - "//" (floor division)
        - "%" (modulo)
        
        Only detects LITERAL zero (0 as a constant), not:
        - x / y (where y happens to be 0)
        - x / 0.0 (we'd need float check)
        
        Args:
            node: A parse tree node containing an expression
        
        Raises:
            SemanticError if division/modulo by literal 0 is detected
        """
        tokens = self._get_all_tokens(node)
        for i in range(len(tokens) - 1):
            val = tokens[i].get("value")
            # Check for division/modulo operator followed by 0
            if val in ["/", "//", "%"] and str(tokens[i+1].get("value")) == "0":
                raise SemanticError("Division or modulo by zero detected.", tokens[i+1]["line"], tokens[i+1]["col"])
            
    def _get_all_tokens(self, node):
        """
        Recursively collect ALL tokens from a subtree into a flat list.
        
        This is useful for scanning an expression for specific patterns.
        For example, finding division by zero: search for "/" followed by "0".
        
        The parse tree is hierarchical, but sometimes we need a flat view
        to check relationships between tokens.
        
        Args:
            node: A parse tree node
        
        Returns:
            A list of all TOKEN nodes found in the tree (depth-first order)
        
        Example:
            For expression: x + 5 / 0
            Returns: [TOKEN(identifier,x), TOKEN(+), TOKEN(5), TOKEN(/), TOKEN(0)]
        """
        tokens = []
        if not node: return tokens
        if node.get("type") == "TOKEN":
            tokens.append(node)
        if "children" in node:
            for child in node["children"]:
                tokens.extend(self._get_all_tokens(child))
        return tokens
    
    def visit_output_statement(self, node):
        """
        Validate an output statement: nova(expression);
        
        Steps:
        1. Find the output_arg (what to print)
        2. Extract the expression being output
        3. Get its type (validates it's valid)
        
        The type doesn't matter - any type can be printed.
        This just ensures the expression is valid.
        
        Args:
            node: An output_statement parse tree node
        """
        arg_node = self._find_child(node, "output_arg")
        if arg_node:
            expr_node = self._find_child(arg_node, "expression")
            if expr_node:
                self._get_expression_type(expr_node)

    def _check_no_starting_semicolon(self, block_node, error_msg):
        """
        Check that a code block doesn't start with an empty statement (;).
        
        Common syntax error:
            sol x > 0 cos;  // <- Error: semicolon after condition
                ...
            mos
        
        A block of statements should not start with just a semicolon.
        This helper validates that.
        
        Args:
            block_node: A 'statements' or 'loop_statements' node
            error_msg: The error message to show if semicolon found
        
        Raises:
            SemanticError if starting semicolon is detected
        """
        if block_node and "children" in block_node and len(block_node["children"]) > 0:
            first_child = block_node["children"][0]
            # Handle both standard 'statements' and 'loop_statements'
            if first_child and first_child.get("type") in ["statement", "loop_statement"]:
                empty_stmt = self._find_child(first_child, "empty_statement")
                if empty_stmt:
                    tokens = self._get_all_tokens(empty_stmt)
                    if tokens:
                        raise SemanticError(error_msg, tokens[0]["line"], tokens[0]["col"])
                    
    def _check_string_math(self, node):
        """
        Detect attempt to do arithmetic on non-numeric strings.
        
        Common error:
            let msg = "hello" + 5  // <- Error: can't add number to string
        
        We can detect this when:
        - Expression contains arithmetic operators (+, -, *, /, %, ^, etc.)
        - And contains string literals
        - And those strings don't hold numeric values
        
        Allowed:
            "hello" + " world"  (string concatenation with .., not +)
            let x = "5";
            kai y = x + 10      (if "5" converts to number)
        
        Args:
            node: A parse tree node containing an expression
        
        Raises:
            SemanticError if non-numeric string is used in arithmetic
        """
        # Check if expression contains any arithmetic operators
        if self._has_any_token_recursive(node, ['+', '-', '*', '/', '//', '%', '^']):
            tokens = self._get_all_tokens(node)
            for t in tokens:
                # Found a string literal in an arithmetic expression
                if t.get("token_type") in ["string", "char"]:
                    val = str(t.get("value", "")).strip("\"'")
                    # Try to parse it as a number - if it fails, error
                    try:
                        float(val)  # Can this string be converted to a number?
                    except ValueError:
                        raise SemanticError(f"String literal '{val}' cannot be used in an arithmetic expression.", t["line"], t["col"])
    
    def _validate_table_indices(self, node, table_sym=None):
        """
        Validate array/object indices are correct type and defined.
        
        When you access a table: arr[0], obj["key"], arr[i]
        We need to ensure:
        1. Numeric indices are numeric (kai type)
        2. String indices are only for 'let' (object) tables
        3. Variable indices are declared and initialized
        
        Examples:
            hubble kai arr = {1, 2, 3}
            arr[0]        ✓ (numeric index on numeric table)
            arr["key"]    ✗ (string index on numeric table)
            
            hubble let obj = {x: 5, y: 10}
            obj["x"]      ✓ (string index on object table)
            obj[0]        ✓ (numeric index on object - alternative syntax)
            
            kai idx = 5;
            arr[idx]      ✓ (variable index, initialized)
            
            kai bad_idx;
            arr[bad_idx]  ✗ (variable index, not initialized)
        
        Args:
            node: An index_val parse tree node (the [...] part)
            table_sym: The symbol table entry for the table being indexed
        
        Raises:
            SemanticError if index type is invalid or variable not initialized
        """
        if not node: return
        if node.get("type") == "index_val":
            
            # 1. Handle string keys (Only allowed for 'let' object tables)
            str_token = self._find_token(node, "string")
            if str_token:
                if table_sym and table_sym.get("element_type") == "let":
                    key_val = str_token.get("value", "").strip("\"'")
                    # For objects, check if the key actually exists
                    if "keys" in table_sym and key_val not in table_sym["keys"]:
                        raise SemanticError(f"Property '{key_val}' is not defined in hubble '{table_sym.get('name', 'table')}'.", str_token["line"], str_token["col"])
                else:
                    raise SemanticError("Standard tables only support numeric indexing, not string keys.", str_token["line"], str_token["col"])
            
            # 2. Check if a variable used as an index is declared and initialized
            ident = self._find_token(node, "identifier")
            if ident:
                idx_sym = self.symbols.lookup(ident["value"])
                if not idx_sym:
                    raise SemanticError(f"Undefined variable '{ident['value']}' used as index.", ident["line"], ident["col"])
                if idx_sym.get("category") == "variable" and not idx_sym.get("is_initialized", False):
                    raise SemanticError(f"Variable '{ident['value']}' used as index is uninitialized.", ident["line"], ident["col"])
        
        if "children" in node:
            for child in node["children"]:
                self._validate_table_indices(child, table_sym)

    def _validate_string_indices(self, node, string_sym=None):
        """
        Validate string indices are correct type and defined.
        
        When you index into a string: str[0], str[i]
        We need to ensure:
        1. Only numeric indices are allowed for strings (not string keys)
        2. Variable indices are declared and initialized
        
        Examples:
            let myStr = "hello"
            myStr[0]      ✓ (numeric index returns character)
            myStr["key"]  ✗ (string index not allowed on strings)
            
            kai idx = 2;
            myStr[idx]    ✓ (variable index, initialized)
            
            kai bad_idx;
            myStr[bad_idx] ✗ (variable index, not initialized)
        
        Args:
            node: An identifier_tail or table_index parse tree node
            string_sym: The symbol table entry for the string variable
        
        Raises:
            SemanticError if index type is invalid or variable not initialized
        """
        if not node: return
        
        if node.get("type") == "identifier_tail":
            # Check each table_index in the tail
            if "children" in node:
                for child in node["children"]:
                    if child and child.get("type") == "table_index":
                        self._validate_string_indices(child, string_sym)
                    elif child:
                        self._validate_string_indices(child, string_sym)
            return
        
        if node.get("type") == "table_index":
            index_val = self._find_child(node, "index_val")
            if index_val:
                self._validate_string_indices(index_val, string_sym)
            return
        
        if node.get("type") == "index_val":
            # 1. String keys are NOT allowed for strings
            str_token = self._find_token(node, "string")
            if str_token:
                raise SemanticError("String indices are only numeric. Cannot use string literal as index.", str_token["line"], str_token["col"])
            
            # 2. Check if a variable used as an index is declared and initialized
            ident = self._find_token(node, "identifier")
            if ident:
                idx_sym = self.symbols.lookup(ident["value"])
                if not idx_sym:
                    raise SemanticError(f"Undefined variable '{ident['value']}' used as string index.", ident["line"], ident["col"])
                if idx_sym.get("category") == "variable" and not idx_sym.get("is_initialized", False):
                    raise SemanticError(f"Variable '{ident['value']}' used as string index is uninitialized.", ident["line"], ident["col"])
        
        if "children" in node:
            for child in node["children"]:
                self._validate_string_indices(child, string_sym)