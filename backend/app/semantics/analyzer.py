# app/semantics/analyzer.py
from .symbol_table import SymbolTable
from .errors import SemanticError

class SemanticAnalyzer:
    def __init__(self):
        self.symbols = SymbolTable()
        self.current_return_type = None
        # STATE FLAG: Tracks if we are currently inside a 'local ...' declaration wrapper
        self.is_inside_local_decl = False 

    def analyze(self, tree):
        self.symbols = SymbolTable()
        self.current_return_type = None
        self.is_inside_local_decl = False
        if tree:
            self.visit(tree)

    def visit(self, node):
        if not node: return None
        node_type = node.get("type")
        method_name = f"visit_{node_type}" if node_type else "generic_visit"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        if not node: return
        if "children" in node:
            for child in node["children"]:
                if child: self.visit(child)

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
        # 1. Check Scope Context
        # We use the flag set by visit_local_dec because the 'local' token is a parent, not a child.
        is_local = self.is_inside_local_decl
        
        is_const = self._has_token(node, "zeta")
        
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

        for i, ident_token in enumerate(identifiers):
            var_name = ident_token["value"]
            line, col = ident_token["line"], ident_token["col"]

            val_node = values[i] if i < len(values) else None
            final_type = declared_type

            if declared_type == 'let':
                if val_node:
                    final_type = self._get_expression_type(val_node)
                    if final_type == 'unknown': final_type = 'zeru' 
                else:
                    final_type = 'zeru'
            elif val_node:
                expr_type = self._get_expression_type(val_node)
                if not self._check_coercion(declared_type, expr_type):
                     raise SemanticError(f"Type Mismatch: Cannot assign '{expr_type}' to '{declared_type}'.", line, col)

            # Register with correct scope preference
            self.symbols.declare(var_name, {
                "category": "variable",
                "type": final_type,
                "is_const": is_const
            }, line, col, is_local=is_local)

    # ==========================================
    # 2. TYPE COERCION
    # ==========================================
    
    def _check_coercion(self, target, source):
        if target == 'let' or target == source or source == 'zeru': return True
        if target == 'kai' and source in ['flux', 'lani', 'selene']: return True
        if target == 'flux' and source in ['kai', 'lani', 'selene']: return True
        if target == 'lani': return True 
        return False

    # ==========================================
    # 3. STATEMENTS
    # ==========================================
    
    def visit_assignment_statement(self, node):
        # Case 1: Array/Table Assignment (a[1] = 5)
        table_nav = self._find_child(node, "table_nav")
        if table_nav:
            self.visit_table_nav(table_nav)
            return

        # Case 2: Standard Assignment
        ident_token = self._find_token(node, "identifier")
        if ident_token:
            var_name = ident_token["value"]
            line, col = ident_token["line"], ident_token["col"]

            symbol = self.symbols.lookup(var_name)
            if not symbol:
                raise SemanticError(f"Variable '{var_name}' not declared.", line, col)
            if symbol.get("is_const"):
                raise SemanticError(f"Cannot reassign constant variable '{var_name}'.", line, col)

            assign_val = self._find_child(node, "assignment_value")
            val_wrapper = self._find_child(assign_val, "value") 
            val_node = self._find_child(val_wrapper, "expression")

            if val_node:
                expr_type = self._get_expression_type(val_node)
                if not self._check_coercion(symbol["type"], expr_type):
                    raise SemanticError(f"Type Mismatch: Cannot assign '{expr_type}' to '{symbol['type']}'.", line, col)

    def visit_statements(self, node):
        self.generic_visit(node)

    def visit_conditional_statement(self, node):
        """
        Rule: sol (if) ...
        We explicitly scope the bodies of the if/else blocks.
        """
        if not node or "children" not in node: return

        for child in node["children"]:
            if not child: continue
            
            # The grammar usually structures this as: sol -> conditions -> statements -> mos
            # We want to scope the 'statements' part.
            if child.get("type") == "statements":
                self.symbols.enter_scope()
                self.visit(child)
                self.symbols.exit_scope()
            else:
                self.visit(child)

    def visit_loop_while_statement(self, node):
        self.symbols.enter_loop()
        self.symbols.enter_scope()
        self.generic_visit(node)
        self.symbols.exit_scope()
        self.symbols.exit_loop()

    def visit_loop_for_statement(self, node):
        self.symbols.enter_loop()
        self.symbols.enter_scope()
        self.generic_visit(node)
        self.symbols.exit_scope()
        self.symbols.exit_loop()

    def visit_break_statements(self, node):
        if not self.symbols.is_inside_loop():
             raise SemanticError("Statement 'warp' can only be used inside a loop.", 0, 0)

    # ==========================================
    # 4. FUNCTIONS
    # ==========================================
    
    def visit_func_dec(self, node):
        func_type_node = self._find_child(node, "func_data_type")
        return_type = self._extract_type_name(func_type_node)
        
        func_def = self._find_child(node, "func_def")
        func_name_token = self._find_token(func_def, "identifier")
        
        if func_name_token:
            func_name = func_name_token["value"]
            self.symbols.declare(func_name, {
                "category": "function",
                "return_type": return_type,
                "params": [] 
            }, func_name_token["line"], func_name_token["col"], is_local=False)

        self.current_return_type = return_type
        self.symbols.enter_scope()
        
        if func_def:
            statements = self._find_child(func_def, "statements")
            self.visit(statements)
        
        self.symbols.exit_scope()
        self.current_return_type = None

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
            val_type = self._get_expression_type(self._find_child(expr_node, "expression"))
            if not self._check_coercion(self.current_return_type, val_type):
                 raise SemanticError(f"Invalid return type. Expected '{self.current_return_type}', got '{val_type}'.", 0, 0)

    # ==========================================
    # 5. EXPRESSIONS & TABLES
    # ==========================================
    
    def _get_expression_type(self, node):
        if not node: return 'zeru'

        token = self._find_token_in_tree(node)
        if token:
            t_type = token.get("token_type")
            if t_type == 'integer': return 'kai'
            if t_type == 'float': return 'flux'
            if t_type == 'string': return 'selene'
            if t_type == 'char': return 'blaze'
            if t_type == 'identifier':
                sym = self.symbols.lookup(token["value"])
                if not sym: raise SemanticError(f"Undefined variable '{token['value']}'", token['line'], token['col'])
                return sym["type"]
            if t_type in ['iris', 'sage']: return 'lani'
        
        if self._has_token_recursive(node, ".."): return 'selene'
        if self._has_any_token_recursive(node, ['==', '!=', '<', '>', '<=', '>=']): return 'lani'
        
        types_in_expr = self._collect_types_in_expr(node)
        if 'flux' in types_in_expr: return 'flux'
        if 'kai' in types_in_expr: return 'kai'
        return 'unknown'

    def visit_table_dec(self, node):
        type_node = self._find_child(node, "data_type")
        elem_type = self._extract_type_name(type_node)
        
        ident = self._find_token(node, "identifier")
        
        # Use the flag from visit_local_dec
        is_local = self.is_inside_local_decl
        
        if ident:
            self.symbols.declare(ident["value"], {
                "category": "table",
                "type": "hubble",
                "element_type": elem_type
            }, ident["line"], ident["col"], is_local=is_local)

    def visit_table_nav(self, node):
        ident = self._find_token(node, "identifier")
        if ident:
            sym = self.symbols.lookup(ident["value"])
            if not sym:
                raise SemanticError(f"Variable '{ident['value']}' not declared.", ident["line"], ident["col"])

    # ==========================================
    # HELPER METHODS (Guarded)
    # ==========================================

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
            if expr: list_ref.append(expr)
        next_tail = self._find_child(node, "value_init_tail")
        if next_tail: self._collect_values(next_tail, list_ref)

    def _collect_types_in_expr(self, node):
        types = set()
        if not node: return types
        token = self._find_token_in_tree(node)
        if token:
            tt = token.get("token_type")
            if tt == 'integer': types.add('kai')
            elif tt == 'float': types.add('flux')
            elif tt == 'identifier':
                sym = self.symbols.lookup(token.get("value"))
                if sym: types.add(sym["type"])
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