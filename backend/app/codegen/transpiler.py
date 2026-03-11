class PythonTranspiler:
    def __init__(self):
        self.indent_level = 0
        self.code = []
        self.symbol_table = {}

    def emit(self, line):
        indent = "    " * self.indent_level
        self.code.append(f"{indent}{line}")

    def generate(self, tree):
        preamble = [
            "def __soluna_input(expected_type):",
            "    val = input()",
            "    try:",
            "        if expected_type == 'kai': return int(val)",
            "        if expected_type in ['flux', 'selene']: return float(val)",
            "        if expected_type == 'lani':",
            "            if val not in ['iris', 'sage']:",
            "                raise ValueError",
            "            return val == 'iris'",
            "        return val",
            "    except ValueError:",
            "        raise RuntimeError(f\"Runtime Error: Invalid input '{val}' for type {expected_type}\")",
            ""
        ]
        self.code = preamble + self.code
        self.visit(tree)
        return "\n".join(self.code)

    def visit(self, node):
        if not node: return ""
        if isinstance(node, dict) and node.get("type") == "TOKEN":
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

    def _cast_lumina(self, var_name, base_val):
        if base_val != "input()":
            return base_val
        var_type = self.symbol_table.get(var_name, "let")
        return f"__soluna_input('{var_type}')"

    # --- Flattening Logic for Expressions ---
    
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
            
        # Coerce both sides of the `..` operator to strings
        while ".." in parts:
            idx = parts.index("..")
            left = parts[idx-1]
            right = parts[idx+1]
            combined = f"(str({left}) + str({right}))"
            parts[idx-1:idx+2] = [combined]
            
        py_parts = []
        for p in parts:
            if p in ["&&", "and"]: py_parts.append("and")
            elif p in ["||", "or"]: py_parts.append("or")
            else: py_parts.append(p)
            
        return " ".join(py_parts)

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
        
        first_operand = f"{unary_str}({expr_str})"
        
        tail_node = self._find_child(node, "expr_tail")
        return self._flatten_and_build_expr(first_operand, tail_node)

    # ----------------------------------------

    def visit_unary_negation(self, node):
        if not node or "children" not in node: 
            return ""
        
        results = []
        for child in node["children"]:
            if child.get("type") == "TOKEN":
                val = child.get("value")
                # Translate both '!' and 'not' to a clean 'not ' with a trailing space
                if val in ["!", "not"]:
                    results.append("not ")
            else:
                results.append(self.visit(child))
                
        return "".join(results)

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
            val_str = self.visit(init_node).strip()
            if val_str.startswith("="):
                val_str = val_str[1:].strip()
            if val_str:
                val_str = self._cast_lumina(var_name, val_str)
                self.emit(f"{var_name} = {val_str}")
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
            val_str = self.visit(val_node).strip()
            val_str = self._cast_lumina(var_name, val_str)
            self.emit(f"{var_name} {op} {val_str}")
        elif unary_op:
            op_token = self._find_token(unary_op)
            if op_token:
                if op_token["value"] == "++":
                    self.emit(f"{var_name} += 1")
                elif op_token["value"] == "--":
                    self.emit(f"{var_name} -= 1")
        return ""

    def visit_output_statement(self, node):
        out_type_node = self._find_child(node, "output_type")
        out_type = self.visit(out_type_node).strip()
        arg = self._find_child(node, "output_arg")
        arg_val = self.visit(arg).strip()
        if out_type == "nova":
            self.emit(f"print({arg_val}, end='')")
        else:
            self.emit(f"print({arg_val})")
        return ""

    def visit_value(self, node):
        if self._has_token(node, "lumina"):
            return "input()"
        return self.generic_visit(node)

    def visit_conditional_statement(self, node):
        cond_node = self._find_child(node, "conditions")
        cond_str = self.visit(cond_node)
        self.emit(f"if {cond_str}:")
        self.indent_level += 1
        statements = self._find_child(node, "statements") or self._find_child(node, "loop_statements")
        if statements and statements.get("children"):
            self.visit(statements)
        else:
            self.emit("pass")
        self.indent_level -= 1
        tail = self._find_child(node, "conditional_tail") or self._find_child(node, "conditional_tail_in_loop")
        if tail:
            self.visit(tail)
        return ""

    def visit_conditional_statement_in_loop(self, node):
        return self.visit_conditional_statement(node)

    def visit_ifelse(self, node):
        cond_node = self._find_child(node, "conditions")
        cond_str = self.visit(cond_node)
        self.emit(f"elif {cond_str}:")
        self.indent_level += 1
        statements = self._find_child(node, "statements") or self._find_child(node, "loop_statements")
        if statements and statements.get("children"):
            self.visit(statements)
        else:
            self.emit("pass")
        self.indent_level -= 1
        return ""

    def visit_ifelse_in_loop(self, node):
        return self.visit_ifelse(node)

    def visit_else(self, node):
        self.emit("else:")
        self.indent_level += 1
        statements = self._find_child(node, "statements") or self._find_child(node, "loop_statements")
        if statements and statements.get("children"):
            self.visit(statements)
        else:
            self.emit("pass")
        self.indent_level -= 1
        return ""

    def visit_else_in_loop(self, node):
        return self.visit_else(node)

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

    def visit_loop_for_statement(self, node):
        params = self._find_child(node, "for_loop_params")
        if params:
            start_node = self._find_child(params, "for_start")
            limit_node = self._find_child(params, "for_limit")
            step_node = self._find_child(params, "for_step")
            ident = self._find_token(start_node, "identifier")
            var_name = ident["value"] if ident else "i"
            start_factor = self._find_child(start_node, "expr_factor")
            start_val = self.visit(start_factor).strip() if start_factor else "0"
            limit_factor = self._find_child(limit_node, "expr_factor")
            limit_val = self.visit(limit_factor).strip() if limit_factor else "0"
            step_factor = self._find_child(step_node, "expr_factor")
            step_val = self.visit(step_factor).strip() if step_factor else "1"
            self.emit(f"for {var_name} in range({start_val}, {limit_val}, {step_val}):")
            self.indent_level += 1
            statements = self._find_child(node, "loop_statements")
            if statements and statements.get("children"):
                self.visit(statements)
            else:
                self.emit("pass")
            self.indent_level -= 1
        return ""

    def visit_func_def(self, node):
        ident_node = self._find_token(node, "identifier")
        if not ident_node: return ""
        func_name = ident_node["value"]
        params_node = self._find_child(node, "func_params")
        params_str = self.visit(params_node) if params_node else ""
        self.emit(f"def {func_name}({params_str}):")
        self.indent_level += 1
        statements = self._find_child(node, "statements")
        if statements and statements.get("children"):
            self.visit(statements)
        else:
            self.emit("pass")
        self.indent_level -= 1
        return ""

    def visit_param(self, node):
        ident = self._find_token(node, "identifier")
        return ident["value"] if ident else ""

    def visit_param_tail(self, node):
        res = ""
        for child in node.get("children", []):
            if child.get("type") == "TOKEN" and child.get("value") == ",":
                res += ", "
            else:
                res += self.visit(child)
        return res

    def visit_func_call(self, node):
        ident = self._find_token(node, "identifier")
        args = self._find_child(node, "func_call_args")
        func_name = ident["value"] if ident else ""
        args_str = self.visit(args) if args else ""
        self.emit(f"{func_name}({args_str})")
        return ""

    def visit_func_call_in_expr(self, node):
        ident = self._find_token(node, "identifier")
        args = self._find_child(node, "func_call_args")
        func_name = ident["value"] if ident else ""
        args_str = self.visit(args) if args else ""
        return f"{func_name}({args_str})"

    def visit_func_call_args_tail(self, node):
        res = ""
        for child in node.get("children", []):
            if child.get("type") == "TOKEN" and child.get("value") == ",":
                res += ", "
            else:
                res += self.visit(child)
        return res

    def visit_func_return(self, node):
        val_node = self._find_child(node, "return_val")
        val_str = self.visit(val_node).strip()
        if val_str:
            self.emit(f"return {val_str}")
        else:
            self.emit("return")
        return ""

    def visit_table_dec(self, node):
        ident = self._find_token(node, "identifier")
        if not ident: return ""
        var_name = ident["value"]
        elements = self._find_child(node, "hubble_elements")
        tail = self._find_child(node, "hubble_element_tail")
        elems_str = self.visit(elements) if elements else ""
        tail_str = self.visit(tail) if tail else ""
        self.emit(f"{var_name} = [{elems_str}{tail_str}]")
        return ""

    def visit_hubble_element_tail(self, node):
        res = ""
        for child in node.get("children", []):
            if child.get("type") == "TOKEN" and child.get("value") == ",":
                res += ", "
            else:
                res += self.visit(child)
        return res

    def visit_table_nav(self, node):
        ident = self._find_token(node, "identifier")
        if not ident: return ""
        var_name = ident["value"]
        idx_node = self._find_child(node, "table_index")
        tail_node = self._find_child(node, "nav_tail")
        idx_str = self.visit(idx_node) if idx_node else ""
        tail_str = self.visit(tail_node) if tail_node else ""
        expr = self._find_child(node, "expression")
        expr_str = self.visit(expr) if expr else ""
        self.emit(f"{var_name}{idx_str}{tail_str} = {expr_str}")
        return ""

    def visit_table_index(self, node):
        idx_val = self._find_child(node, "index_val")
        val_str = self.visit(idx_val)
        return f"[{val_str}]"

    def visit_string_or_table_len(self, node):
        ident = self._find_token(node, "identifier")
        if ident:
            return f"len({ident['value']})"
        return ""

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