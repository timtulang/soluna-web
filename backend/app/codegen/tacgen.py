class TACGenerator:
    def __init__(self):
        self.code = []
        self.temp_count = 0
        self.label_count = 0
        self.symbol_table = {}

    def new_temp(self):
        name = f"t{self.temp_count}"
        self.temp_count += 1
        return name

    def new_label(self):
        name = f"L{self.label_count}"
        self.label_count += 1
        return name

    def emit(self, instruction):
        self.code.append(instruction)

    def generate(self, tree):
        self.visit(tree)
        return "\n".join(self.code)

    def visit(self, node, *args, **kwargs):
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
        if not node or "children" not in node: return ""
        results = []
        for child in node["children"]:
            res = self.visit(child, *args, **kwargs)
            if res: results.append(res)
        return "".join(results)

    # --- Expression Logic ---
    
    def _flatten_and_build_expr(self, first_operand_str, tail_node):
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
            
            # Standardize logic/concat operators
            if op in ["&&", "and"]: op = "AND"
            elif op in ["||", "or"]: op = "OR"
            elif op == "..": op = "CONCAT"
                
            temp = self.new_temp()
            self.emit(f"{temp} = {result} {op} {right}")
            result = temp
            
        return result

    def visit_simple_expr(self, node):
        factor_node = self._find_child(node, "expr_factor")
        factor_str = self.visit(factor_node)
        tail_node = self._find_child(node, "expr_tail")
        return self._flatten_and_build_expr(factor_str, tail_node)

    def visit_multi_expr(self, node):
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

    # --- Statements ---

    def visit_var_dec(self, node):
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
        arg = self._find_child(node, "output_arg")
        arg_temp = self.visit(arg)
        self.emit(f"param {arg_temp}")
        self.emit("call print, 1")
        return ""

    def visit_value(self, node):
        if self._has_token(node, "lumina"):
            temp = self.new_temp()
            self.emit(f"{temp} = call input, 0")
            return temp
            
        # If it's a simple value, generic_visit will find the token and return it
        val = self.generic_visit(node)
        return val

    # --- Control Flow ---

    def visit_conditional_statement(self, node, end_label=None):
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
        return self.visit_conditional_statement(node)

    def visit_ifelse(self, node, end_label=None):
        return self.visit_conditional_statement(node, end_label=end_label)

    def visit_ifelse_in_loop(self, node, end_label=None):
        return self.visit_ifelse(node, end_label=end_label)

    def visit_else(self, node, end_label=None):
        statements = self._find_child(node, "statements") or self._find_child(node, "loop_statements")
        if statements: self.visit(statements)
        return ""

    def visit_else_in_loop(self, node, end_label=None):
        return self.visit_else(node, end_label=end_label)

    def visit_loop_while_statement(self, node):
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
        ident_node = self._find_token(node, "identifier")
        if not ident_node: return ""
        func_name = ident_node["value"]
        
        self.emit(f"func {func_name}:")
        
        # In a real TAC compiler, you'd pull parameters into local scope here
        
        statements = self._find_child(node, "statements")
        if statements: self.visit(statements)
            
        self.emit(f"endfunc")
        return ""

    def visit_func_call(self, node):
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
        return self.visit_func_call(node)

    def visit_func_call_args_tail(self, node):
        args = []
        for child in node.get("children", []):
            if child.get("type") == "expression":
                args.append(self.visit(child))
        return args

    def visit_func_return(self, node):
        val_node = self._find_child(node, "return_val")
        val_temp = self.visit(val_node)
        if val_temp:
            self.emit(f"return {val_temp}")
        else:
            self.emit("return")
        return ""

    # --- Helpers ---
    
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