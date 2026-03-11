from .symbol_table import SymbolTable
from .errors import SemanticError

class SemanticAnalyzer:
    def __init__(self):
        self.symbols = SymbolTable()
        self.warnings = []
        self.current_return_type = None
        self.is_inside_local_decl = False

    def analyze(self, tree):
        self.symbols = SymbolTable()
        self.warnings = []
        self.current_return_type = None
        self.is_inside_local_decl = False
        
        self._declare_all_functions(tree)
        
        if tree:
            self.visit(tree)
            
        self._check_unused(self.symbols.scopes[0])

    def visit(self, node):
        if not node: return None
        node_type = node.get("type")
        method_name = f"visit_{node_type}" if node_type else "generic_visit"
        
        if not hasattr(self, method_name) and node_type:
            print(f"Unmapped AST Node: {node_type}")
            
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        if not node: return
        if "children" in node:
            for child in node["children"]:
                if child: self.visit(child)

    def _declare_all_functions(self, node):
        if not node: return
        
        if node.get("type") == "func_dec":
            func_def = self._find_child(node, "func_def")
            if func_def:
                func_type_node = self._find_child(func_def, "func_data_type")
                return_type = self._extract_type_name(func_type_node)
                
                func_name_token = self._find_token(func_def, "identifier")
                
                params = []
                func_params_node = self._find_child(func_def, "func_params")
                if func_params_node:
                    self._collect_params(func_params_node, params)
                
                if func_name_token:
                    func_name = func_name_token["value"]
                    param_types = [p["type"] for p in params]
                    
                    if self.symbols.lookup(func_name):
                        raise SemanticError(f"Function '{func_name}' is already declared.", func_name_token["line"], func_name_token["col"])
                    
                    self.symbols.declare(func_name, {
                        "category": "function",
                        "return_type": return_type,
                        "params": param_types
                    }, func_name_token["line"], func_name_token["col"], is_local=False)

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
    # 2. TYPE COERCION
    # ==========================================
    
    def _check_coercion(self, target, source, expr_node=None):
        if target == 'let' or target == source or source == 'zeru': return True

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

        if target == 'kai' and source in ['flux', 'lani']: return True
        if target == 'flux' and source in ['kai', 'lani']: return True
        if target == 'lani': return True 
        return False

    # ==========================================
    # 3. STATEMENTS
    # ==========================================
    
    def visit_assignment_statement(self, node):
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

        ident_token = self._find_token(node, "identifier")
        if ident_token:
            var_name = ident_token["value"]
            line, col = ident_token["line"], ident_token["col"]

            symbol = self.symbols.lookup(var_name)
            if not symbol:
                raise SemanticError(f"Variable '{var_name}' not declared.", line, col)
            if symbol.get("is_const"):
                raise SemanticError(f"Cannot reassign constant variable '{var_name}'.", line, col)
            
            symbol["is_initialized"] = True

            assign_val = self._find_child(node, "assignment_value")
            val_wrapper = self._find_child(assign_val, "value") 
            
            if val_wrapper and not self._has_token(val_wrapper, "lumina"):
                val_node = self._find_child(val_wrapper, "expression")
                if val_node:
                    expr_type = self._get_expression_type(val_node)
                    if not self._check_coercion(symbol["type"], expr_type, val_node):
                        raise SemanticError(f"Type Mismatch: Cannot assign '{expr_type}' to '{symbol['type']}'.", line, col)
                    symbol["static_value"] = self._evaluate_static_string(val_node)

    def visit_statements(self, node):
        self.generic_visit(node)

    def visit_conditional_statement(self, node):
        """
        Rule: sol (if) ...
        We explicitly scope the bodies of the if/else blocks.
        """
        if not node or "children" not in node: return

        statements_node = self._find_child(node, "statements")
        self._check_no_starting_semicolon(statements_node, "Condition cannot be followed by a semicolon.")

        for child in node["children"]:
            if not child: continue
            
            # The grammar usually structures this as: sol -> conditions -> statements -> mos
            # We want to scope the 'statements' part.
            if child.get("type") == "statements":
                self.symbols.enter_scope()
                self.visit(child)
                popped = self.symbols.exit_scope()
                self._check_unused(popped)
            else:
                self.visit(child)

    def visit_conditions(self, node):
        if not node: return

        tokens = self._get_all_tokens(node)
        for t in tokens:
            if t.get("value") == ";":
                raise SemanticError("Conditions cannot contain a semicolon.", t.get("line", 0), t.get("col", 0))
        
        # Check if the condition directly contains an expression
        expr_node = self._find_child(node, "expression")
        if expr_node:
            self._get_expression_type(expr_node)
        else:
            # If it is a nested condition like ( conditions ), keep traversing
            self.generic_visit(node)

    def visit_loop_repeat_until_statement(self, node):
        self.symbols.enter_loop()
        self.symbols.enter_scope()
        self.generic_visit(node)
        popped = self.symbols.exit_scope()
        self._check_unused(popped)
        self.symbols.exit_loop()

    def visit_loop_while_statement(self, node):
        self.symbols.enter_loop()
        self.symbols.enter_scope()
        self.generic_visit(node)
        popped = self.symbols.exit_scope()
        self._check_unused(popped)
        self.symbols.exit_loop()

    def visit_loop_for_statement(self, node):
        self.symbols.enter_loop()
        self.symbols.enter_scope() # Scope 1: Loop Parameters

        params_node = self._find_child(node, "for_loop_params")
        if params_node:
            for_start = self._find_child(params_node, "for_start")
            if for_start:
                self._validate_for_start(for_start)
            
            # Validate Limit Expression
            for_limit = self._find_child(params_node, "for_limit")
            if for_limit:
                limit_expr = self._find_child(for_limit, "expr_factor")
                if limit_expr:
                    limit_type = self._get_expression_type(limit_expr)
                    if limit_type not in ['kai', 'unknown']:
                        raise SemanticError(f"For loop limit must evaluate to 'kai', got '{limit_type}'.", 0, 0)
            
            # Validate Step Expression
            for_step = self._find_child(params_node, "for_step")
            if for_step:
                step_expr = self._find_child(for_step, "expr_factor")
                if step_expr:
                    step_type = self._get_expression_type(step_expr)
                    if step_type not in ['kai', 'unknown']:
                        raise SemanticError(f"For loop step must evaluate to 'kai', got '{step_type}'.", 0, 0)

        # Process Inner Loop Block
        loop_statements = self._find_child(node, "loop_statements")
        if loop_statements:
            self.symbols.enter_scope() # Scope 2: Nested Loop Body
            self.visit(loop_statements)
            popped_body = self.symbols.exit_scope()
            self._check_unused(popped_body)
        
        popped_params = self.symbols.exit_scope()
        self._check_unused(popped_params)
        self.symbols.exit_loop()

    def _validate_for_start(self, for_start_node):
        ident_token = self._find_token(for_start_node, "identifier")
        if not ident_token: return
        
        var_name = ident_token["value"]
        line, col = ident_token["line"], ident_token["col"]

        is_declaration = self._has_token(for_start_node, "kai")
        has_assignment = self._has_token(for_start_node, "=")

        if is_declaration:
            # Case 1: kai i = 1
            expr_node = self._find_child(for_start_node, "expr_factor")
            if expr_node:
                expr_type = self._get_expression_type(expr_node)
                if expr_type not in ['kai', 'unknown']:
                    raise SemanticError(f"Type Mismatch in loop init: Cannot assign '{expr_type}' to 'kai'.", line, col)
            
            self.symbols.declare(var_name, {
                "category": "variable",
                "type": "kai",
                "is_const": False,
                "is_initialized": True
            }, line, col, is_local=True)
            
        else:
            # Case 2 & 3: i = 1 OR i
            sym = self.symbols.lookup(var_name)
            if not sym:
                raise SemanticError(f"Variable '{var_name}' not declared in for loop initialization.", line, col)
            
            if sym.get("type") != "kai":
                raise SemanticError(f"For loop variable '{var_name}' must be of type 'kai', but is '{sym.get('type')}'.", line, col)

            if has_assignment:
                expr_node = self._find_child(for_start_node, "expr_factor")
                if expr_node:
                    expr_type = self._get_expression_type(expr_node)
                    if expr_type not in ['kai', 'unknown']:
                        raise SemanticError(f"Type Mismatch in loop init: Cannot assign '{expr_type}' to 'kai'.", line, col)

    def visit_break_statements(self, node):
        if not self.symbols.is_inside_loop():
             raise SemanticError("Statement 'warp' can only be used inside a loop.", 0, 0)

    # ==========================================
    # 4. FUNCTIONS
    # ==========================================
    
    def visit_func_dec(self, node):
        func_def = self._find_child(node, "func_def")
        if not func_def:
            self.generic_visit(node)
            return
        
        statements_node = self._find_child(func_def, "statements")
        self._check_no_starting_semicolon(statements_node, "Function definition cannot be followed by a semicolon.")

        func_type_node = self._find_child(func_def, "func_data_type")
        return_type = self._extract_type_name(func_type_node)
        
        func_name_token = self._find_token(func_def, "identifier")
        
        params = []
        func_params_node = self._find_child(func_def, "func_params")
        if func_params_node:
            self._collect_params(func_params_node, params)
        
        if func_name_token:
            func_name = func_name_token["value"]
            param_types = [p["type"] for p in params]
            
            if not self.symbols.lookup(func_name):
                self.symbols.declare(func_name, {
                    "category": "function",
                    "return_type": return_type,
                    "params": param_types,
                    "is_initialized": True
                }, func_name_token["line"], func_name_token["col"], is_local=False)

        self.current_return_type = return_type
        self.symbols.enter_scope()
        
        for p in params:
            self.symbols.declare(p["name"], {
                "category": "variable",
                "type": p["type"],
                "is_const": False,
                "is_initialized": True
            }, p["line"], p["col"], is_local=True)
        
        statements = self._find_child(func_def, "statements")
        if statements:
            self.visit(statements)
        
        popped = self.symbols.exit_scope()
        self._check_unused(popped)
        self.current_return_type = None

        for child in node.get("children", []):
            if child and child.get("type") != "func_def":
                self.visit(child)
                
    def visit_func_return(self, node):
        if self.current_return_type is None:
            raise SemanticError("'zara' used outside of function.", 0, 0)

        expr_node = self._find_child(node, "return_val")
        has_value = self._find_child(expr_node, "expression") is not None
        
        if self.current_return_type == 'void' and has_value:
             raise SemanticError("Void function cannot return a value.", 0, 0)
        
        if self.current_return_type != 'void' and not has_value:
             raise SemanticError(f"Function must return a value of type '{self.current_return_type}'.", 0, 0)

        if has_value:
            val_node = self._find_child(expr_node, "expression")
            val_type = self._get_expression_type(val_node)
            if not self._check_coercion(self.current_return_type, val_type, val_node):
                 raise SemanticError(f"Invalid return type. Expected '{self.current_return_type}', got '{val_type}'.", 0, 0)
    
    def _collect_params(self, node, param_list):
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
        ident = self._find_token(node, "identifier")
        if ident:
            func_name = ident["value"]
            
            # Built-in check
            if func_name in ["nova", "lumen"]:
                args_node = self._find_child(node, "func_call_args")
                args = []
                if args_node:
                    self._collect_args(args_node, args)
                for arg_expr in args:
                    self._get_expression_type(arg_expr)
                return
            
            sym = self.symbols.lookup(func_name)
            if not sym:
                raise SemanticError(f"Function '{func_name}' not declared.", ident["line"], ident["col"])
            
            if sym.get("category") != "function":
                raise SemanticError(f"'{func_name}' is not callable.", ident["line"], ident["col"])
            
            args_node = self._find_child(node, "func_call_args")
            args = []
            if args_node:
                self._collect_args(args_node, args)
            
            expected_params = sym.get("params", [])
            
            if len(args) != len(expected_params):
                raise SemanticError(f"Function '{func_name}' expects {len(expected_params)} arguments, got {len(args)}.", ident["line"], ident["col"])
            
            for i, arg_expr in enumerate(args):
                arg_type = self._get_expression_type(arg_expr)
                expected_type = expected_params[i]
                if not self._check_coercion(expected_type, arg_type, arg_expr):
                    raise SemanticError(f"Argument {i+1} of '{func_name}' expects '{expected_type}', got '{arg_type}'.", ident["line"], ident["col"])

    def visit_func_call_in_expr(self, node):
        self.visit_func_call(node)

    def _collect_args(self, node, arg_list):
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
        if not node: return
        
        node_type = node.get("type")
        if node_type == "table_nav":
            self.visit_table_nav(node)

        if node_type == "factor_value":
            ident = self._find_token(node, "identifier")
            tail = self._find_child(node, "identifier_tail")
            if ident and tail and self._find_child(tail, "table_index"):
                sym = self.symbols.lookup(ident["value"])
                
                if sym and sym.get("category") != "table":
                    raise SemanticError(f"Cannot index non-table variable '{ident['value']}'.", ident["line"], ident["col"])
                
                # Make sure you have this block!
                if sym and sym.get("category") == "table":
                    sym["name"] = ident["value"] 
                    self._validate_table_indices(tail, sym)
            
        if node_type in ["func_call", "func_call_in_expr"]:
            self.visit_func_call(node)
            return
            
        if "children" in node:
            for child in node["children"]:
                self._validate_expr_components(child)
    
    def _get_expression_type(self, node):
        if not node: return 'zeru'

        self._check_division_by_zero(node)
        self._check_string_math(node)
        self._validate_expr_components(node) # Replaces _visit_table_navs_in_expr

        types_in_expr = self._collect_types_in_expr(node)

        if self._has_token_recursive(node, ".."): return 'selene'
        if self._has_any_token_recursive(node, ['==', '!=', '<', '>', '<=', '>=']): return 'lani'
        
        if 'flux' in types_in_expr: return 'flux'
        if 'kai' in types_in_expr: return 'kai'
        if 'selene' in types_in_expr: return 'selene'
        if 'lani' in types_in_expr: return 'lani'
        
        if len(types_in_expr) == 1:
            return list(types_in_expr)[0]
            
        return 'unknown'

    def visit_table_dec(self, node):
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

            elems_node = self._find_child(node, "hubble_elements")
            if elems_node:
                self._validate_hubble_elements(elems_node, elem_type, line, col, table_keys)

            tail_node = self._find_child(node, "hubble_element_tail")
            if tail_node:
                self._validate_hubble_elements(tail_node, elem_type, line, col, table_keys)

    def _validate_hubble_elements(self, node, elem_type, line, col, table_keys=None):
        if not node: return

        if node.get("type") in ["hubble_elements", "hubble_element_tail"]:
            expr_node = self._find_child(node, "expression")
            func_def_node = self._find_child(node, "func_def")
            table_var_dec_node = self._find_child(node, "table_var_dec")

            if expr_node:
                expr_type = self._get_expression_type(expr_node)
                if not self._check_coercion(elem_type, expr_type, expr_node):
                    raise SemanticError(f"Type Mismatch: Cannot assign '{expr_type}' to table of '{elem_type}'.", line, col)

            if func_def_node:
                if elem_type != 'let':
                    raise SemanticError(f"Cannot declare functions inside a strictly typed '{elem_type}' table.", line, col)
                if table_keys is not None:
                    ident = self._find_token(func_def_node, "identifier")
                    if ident: table_keys.add(ident["value"])
                if table_var_dec_node:
                    if elem_type != 'let':
                        raise SemanticError(f"Cannot declare variables inside a strictly typed '{elem_type}' table.", line, col)
                    # NEW FIX: Track variable names as object keys
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
        ident = self._find_token(node, "identifier")
        if ident:
            sym = self.symbols.lookup(ident["value"])
            line, col = ident["line"], ident["col"]
            
            if not sym:
                raise SemanticError(f"Variable '{ident['value']}' not declared.", line, col)
            
            if sym.get("category") != "table":
                raise SemanticError(f"Cannot index non-hubble variable '{ident['value']}'.", line, col)
            
            sym["name"] = ident["value"]
            self._validate_table_indices(node, sym)
            
            if self._has_token(node, "="):
                expr_node = self._find_child(node, "expression")
                if expr_node:
                    expr_type = self._get_expression_type(expr_node)
                    elem_type = sym.get("element_type", "unknown")
                    if not self._check_coercion(elem_type, expr_type, expr_node):
                        raise SemanticError(f"Type Mismatch: Cannot assign '{expr_type}' to table of '{elem_type}'.", line, col)
                    
    def _visit_table_navs_in_expr(self, node):
        if not node: return
        if node.get("type") == "table_nav":
            self.visit_table_nav(node)
        if "children" in node:
            for child in node["children"]:
                self._visit_table_navs_in_expr(child)
    # ==========================================
    # HELPER METHODS (Guarded)
    # ==========================================

    def _check_unused(self, scope):
        """Helper to log warnings for unused variables when a scope closes."""
        for name, info in scope.items():
            if info.get("category") in ["variable", "table"] and not info.get("is_used", False):
                self.warnings.append(f"Warning: '{name}' is declared but never used (Line {info.get('line', '?')}).")

    def _find_child(self, node, type_name):
        if not node or "children" not in node: return None
        for child in node.get("children", []):
            if child and child.get("type") == type_name: return child
        return None

    def _find_token(self, node, token_type):
        if not node or "children" not in node: return None
        for child in node.get("children", []):
            if child and child.get("type") == "TOKEN" and child.get("token_type") == token_type: return child
        return None

    def _has_token(self, node, token_type):
        return self._find_token(node, token_type) is not None

    def _extract_type_name(self, type_node):
        if not type_node: return 'void'
        token = self._find_token_in_tree(type_node)
        return token["token_type"] if token else "unknown"

    def _find_token_in_tree(self, node):
        if not node: return None
        if node.get("type") == "TOKEN": return node
        if "children" in node:
            for child in node["children"]:
                if child:
                    res = self._find_token_in_tree(child)
                    if res: return res
        return None

    def _collect_identifiers(self, node, list_ref):
        if not node: return
        ident = self._find_token(node, "identifier")
        if ident: list_ref.append(ident)
        next_multi = self._find_child(node, "multi_identifiers")
        if next_multi: self._collect_identifiers(next_multi, list_ref)

    def _collect_values(self, node, list_ref):
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
        types = set()
        if not node: return types
        
        node_type = node.get("type")
        
        if node_type in ["func_call", "func_call_in_expr"]:
            ident = self._find_token(node, "identifier")
            if ident:
                sym = self.symbols.lookup(ident["value"])
                if sym: types.add(sym.get("type", sym.get("return_type", "unknown")))
            return types 
            
        # Stop traversing down into brackets if we hit a table index!
        if node_type == "identifier_tail":
            return types 
        
        if node_type == "TOKEN":
            tt = node.get("token_type")
            if tt == 'integer': types.add('kai')
            elif tt == 'float': types.add('flux')
            elif tt == 'string': types.add('selene')
            elif tt == 'char': types.add('blaze')
            elif tt in ['iris', 'sage']: types.add('lani')
            elif tt == 'identifier':
                sym = self.symbols.lookup(node.get("value"))
                if not sym: 
                    raise SemanticError(f"Undefined variable '{node.get('value')}'", node.get('line'), node.get('col'))
                
                if sym.get("category") == "function":
                    raise SemanticError(f"Function '{node.get('value')}' must be called with parentheses ().", node.get('line'), node.get('col'))
                
                if sym.get("category") == "variable" and not sym.get("is_initialized", False):
                    raise SemanticError(f"Variable '{node.get('value')}' is uninitialized and cannot be used.", node.get('line'), node.get('col'))
                else:
                    types.add(sym.get("type", sym.get("return_type", "unknown")))
                    
        if "children" in node:
            for child in node["children"]:
                if child: types.update(self._collect_types_in_expr(child))
        return types
    
    def _has_token_recursive(self, node, token_type):
        if not node: return False
        if node.get("type") == "TOKEN" and node.get("token_type") == token_type: return True
        if "children" in node:
            for child in node["children"]:
                if self._has_token_recursive(child, token_type): return True
        return False

    def _has_any_token_recursive(self, node, token_list):
        if not node: return False
        if node.get("type") == "TOKEN" and node.get("token_type") in token_list: return True
        if "children" in node:
            for child in node["children"]:
                if self._has_any_token_recursive(child, token_list): return True
        return False
    
    def _evaluate_static_string(self, node):
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
        tokens = self._get_all_tokens(node)
        for i in range(len(tokens) - 1):
            val = tokens[i].get("value")
            # NEW FIX: Added '%' to the zero-check list
            if val in ["/", "//", "%"] and str(tokens[i+1].get("value")) == "0":
                raise SemanticError("Division or modulo by zero detected.", tokens[i+1]["line"], tokens[i+1]["col"])
            
    def _get_all_tokens(self, node):
        tokens = []
        if not node: return tokens
        if node.get("type") == "TOKEN":
            tokens.append(node)
        if "children" in node:
            for child in node["children"]:
                tokens.extend(self._get_all_tokens(child))
        return tokens
    
    def visit_output_statement(self, node):
        arg_node = self._find_child(node, "output_arg")
        if arg_node:
            expr_node = self._find_child(arg_node, "expression")
            if expr_node:
                self._get_expression_type(expr_node)

    def _check_no_starting_semicolon(self, block_node, error_msg):
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
        # If the expression contains ANY arithmetic operator
        if self._has_any_token_recursive(node, ['+', '-', '*', '/', '//', '%', '^']):
            tokens = self._get_all_tokens(node)
            for t in tokens:
                if t.get("token_type") in ["string", "char"]:
                    val = str(t.get("value", "")).strip("\"'")
                    try:
                        float(val) # Test if the string holds a numerical value
                    except ValueError:
                        raise SemanticError(f"String literal '{val}' cannot be used in an arithmetic expression.", t["line"], t["col"])
    
    def _validate_table_indices(self, node, table_sym=None):
        if not node: return
        if node.get("type") == "index_val":
            
            # 1. Handle string keys (Only allowed for 'let' object tables)
            str_token = self._find_token(node, "string")
            if str_token:
                if table_sym and table_sym.get("element_type") == "let":
                    key_val = str_token.get("value", "").strip("\"'")
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