# app/semantics/analyzer.py
from .symbol_table import SymbolTable
from .errors import SemanticError

class SemanticAnalyzer:
    def __init__(self):
        self.symbols = SymbolTable()

    def analyze(self, tree):
        self.symbols = SymbolTable()
        self.visit(tree)

    def visit(self, node):
        if not node: return
        
        # Dynamic dispatch based on rule name
        method_name = f"visit_{node['type']}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        if "children" in node:
            for child in node["children"]:
                self.visit(child)

    # --- Rule Handlers ---

    def visit_program(self, node):
        self.generic_visit(node)

    def visit_var_dec(self, node):
        # Rule: var_dec -> mutability data_type var_init
        
        # 1. Check Mutability
        is_const = False
        mutability_node = self._find_child(node, "mutability")
        if mutability_node and self._has_token(mutability_node, "zeta"):
            is_const = True

        # 2. Get Data Type
        type_node = self._find_child(node, "data_type")
        var_type = self._extract_token_value(type_node)

        # 3. Visit Initialization
        init_node = self._find_child(node, "var_init")
        if init_node:
            self._handle_var_init(init_node, var_type, is_const)

    def _handle_var_init(self, node, var_type, is_const):
        # Rule: var_init -> identifier multi_identifiers value_init ;
        
        ident_token = self._find_token(node, "identifier")
        if ident_token:
            var_name = ident_token["value"]
            line = ident_token["line"]
            col = ident_token["col"]

            # Register in Symbol Table
            self.symbols.declare(var_name, var_type, is_const, line, col)

    def visit_assignment_statement(self, node):
        # Rule: assignment_statement -> identifier ...
        
        ident_token = self._find_token(node, "identifier")
        if not ident_token:
            return 
            
        var_name = ident_token["value"]
        line = ident_token["line"]
        col = ident_token["col"]

        # Lookup
        symbol = self.symbols.lookup(var_name)

        # Check 1: Existence
        if not symbol:
            raise SemanticError(f"Variable '{var_name}' has not been declared.", line, col)

        # Check 2: Mutability
        if symbol["is_const"]:
            raise SemanticError(f"Cannot reassign constant variable '{var_name}'.", line, col)

    # --- Helpers ---
    
    def _find_child(self, node, type_name):
        for child in node.get("children", []):
            if child.get("type") == type_name:
                return child
        return None

    def _find_token(self, node, token_type):
        for child in node.get("children", []):
            if child.get("type") == "TOKEN" and child.get("token_type") == token_type:
                return child
        return None

    def _has_token(self, node, token_type):
        return self._find_token(node, token_type) is not None

    def _extract_token_value(self, node):
        if node.get("type") == "TOKEN":
            return node["token_type"]
        if "children" in node and node["children"]:
            return self._extract_token_value(node["children"][0])
        return None