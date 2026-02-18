from .symbol_table import SymbolTable
from .errors import SemanticError

class SemanticAnalyzer:
    def __init__(self):
        self.symbols = SymbolTable()
        self.loop_depth = 0          # Tracks if we are inside a loop (for 'warp')
        self.current_func_type = None # Tracks current function return type (for 'zara')

    def analyze(self, tree):
        self.symbols = SymbolTable()
        self.loop_depth = 0
        self.current_func_type = None
        self.visit(tree)

    def visit(self, node):
        if not isinstance(node, dict): return
        
        # Dynamic dispatch based on node type
        node_type = node.get("type")
        method_name = f"visit_{node_type}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        if "children" in node:
            for child in node["children"]:
                self.visit(child)

    # =========================================================================
    #  DECLARATIONS & SCOPING
    # =========================================================================

    def visit_Program(self, node):
        self.generic_visit(node)

    def visit_Block(self, node):
        # Rule: Blocks create new scope (unless it's a function body which is handled separately)
        # However, looking at Grammar, 'statements' -> Block.
        # We generally want explicit scoping for Ifs and Loops.
        # For raw blocks, we can push scope or rely on parent container.
        # Let's rely on parents (IfStatement, etc.) to push scope to avoid double scoping.
        self.generic_visit(node)

    def visit_VariableDeclaration(self, node):
        # Children: [mutability?, data_type, var_init]
        
        is_const = self._has_token(node, "ZETA")
        is_local = self._has_token(node, "LOCAL") # Although Grammar puts LOCAL in 'local_dec' rule
        
        # Extract Type
        type_node = self._find_child_by_type(node, "data_type")
        var_type = self._extract_source_text(type_node) if type_node else "let"

        # Extract Initialization
        init_node = self._find_child_by_type(node, "VarInitialization")
        if init_node:
            self._handle_var_init(init_node, var_type, is_const)

    def _handle_var_init(self, node, var_type, is_const):
        # var_init -> IDENTIFIER multi_identifiers value_init?
        
        # 1. Main Identifier
        ident_token = self._find_child_by_type(node, "Identifier")
        if ident_token:
            name = ident_token["value"]
            # We can't easily get line/col from the dict tree unless we preserved it.
            # Assuming Token nodes have it or we catch basic errors.
            self.symbols.declare(name, var_type, is_const, 0, 0)

        # 2. Multi Identifiers (e.g. kai a, b, c)
        multi_node = self._find_child_by_type(node, "multi_identifiers")
        if multi_node:
            # Recursively find identifiers
            # (Simplified for brevity, would iterate children)
            pass

        # 3. Type Checking of Value
        # value_init -> ASSIGN values
        # We need to check if the assigned value matches 'var_type'
        # This is complex because 'value' can be an expression tree.
        # For now, we enforce CONST checks on reassignment.

    def visit_Assignment(self, node):
        # Assignment -> targets assignment_op values
        
        targets = self._find_child_by_type(node, "targets")
        if not targets: return

        # Iterate all targets (a, b = 1, 2)
        for child in targets.get("children", []):
            if child["type"] == "Identifier":
                var_name = child["value"]
                symbol = self.symbols.lookup(var_name)

                # Rule: Variable must be declared
                if not symbol:
                    raise SemanticError(f"Variable '{var_name}' has not been declared.")

                # Rule: Constant immutability [cite: 1497]
                if symbol["is_const"]:
                    raise SemanticError(f"Cannot reassign constant (zeta) variable '{var_name}'.")

    # =========================================================================
    #  FUNCTIONS
    # =========================================================================

    def visit_FunctionDefinition(self, node):
        # func_def: func_data_type IDENTIFIER LPAREN parameters? RPAREN statements
        
        # 1. Extract Signature
        ret_type_node = self._find_child_by_type(node, "func_data_type")
        ret_type = self._extract_source_text(ret_type_node)
        
        ident_node = self._find_child_by_type(node, "Identifier")
        func_name = ident_node["value"]

        params = []
        # (Parameter extraction logic would go here)

        # 2. Declare Function in Current Scope (No Hoisting support means we declare here)
        self.symbols.declare_function(func_name, ret_type, params, 0, 0)

        # 3. Enter Function Scope
        self.symbols.enter_scope()
        
        # Set context for 'zara' checks
        prev_func_type = self.current_func_type
        self.current_func_type = ret_type

        # 4. Visit Body
        block = self._find_child_by_type(node, "Block")
        if block: self.visit(block)

        # 5. Cleanup
        self.current_func_type = prev_func_type
        self.symbols.exit_scope()

    def visit_ReturnStatement(self, node):
        # Rule: Return type must match function declaration [cite: 2098]
        if self.current_func_type is None:
            raise SemanticError("Return statement 'zara' found outside of function.")
        
        # If function is void, ensure no expression
        has_expr = len(node.get("children", [])) > 0
        
        if self.current_func_type == "void" and has_expr:
            raise SemanticError("Void function cannot return a value.")
        
        # (Detailed type checking of the returned expression would happen here)

    # =========================================================================
    #  CONTROL FLOW & LOOPS
    # =========================================================================

    def visit_WhileLoop(self, node):
        self._visit_loop(node)

    def visit_ForLoop(self, node):
        self._visit_loop(node)

    def _visit_loop(self, node):
        self.loop_depth += 1
        self.symbols.enter_scope() # Loops create a new scope block
        self.generic_visit(node)
        self.symbols.exit_scope()
        self.loop_depth -= 1

    def visit_BreakStatement(self, node):
        # Rule: 'warp' only allowed inside loops 
        if self.loop_depth <= 0:
            raise SemanticError("'warp' statement found outside of a loop.")

    # =========================================================================
    #  HELPERS
    # =========================================================================

    def _find_child_by_type(self, node, type_name):
        if "children" not in node: return None
        for child in node["children"]:
            if isinstance(child, dict) and child.get("type") == type_name:
                return child
        return None

    def _has_token(self, node, token_value):
        # Recursively search for a token string (e.g. "zeta")
        if node.get("value") == token_value:
            return True
        if "children" in node:
            for child in node["children"]:
                if self._has_token(child, token_value): return True
        return False

    def _extract_source_text(self, node):
        # Rudimentary text extractor for types like "kai" or "void"
        if not node: return ""
        if node.get("value"): return node["value"]
        if node.get("children"):
            return self._extract_source_text(node["children"][0])
        return ""