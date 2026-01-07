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
        self.tokens = [t for t in tokens if t['type'] not in ('WHITESPACE', 'TAB', 'NEWLINE', 'comment')]
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
        """Rule 1: <program> -> <global-dec> <func-dec> <statements>"""
        return ParseNode("Program", children=[
            self.parse_global_dec(),
            self.parse_func_dec(),
            self.parse_statements()
        ])

    # --- Declarations ---

    def parse_global_dec(self):
        children = []
        # Rules 2-5: Global declarations
        declaration_starters = {
            'zeta', 'kai', 'aster', 'flux', 'selene', 'blaze', 'lani', 'let', 'hubble', 'void'
        }
        
        while self.current_token() and self.current_token()['type'] in declaration_starters:
            # Lookahead logic to distinguish Global Vars vs Functions
            ct = self.current_token()
            nt = self.peek_token()
            nnt = self.peek_token(2)

            is_func = False
            # Check if this looks like a function definition: <type> <id> (
            if ct['type'] in declaration_starters:
                if nt and nt['type'] == 'identifier' and nnt and nnt['type'] == '(':
                    is_func = True
            
            if is_func:
                break # Stop global parsing, hand over to parse_func_dec

            children.append(self.parse_dec_and_init())
        
        return ParseNode("GlobalDeclarations", children=children)

    def parse_func_dec(self):
        """Rules 30-33: Function Declarations"""
        children = []
        func_starters = {'void', 'kai', 'aster', 'flux', 'selene', 'blaze', 'lani', 'let'}
        
        while self.current_token() and self.current_token()['type'] in func_starters:
            # Double check it is a function
            nt = self.peek_token()
            nnt = self.peek_token(2)
            if nt and nt['type'] == 'identifier' and nnt and nnt['type'] == '(':
                children.append(self.parse_func_def())
            else:
                break 
        
        return ParseNode("FunctionDeclarations", children=children)

    def parse_dec_and_init(self):
        """Rule 6-8: <dec-and-init>"""
        token = self.current_token()

        if token['type'] == 'hubble':
            return self.parse_table_dec()
        
        if token['type'] == 'identifier':
            return self.parse_assignment_statement()
        
        return self.parse_var_dec()

    def parse_var_dec(self):
        """Rule 9: <var-dec> -> <mutability> <data-type> <var-init>"""
        children = []
        
        # Rule 10: <mutability> -> zeta
        if self.current_token()['type'] == 'zeta':
            children.append(ParseNode("Mutability", value=self.eat('zeta')['value']))
        
        # Rule 12+: <data-type>
        children.append(self.parse_data_type())
        
        # Rule 19: <var-init>
        children.append(self.parse_var_init())
        
        return ParseNode("VariableDeclaration", children=children)

    def parse_data_type(self):
        """Rules 12-18: <data-type>"""
        valid_types = ['kai', 'aster', 'flux', 'selene', 'blaze', 'lani', 'let']
        token = self.current_token()
        if token['type'] in valid_types:
            return ParseNode("DataType", value=self.eat(token['type'])['value'])
        raise Exception(f"Expected data type, got {token['type']}")

    def parse_func_data_type(self):
        """
        Rule 52: <func-data-type> -> <data-type>
        Rule 53: <func-data-type> -> void
        """
        token = self.current_token()
        
        if token['type'] == 'void':
            return ParseNode("FuncDataType", value=self.eat('void')['value'])
        
        # If not void, it must be a standard data type
        # We wrap it in a FuncDataType node to preserve the grammar structure
        return ParseNode("FuncDataType", children=[self.parse_data_type()])

    def parse_var_init(self):
        """Rule 19: identifier <multi-identifiers> <value-init>;"""
        children = []
        
        # 1. Parse Identifiers (left side)
        # First ID
        children.append(ParseNode("Identifier", value=self.eat('identifier')['value']))
        
        # Additional IDs (Rule 20: , identifier ...)
        while self.current_token() and self.current_token()['type'] == ',':
            self.eat(',')
            children.append(ParseNode("Identifier", value=self.eat('identifier')['value']))
        
        # 2. Parse Values (right side)
        # Rule 22: = <value> <value-init-tail>
        if self.current_token()['type'] == '=':
            self.eat('=')
            
            # First Value
            val_children = [self.parse_value()]
            
            # Additional Values (Rule 24: , <value> ...)
            while self.current_token() and self.current_token()['type'] == ',':
                self.eat(',')
                val_children.append(self.parse_value())
                
            children.append(ParseNode("Values", children=val_children))
            
        self.eat(';')
        return ParseNode("VarInitialization", children=children)

    def parse_table_dec(self):
        """Rule 95: hubble <data-type> identifier = { elements };"""
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
        """Rule 51: <func-data-type> identifier (<func-params>) <statements> <func-return> mos"""
        children = []
        
        # UPDATED: Use the specific rule for function return types
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
        """Rule 60: <data-type> identifier"""
        dtype = self.parse_data_type()
        ident = ParseNode("Identifier", value=self.eat('identifier')['value'])
        return ParseNode("Param", children=[dtype, ident])

    def parse_func_return(self):
        """Rule 54: zara <return-val>;"""
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
            return self.parse_input()
        elif t_type in ['nova', 'lumen']:
            return self.parse_output()
        elif t_type == 'leo':
            return self.parse_goto()
        
        elif t_type == 'local':
            self.eat('local')
            # Rule 50: <statements> -> local <dec-and-init>
            # We wrap the result in a "LocalDeclaration" node to preserve scope info
            declaration_node = self.parse_dec_and_init()
            return ParseNode("LocalDeclaration", children=[declaration_node])
            
        elif t_type == ';':
            self.eat(';')
            return ParseNode("EmptyStatement")
        elif t_type == 'identifier':
            next_t = self.peek_token()
            if next_t and next_t['type'] == '(':
                return self.parse_func_call_stmt()
            elif next_t and next_t['type'] == ':':
                 pass
            return self.parse_assignment_statement()
            
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
        self.eat('phase')
        start = self.parse_expression()
        self.eat(',')
        limit = self.parse_expression()
        self.eat(',')
        step = self.parse_expression()
        
        self.eat('cos')
        body = self.parse_statements()
        self.eat('mos')
        
        return ParseNode("ForLoop", children=[start, limit, step, body])

    def parse_repeat_loop(self):
        self.eat('wax')
        body = self.parse_statements()
        self.eat('wane')
        cond = self.parse_expression()
        return ParseNode("RepeatUntil", children=[body, cond])

    # --- I/O ---

    def parse_input(self):
        self.eat('lumina')
        self.eat('(')
        args = []
        if self.current_token()['type'] != ')':
            args.append(ParseNode("Arg", value=self.eat(self.current_token()['type'])['value']))
            while self.current_token()['type'] == ',':
                self.eat(',')
                args.append(ParseNode("Arg", value=self.eat(self.current_token()['type'])['value']))
        self.eat(')')
        return ParseNode("Input", children=args)

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
        """
        Handles two distinct rules that start with identifier:
        1. Rule 27: identifier <multi-identifiers> <assignment-value> ;
           (e.g., a, b = 1, 2;)
        2. Rule 28/101: <table-nav> -> identifier [index] = expression ;
           (e.g., arr[0] = 5;)
        """
        start_token = self.eat('identifier')
        first_id = ParseNode("Identifier", value=start_token['value'])

        # --- PATH A: Table Assignment (Rule 28) ---
        if self.current_token()['type'] == '[':
            target = first_id
            # Handle nested access: arr[x][y]
            while self.current_token()['type'] == '[':
                self.eat('[')
                idx = self.parse_expression()
                self.eat(']')
                target = ParseNode("TableAccess", children=[target, idx])
            
            # Rule 101 strictly specifies '='
            op = '='
            if self.current_token()['value'] == '=':
                self.eat('=')
            else:
                # Fallback for +=, -= if you want to support them loosely, 
                # but strict grammar says <table-nav> only has '='.
                op = self.current_token()['value']
                valid_ops = ['=', '-=', '+=', '*=', '/=', '%=']
                if op in valid_ops:
                    self.eat(self.current_token()['type'])
                else:
                    raise Exception(f"Expected '=', got {op}")

            val = self.parse_expression()
            self.eat(';')
            return ParseNode("Assignment", value=op, children=[target, val])

        # --- PATH B: Variable Assignment (Rule 27) ---
        targets = [first_id]
        
        # Parse extra identifiers: a, b, c ...
        while self.current_token()['type'] == ',':
            self.eat(',')
            targets.append(ParseNode("Identifier", value=self.eat('identifier')['value']))

        # Assignment Operator
        op = self.current_token()['value']
        valid_ops = ['=', '-=', '+=', '*=', '/=', '%=']
        if op in valid_ops:
            self.eat(self.current_token()['type'])
        else:
             raise Exception(f"Expected assignment operator, got {op}")

        # Parse Values
        # Rule 29: <assignment-value> -> <op> <value> <value-init-tail>
        values = []
        values.append(self.parse_expression()) # First value
        
        # Parse tail values: , 10, 20 ...
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
        if self.current_token()['type'] in ['!', 'not']:
            op = self.eat(self.current_token()['type'])['value']
            return ParseNode("UnaryExpr", value=op, children=[self.parse_expr_factor()])
        return self.parse_factor_value()

    def parse_factor_value(self):
        tok = self.current_token()
        t_type = tok['type']

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
        return ['+', '-', '*', '/', '//', '%', '^', '&&', 'and', 'or', '!=', '>', '<', '<=', '>=', '==']