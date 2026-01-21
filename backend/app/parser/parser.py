# app/parser/parser.py

class ParseNode:
    def __init__(self, node_type, value=None, children=None):
        self.type = node_type
        self.value = value
        self.children = children if children is not None else []

    def to_dict(self):
        return {
            "type": self.type,
            "value": self.value,
            "children": [child.to_dict() for child in self.children]
        }

class Parser:
    def __init__(self, tokens):
        # Filter whitespace/comments
        self.tokens = [t for t in tokens if t['type'] not in ('whitespace', 'tab', 'newline', 'comment')]
        self.cursor = 0

    def current_token(self):
        return self.tokens[self.cursor] if self.cursor < len(self.tokens) else None

    def peek_token(self, offset=1):
        idx = self.cursor + offset
        return self.tokens[idx] if idx < len(self.tokens) else None

    def eat(self, expected_type):
        token = self.current_token()
        if not token:
            raise Exception(f"Unexpected End of Input. Expected: {expected_type}")

        if isinstance(expected_type, list):
            match = token['type'] in expected_type
        else:
            match = token['type'] == expected_type

        if match:
            self.cursor += 1
            return token
        else:
            raise Exception(
                f"Syntax Error at Line {token['line']}: Expected '{expected_type}', found '{token['type']}' ('{token['value']}')"
            )

    # =========================================================================
    #  GRAMMAR IMPLEMENTATION
    # =========================================================================

    def parse(self):
        return ParseNode("Program", children=[
            self.parse_global_dec(),
            self.parse_func_dec(),
            self.parse_statements()
        ])

    # --- Declarations ---

    def parse_global_dec(self):
        children = []
        declaration_starters = {
            'zeta', 'kai', 'aster', 'flux', 'selene', 'blaze', 'lani', 'let', 'hubble', 'void'
        }
        
        while self.current_token() and self.current_token()['type'] in declaration_starters:
            ct = self.current_token()
            nt = self.peek_token()
            nnt = self.peek_token(2)

            is_func = False
            # Check for function definition pattern: type identifier (
            if ct['type'] in declaration_starters:
                if nt and nt['type'] == 'identifier' and nnt and nnt['type'] == '(':
                    is_func = True
            
            if is_func:
                break 

            children.append(self.parse_dec_and_init())
        
        return ParseNode("GlobalDeclarations", children=children)

    def parse_func_dec(self):
        children = []
        func_starters = {'void', 'kai', 'aster', 'flux', 'selene', 'blaze', 'lani', 'let'}
        
        while self.current_token() and self.current_token()['type'] in func_starters:
            nt = self.peek_token()
            nnt = self.peek_token(2)
            if nt and nt['type'] == 'identifier' and nnt and nnt['type'] == '(':
                children.append(self.parse_func_def())
            else:
                break 
        
        return ParseNode("FunctionDeclarations", children=children)

    def parse_dec_and_init(self):
        token = self.current_token()

        if token['type'] == 'hubble':
            return self.parse_table_dec()
        
        if token['type'] == 'identifier':
            return self.parse_assignment_statement()
        
        return self.parse_var_dec()

    def parse_var_dec(self):
        children = []
        if self.current_token()['type'] == 'zeta':
            children.append(ParseNode("Mutability", value=self.eat('zeta')['value']))
        children.append(self.parse_data_type())
        children.append(self.parse_var_init())
        return ParseNode("VariableDeclaration", children=children)

    def parse_data_type(self):
        valid_types = ['kai', 'aster', 'flux', 'selene', 'blaze', 'lani', 'let']
        token = self.current_token()
        if token['type'] in valid_types:
            return ParseNode("DataType", value=self.eat(token['type'])['value'])
        raise Exception(f"Expected data type, got {token['type']}")

    def parse_func_data_type(self):
        token = self.current_token()
        if token['type'] == 'void':
            return ParseNode("FuncDataType", value=self.eat('void')['value'])
        return ParseNode("FuncDataType", children=[self.parse_data_type()])

    def parse_var_init(self):
        children = []
        children.append(ParseNode("Identifier", value=self.eat('identifier')['value']))
        
        while self.current_token() and self.current_token()['type'] == ',':
            self.eat(',')
            children.append(ParseNode("Identifier", value=self.eat('identifier')['value']))
        
        if self.current_token()['type'] == '=':
            self.eat('=')
            val_children = [self.parse_value()]
            while self.current_token() and self.current_token()['type'] == ',':
                self.eat(',')
                val_children.append(self.parse_value())
            children.append(ParseNode("Values", children=val_children))
            
        self.eat(';')
        return ParseNode("VarInitialization", children=children)

    def parse_table_dec(self):
        self.eat('hubble')
        dtype = self.parse_data_type()
        ident = ParseNode("Identifier", value=self.eat('identifier')['value'])
        self.eat('=')
        self.eat('{')
        elements = []
        if self.current_token()['type'] != '}':
            elements.append(self.parse_expression()) 
            while self.current_token()['type'] == ',':
                self.eat(',')
                elements.append(self.parse_expression())
        self.eat('}')
        self.eat(';')
        return ParseNode("TableDeclaration", children=[dtype, ident, ParseNode("Elements", children=elements)])

    # --- Functions ---

    def parse_func_def(self):
        children = []
        children.append(self.parse_func_data_type())
        children.append(ParseNode("FuncName", value=self.eat('identifier')['value']))
        
        self.eat('(')
        params = []
        if self.current_token()['type'] != ')':
            params.append(self.parse_param())
            while self.current_token()['type'] == ',':
                self.eat(',')
                params.append(self.parse_param())
        children.append(ParseNode("Parameters", children=params))
        self.eat(')')
        
        children.append(self.parse_statements())
        children.append(self.parse_func_return())
        
        self.eat('mos') 
        return ParseNode("FunctionDefinition", children=children)

    def parse_param(self):
        dtype = self.parse_data_type()
        ident = ParseNode("Identifier", value=self.eat('identifier')['value'])
        return ParseNode("Param", children=[dtype, ident])

    def parse_func_return(self):
        self.eat('zara')
        val = None
        if self.current_token()['type'] != ';':
            val = self.parse_expression()
        self.eat(';')
        return ParseNode("ReturnStatement", children=[val] if val else [])

    # --- Statements ---

    def parse_statements(self):
        stmts = []
        block_enders = {'mos', 'wane', 'cos'}
        while self.current_token():
            tok = self.current_token()
            if tok['type'] in block_enders:
                break
            if tok['type'] == 'zara':
                break 
            stmts.append(self.parse_single_statement())
        return ParseNode("Block", children=stmts)

    def parse_single_statement(self):
        tok = self.current_token()
        t_type = tok['type']

        if t_type == 'sol':
            return self.parse_conditional()
        elif t_type == 'orbit':
            return self.parse_while_loop()
        elif t_type == 'phase':
            return self.parse_for_loop()
        elif t_type == 'wax':
            return self.parse_repeat_loop()
        elif t_type == 'lumina':
            node = self.parse_input_expression()
            if self.current_token() and self.current_token()['type'] == ';':
                self.eat(';')
            return ParseNode("ExpressionStatement", children=[node])
        elif t_type in ['nova', 'lumen']:
            return self.parse_output()
        elif t_type == 'leo':
            return self.parse_goto()
        elif t_type == 'local':
            self.eat('local')
            declaration_node = self.parse_dec_and_init()
            return ParseNode("LocalDeclaration", children=[declaration_node])
        elif t_type == ';':
            self.eat(';')
            return ParseNode("EmptyStatement")
            
        elif t_type == 'identifier':
            next_t = self.peek_token()
            
            # Function Call: id(...)
            if next_t and next_t['type'] == '(':
                return self.parse_func_call_stmt()
                
            # Postfix Unary Start (i++ ...) handled via expression parsing
            elif next_t and next_t['value'] in ['++', '--']:
                expr = self.parse_expression()
                self.eat(';')
                return ParseNode("ExpressionStatement", children=[expr])
            
            return self.parse_assignment_statement()
        
        # Prefix Unary as statement: ++id;
        elif t_type in ['!', 'not'] or tok['value'] in ['++', '--']:
             expr = self.parse_expression()
             self.eat(';')
             return ParseNode("ExpressionStatement", children=[expr])

        if t_type in ['zeta', 'kai', 'aster', 'flux', 'selene', 'blaze', 'lani', 'let', 'hubble']:
             return self.parse_dec_and_init()

        raise Exception(f"Unknown statement starting with {t_type}")

    # --- Control Flow ---

    def parse_conditional(self):
        self.eat('sol')
        cond = self.parse_expression()
        true_block = self.parse_statements()
        self.eat('mos')
        
        children = [ParseNode("Condition", children=[cond]), ParseNode("TrueBlock", children=[true_block])]
        
        while self.current_token() and self.current_token()['type'] in ['soluna', 'luna']:
            if self.current_token()['type'] == 'soluna':
                self.eat('soluna')
                elif_cond = self.parse_expression()
                elif_block = self.parse_statements()
                self.eat('mos')
                children.append(ParseNode("ElseIf", children=[elif_cond, elif_block]))
            elif self.current_token()['type'] == 'luna':
                self.eat('luna')
                else_block = self.parse_statements()
                self.eat('mos')
                children.append(ParseNode("Else", children=[else_block]))
                break
        return ParseNode("IfStatement", children=children)

    def parse_while_loop(self):
        self.eat('orbit')
        cond = self.parse_expression()
        self.eat('cos')
        body = self.parse_statements()
        self.eat('mos')
        return ParseNode("WhileLoop", children=[cond, body])

    def parse_for_loop(self):
        """
        Rule 141: phase <for-loop-params> cos <statements> mos
        Rule 155: <for-loop-params> -> <for_start> <for_limit> <for_step>
        Rule 157: <for_start> -> kai identifier = <expr-factor>
        """
        self.eat('phase')
        
        # --- Start Clause (Strict Rule 157) ---
        self.eat('kai') # Enforce 'kai'
        id_token = self.eat('identifier')
        self.eat('=')
        init_val = self.parse_expression() # Parses the value
        
        start_node = ParseNode("ForInit", children=[
            ParseNode("DataType", value="kai"),
            ParseNode("Identifier", value=id_token['value']),
            init_val
        ])
        
        # --- Limit Clause ---
        self.eat(',')
        limit = self.parse_expression()
        
        # --- Step Clause ---
        self.eat(',')
        step = self.parse_expression()
        
        self.eat('cos')
        body = self.parse_statements()
        self.eat('mos')
        
        return ParseNode("ForLoop", children=[start_node, limit, step, body])

    def parse_repeat_loop(self):
        self.eat('wax')
        body = self.parse_statements()
        self.eat('wane')
        cond = self.parse_expression()
        return ParseNode("RepeatUntil", children=[body, cond])

    # --- I/O ---

    def parse_input_expression(self):
        self.eat('lumina')
        self.eat('(')
        args = []
        if self.current_token()['type'] != ')':
            args.append(ParseNode("Arg", value=self.eat(self.current_token()['type'])['value']))
            while self.current_token()['type'] == ',':
                self.eat(',')
                args.append(ParseNode("Arg", value=self.eat(self.current_token()['type'])['value']))
        self.eat(')')
        return ParseNode("InputExpression", children=args)

    def parse_output(self):
        out_type = self.current_token()['type']
        self.eat(out_type)
        self.eat('(')
        arg = self.parse_expression()
        self.eat(')')
        return ParseNode("Output", value=out_type, children=[arg])

    def parse_goto(self):
        self.eat('leo')
        target = self.eat('identifier') 
        self.eat(';')
        return ParseNode("Goto", value=target['value'])

    # --- Expressions & Assignments ---

    def parse_assignment_statement(self):
        start_token = self.eat('identifier')
        first_id = ParseNode("Identifier", value=start_token['value'])

        # Path A: Table Assignment
        if self.current_token()['type'] == '[':
            target = first_id
            while self.current_token()['type'] == '[':
                self.eat('[')
                idx = self.parse_expression()
                self.eat(']')
                target = ParseNode("TableAccess", children=[target, idx])
            
            op = '='
            if self.current_token()['value'] == '=':
                self.eat('=')
            else:
                op = self.current_token()['value']
                valid_ops = ['=', '-=', '+=', '*=', '/=', '%=']
                if op in valid_ops:
                    self.eat(self.current_token()['type'])
                else:
                    raise Exception(f"Expected '=', got {op}")

            val = self.parse_expression()
            self.eat(';')
            return ParseNode("Assignment", value=op, children=[target, val])

        # Path B: Variable Assignment
        targets = [first_id]
        while self.current_token()['type'] == ',':
            self.eat(',')
            targets.append(ParseNode("Identifier", value=self.eat('identifier')['value']))

        op = self.current_token()['value']
        valid_ops = ['=', '-=', '+=', '*=', '/=', '%=']
        if op in valid_ops:
            self.eat(self.current_token()['type'])
        else:
             raise Exception(f"Expected assignment operator, got {op}")

        values = []
        values.append(self.parse_expression()) 
        while self.current_token()['type'] == ',':
            self.eat(',')
            values.append(self.parse_expression())

        self.eat(';')
        return ParseNode("Assignment", value=op, children=[
            ParseNode("Targets", children=targets),
            ParseNode("Values", children=values)
        ])

    def parse_func_call_stmt(self):
        call_node = self.parse_func_call()
        if self.current_token() and self.current_token()['type'] == ';':
            self.eat(';')
        return call_node

    def parse_func_call(self):
        name = self.eat('identifier')['value']
        self.eat('(')
        args = []
        if self.current_token()['type'] != ')':
            args.append(self.parse_expression())
            while self.current_token()['type'] == ',':
                self.eat(',')
                args.append(self.parse_expression())
        self.eat(')')
        return ParseNode("FunctionCall", value=name, children=args)

    def parse_expression(self):
        return self.parse_simple_expr()

    def parse_simple_expr(self):
        left = self.parse_expr_factor()
        while self.current_token() and self.current_token()['value'] in self.get_general_ops():
            op = self.current_token()['value']
            self.eat(self.current_token()['type'])
            right = self.parse_expr_factor()
            left = ParseNode("BinaryExpr", value=op, children=[left, right])
        return left

    def parse_expr_factor(self):
        tok = self.current_token()
        if tok['type'] in ['!', 'not'] or tok['value'] in ['++', '--']:
            op = tok['value']
            self.eat(tok['type'])
            return ParseNode("UnaryExpr", value=op, children=[self.parse_expr_factor()])
        return self.parse_factor_value()

    def parse_factor_value(self):
        tok = self.current_token()
        t_type = tok['type']

        if t_type == 'lumina':
            return self.parse_input_expression()

        if t_type == 'identifier':
            nt = self.peek_token()
            if nt and nt['type'] == '(':
                return self.parse_func_call()
            elif nt and nt['type'] == '[':
                ident = ParseNode("Identifier", value=self.eat('identifier')['value'])
                self.eat('[')
                idx = self.parse_expression()
                self.eat(']')
                return ParseNode("TableAccess", children=[ident, idx])
            
            # Postfix check inside expression (e.g. x = i++ + 1)
            if nt and nt['value'] in ['++', '--']:
                ident = ParseNode("Identifier", value=self.eat('identifier')['value'])
                op = self.eat(self.current_token()['type'])['value']
                return ParseNode("UnaryExpr", value="postfix " + op, children=[ident])

            return ParseNode("Identifier", value=self.eat('identifier')['value'])

        elif t_type in ['int', 'float', 'double', 'char', 'string', 'iris', 'sage']:
            return ParseNode("Literal", value=self.eat(t_type)['value'])
            
        elif t_type == '(':
            self.eat('(')
            node = self.parse_expression()
            self.eat(')')
            return node
            
        raise Exception(f"Unexpected token in expression: {tok['value']}")

    def parse_value(self):
        return self.parse_expression()

    def get_general_ops(self):
        return ['+', '-', '*', '/', '//', '%', '^', '&&', 'and', 'or', '!=', '>', '<', '<=', '>=', '==', '..']