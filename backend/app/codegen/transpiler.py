class PythonTranspiler:
    def __init__(self):
        self.indent_level = 0
        self.code = []

    def emit(self, line):
        indent = "    " * self.indent_level
        self.code.append(f"{indent}{line}")

    def generate(self, tree):
        self.visit(tree)
        return "\n".join(self.code)

    def visit(self, node):
        if not node: return ""
        
        # If it's a leaf token, just return its value
        if isinstance(node, dict) and node.get("type") == "TOKEN":
            # Map Soluna literals to Python literals
            val = node.get("value")
            if val == "iris": return "True"
            if val == "sage": return "False"
            return str(val)

        node_type = node.get("type")
        method_name = f"visit_{node_type}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        if not node or "children" not in node: return ""
        results = []
        for child in node["children"]:
            res = self.visit(child)
            if res: results.append(res)
        return "".join(results)

    # --- 1. Variables ---
    def visit_var_dec(self, node):
        # Extract the identifier and initialization value
        ident_node = self._find_token(node, "identifier")
        init_node = self._find_child(node, "value_init")
        
        if ident_node and init_node:
            var_name = ident_node["value"]
            val_str = self.visit(init_node).strip("= ") # Remove the '=' from the grammar
            self.emit(f"{var_name} = {val_str}")
        return ""

    def visit_assignment_statement(self, node):
        ident_node = self._find_token(node, "identifier")
        assign_val = self._find_child(node, "assignment_value")
        
        if ident_node and assign_val:
            var_name = ident_node["value"]
            # Extract the operator (e.g., =, +=) and the value
            op_node = self._find_child(assign_val, "assignment_op")
            op = self.visit(op_node) if op_node else "="
            
            val_node = self._find_child(assign_val, "value")
            val_str = self.visit(val_node)
            
            self.emit(f"{var_name} {op} {val_str}")
        return ""

    # --- 2. Input / Output ---
    def visit_output_statement(self, node):
        out_type = self._find_child(node, "output_type")
        arg = self._find_child(node, "output_arg")
        
        cmd = self.visit(out_type)
        arg_val = self.visit(arg)
        
        # nova -> print(), lumen -> print() 
        self.emit(f"print({arg_val})")
        return ""

    def visit_value(self, node):
        # Handle lumina() input
        if self._has_token(node, "lumina"):
            return "input()"
        return self.generic_visit(node)

    # --- 3. Control Flow ---
    def visit_conditional_statement(self, node):
        cond_node = self._find_child(node, "conditions")
        cond_str = self.visit(cond_node)
        
        self.emit(f"if {cond_str}:")
        self.indent_level += 1
        
        statements = self._find_child(node, "statements")
        if statements and statements.get("children"):
            self.visit(statements)
        else:
            self.emit("pass")
            
        self.indent_level -= 1
        return ""

    # --- 4. Loops ---
    def visit_loop_while_statement(self, node):
        cond_node = self._find_child(node, "conditions")
        cond_str = self.visit(cond_node)
        
        self.emit(f"while {cond_str}:")
        self.indent_level += 1
        
        statements = self._find_child(node, "loop_statements")
        if statements and statements.get("children"):
            self.visit(statements)
        else:
            self.emit("pass")
            
        self.indent_level -= 1
        return ""

    # --- 5. Expressions & Operators ---
    def visit_general_op(self, node):
        op = self._find_token(node, "TOKEN")
        if op:
            val = op["value"]
            if val == "&&" or val == "and": return " and "
            if val == "||" or val == "or": return " or "
            if val == "..": return " + " # String concatenation
            return f" {val} "
        return ""

    def visit_expression(self, node):
        return self.generic_visit(node)

    # --- Utility Methods ---
    def _find_child(self, node, type_name):
        if not node or "children" not in node: return None
        for child in node.get("children", []):
            if child and child.get("type") == type_name: return child
        return None

    def _find_token(self, node, token_type=None):
        if not node or "children" not in node: return None
        for child in node.get("children", []):
            if child and child.get("type") == "TOKEN":
                if not token_type or child.get("token_type") == token_type:
                    return child
        return None

    def _has_token(self, node, value):
        if not node or "children" not in node: return False
        for child in node.get("children", []):
            if child and child.get("type") == "TOKEN" and child.get("value") == value:
                return True
        return False