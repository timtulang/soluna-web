# app/parser/parser.py

from app.lexer import token

# =========================================================================
#  PREDICT SETS (Derived from CFG First Sets)
# =========================================================================
PREDICT_SETS = {
    "Program": {
        'zeta', 'kai', 'flux', 'selene', 'blaze', 'lani', 'let', 'identifier',
        '++', '--', 'hubble', 'void', 'orbit', 'wax', ';', 'leo', 'local',
        'sol', 'nova', 'lumen', 'zara', 'label', 'phase'
    },
    "GlobalDec": {
        'zeta', 'kai', 'flux', 'selene', 'blaze', 'lani', 'let',
        'identifier', '++', '--', 'hubble'
    },
    "FuncDec": {
        'void', 'kai', 'flux', 'selene', 'blaze', 'lani', 'let'
    },
    "Statement": {
        'zeta', 'kai', 'flux', 'selene', 'blaze', 'lani', 'let',
        'identifier', '++', '--', 'hubble', 'void', 'orbit', 'wax',
        ';', 'leo', 'local', 'sol', 'nova', 'lumen', 'zara', 'label',
        'phase', 'warp', 'mos', 'wane', 'cos', '}'
    },
    "DataType": {
        'kai', 'flux', 'selene', 'blaze', 'lani', 'let'
    },
    "Value": {
        'lumina', '!', 'not', 'identifier', '(', 'integer',
        'float', 'char', 'string', 'iris', 'sage', '#', '++', '--'
    },
    "AssignmentOp": {'=', '-=', '+=', '*=', '/=', '%='},
    "GeneralOp": {
        '+', '-', '*', '/', '//', '%', '^', '&&', '||', 'and', 'or',
        '!=', '>', '<', '<=', '>=', '==', '..'
    }
}

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
        # Filter out ignorable tokens
        self.tokens = [t for t in tokens if t['type'] not in ('whitespace', 'tab', 'newline', 'comment')]
        self.cursor = 0

    # --- Helper Methods ---

    def current_token(self):
        return self.tokens[self.cursor] if self.cursor < len(self.tokens) else None

    def peek_token(self, offset=1):
        idx = self.cursor + offset
        return self.tokens[idx] if idx < len(self.tokens) else None

    def get_val(self, token):
        """Helper to get the aliased value (identifier1) if present, else original value."""
        return token.get('alias', token['value'])

    def validate_token(self, predict_set_key):
        """
        Checks if the current token exists in the given Predict Set.
        If not, raises a SyntaxError with a helpful message.
        """
        token = self.current_token()
        if not token:
             return False

        valid_tokens = PREDICT_SETS.get(predict_set_key, set())
        
        # Determine effective type for checking (handles literal values vs types)
        t_type = token['type']
        t_val = token['value']
        
        # Check if type matches OR exact value matches (for operators/keywords)
        is_valid = (t_type in valid_tokens) or (t_val in valid_tokens)
        
        if not is_valid:
            # Format the expected tokens for the error message
            expected_str = ", ".join(sorted(list(valid_tokens)))
            raise Exception(
                f"Syntax Error at Line {token['line']}, Col {token['col']}: "
                f"Expected one of [{expected_str}], found '{t_type}' ('{t_val}')"
            )
        return True

    def require_one_of(self, valid_options):
        """
        Checks if the current token matches one of the valid options.
        If not, raises an Exception listing ALL options.
        Used to fix the "Expected ;" issue when "," or "=" were also valid.
        """
        token = self.current_token()
        if not token:
            raise Exception(f"Unexpected End of Input. Expected one of: {valid_options}")

        # Check type or value against options
        if token['type'] in valid_options or token['value'] in valid_options:
            return True
        
        # Format options for display
        opts_str = ", ".join([f"'{opt}'" for opt in valid_options])
        raise Exception(
            f"Syntax Error at Line {token['line']}, Col {token['col']}: "
            f"Expected one of [{opts_str}], found '{token['type']}' ('{token['value']}')"
        )

    def eat(self, expected_type):
        token = self.current_token()
        if not token:
            raise Exception(f"Unexpected End of Input. Expected: {expected_type}")

        if isinstance(expected_type, list) or isinstance(expected_type, set):
            match = token['type'] in expected_type
        else:
            match = token['type'] == expected_type

        if match:
            self.cursor += 1
            return token
        else:
            exp_str = expected_type if isinstance(expected_type, str) else ", ".join(expected_type)
            raise Exception(
                f"Syntax Error at Line {token['line']}, Col {token['col']}: "
                f"Expected '{exp_str}', found '{token['type']}' ('{token['value']}')"
            )

    # =========================================================================
    #  GRAMMAR IMPLEMENTATION
    # =========================================================================

    def parse(self):
        # <program> -> <global-dec> <func-dec> <statements>
        return ParseNode("Program", children=[
            self.parse_global_dec(),
            self.parse_func_dec(),
            self.parse_statements()
        ])

    # --- Declarations ---

    def parse_global_dec(self):
        # <global-dec> -> <dec-and-init> <global-dec-tail> | lambda
        children = []
        
        while self.current_token():
            token = self.current_token()
            t_type = token['type']
            
            if t_type not in PREDICT_SETS['GlobalDec']:
                break

            # LOOKAHEAD: Distinguish Global Var vs Function
            is_func = False
            if t_type in PREDICT_SETS['DataType'] or t_type == 'void':
                nt = self.peek_token(1)
                nnt = self.peek_token(2)
                if nt and nt['type'] == 'identifier' and nnt and nnt['type'] == '(':
                    is_func = True
            
            if is_func:
                break 

            children.append(self.parse_dec_and_init())
        
        return ParseNode("GlobalDeclarations", children=children)

    def parse_func_dec(self):
        children = []
        
        while self.current_token():
            token = self.current_token()
            if token['type'] not in PREDICT_SETS['FuncDec']:
                break
                
            nt = self.peek_token(1)
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
        
        if token['type'] == 'identifier' or token['value'] in ['++', '--']:
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
        self.validate_token('DataType')
        token = self.current_token()
        return ParseNode("DataType", value=self.eat(token['type'])['value'])

    def parse_func_data_type(self):
        token = self.current_token()
        if token['type'] == 'void':
            return ParseNode("FuncDataType", value=self.eat('void')['value'])
        return ParseNode("FuncDataType", children=[self.parse_data_type()])

    def parse_var_init(self):
        # <var-init> -> identifier <multi-identifiers> <value-init>;
        children = []
        tok = self.eat('identifier')
        children.append(ParseNode("Identifier", value=self.get_val(tok)))
        
        # --- FIXED: Validate next token before greedy consumption ---
        # The parser loops on ',' or checks for '='. If neither matches, 
        # it forces ';'. But if the user typed 'identifier identifier', 
        # they likely missed a comma or semicolon. We check ALL valid options here.
        
        # 1. Multi-identifiers loop
        while self.current_token() and self.current_token()['type'] == ',':
            self.eat(',')
            tok = self.eat('identifier')
            children.append(ParseNode("Identifier", value=self.get_val(tok)))
        
        # 2. Value initialization
        if self.current_token()['type'] == '=':
            self.eat('=')
            val_children = [self.parse_value()]
            while self.current_token() and self.current_token()['type'] == ',':
                self.eat(',')
                val_children.append(self.parse_value())
            children.append(ParseNode("Values", children=val_children))
            
        # 3. Final validation before eating ';'
        # At this stage, if we aren't at ';', it means we failed the ',' loop
        # AND the '=' check, so the token is invalid.
        # We explicitly require ';' here, but logic implies we *could* have accepted 
        # ',' or '=' earlier if the token matched.
        # If we just 'eat', it says "Expected ;". 
        # If we fail here, we list what COULD have been valid to aid debugging.
        
        if self.current_token()['type'] != ';':
             self.require_one_of({',', '=', ';'})
             
        self.eat(';')
        return ParseNode("VarInitialization", children=children)

    def parse_table_dec(self):
        self.eat('hubble')
        dtype = self.parse_data_type()
        tok = self.eat('identifier')
        ident = ParseNode("Identifier", value=self.get_val(tok))
        self.eat('=')
        self.eat('{')
        elements = []
        
        if self.current_token()['type'] != '}':
            elements.append(self.parse_hubble_element()) 
            while self.current_token()['type'] == ',':
                self.eat(',')
                elements.append(self.parse_hubble_element())
        
        # Validate table end
        if self.current_token()['type'] != '}':
            self.require_one_of({',', '}'})

        self.eat('}')
        self.eat(';')
        return ParseNode("TableDeclaration", children=[dtype, ident, ParseNode("Elements", children=elements)])

    def parse_hubble_element(self):
        tok = self.current_token()
        potential_keywords = {'void', 'zeta', 'kai', 'aster', 'flux', 'selene', 'blaze', 'lani', 'let'}
        
        if tok['type'] in potential_keywords:
            is_func = False
            if tok['type'] == 'void':
                is_func = True
            elif tok['type'] != 'zeta':
                nt = self.peek_token(1)
                nnt = self.peek_token(2)
                if nt and nt['type'] == 'identifier' and nnt and nnt['type'] == '(':
                    is_func = True
            
            if is_func:
                return self.parse_func_def()
            else:
                return self.parse_var_dec()
        
        return self.parse_expression()

    # --- Functions ---

    def parse_func_def(self):
        children = []
        children.append(self.parse_func_data_type())
        tok = self.eat('identifier')
        children.append(ParseNode("FuncName", value=self.get_val(tok)))
        
        self.eat('(')
        params = []
        if self.current_token()['type'] != ')':
            params.append(self.parse_param())
            while self.current_token()['type'] == ',':
                self.eat(',')
                params.append(self.parse_param())
        children.append(ParseNode("Parameters", children=params))
        
        # Validate function close
        if self.current_token()['type'] != ')':
            self.require_one_of({',', ')'})

        self.eat(')')
        
        children.append(self.parse_statements(stop_tokens={'zara'}))
        children.append(self.parse_func_return())
        
        self.eat('mos') 
        return ParseNode("FunctionDefinition", children=children)

    def parse_param(self):
        dtype = self.parse_data_type()
        tok = self.eat('identifier')
        ident = ParseNode("Identifier", value=self.get_val(tok))
        return ParseNode("Param", children=[dtype, ident])

    def parse_func_return(self):
        self.eat('zara')
        val = None
        if self.current_token()['type'] != ';':
            val = self.parse_expression()
        self.eat(';')
        return ParseNode("ReturnStatement", children=[val] if val else [])

    # --- Statements ---

    def parse_statements(self, stop_tokens=None):
        stmts = []
        block_enders = {'mos', 'wane', 'cos', '}'}
        if stop_tokens:
            block_enders.update(stop_tokens)
        
        while self.current_token():
            tok = self.current_token()
            if tok['type'] in block_enders:
                break
            
            if tok['type'] not in PREDICT_SETS['Statement']:
                # Construct extended expected list including block enders
                valid_set = PREDICT_SETS['Statement'].union(block_enders)
                self.require_one_of(valid_set)
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
        elif t_type == 'zara':
            return self.parse_func_return()
        elif t_type == 'warp':
            self.eat('warp')
            self.eat(';')
            return ParseNode("BreakStatement", value="warp")
        elif t_type in ['nova', 'lumen']:
            return self.parse_output()
        elif t_type == 'lumina':
            node = self.parse_input_expression()
            if self.current_token() and self.current_token()['type'] == ';':
                self.eat(';')
            return ParseNode("ExpressionStatement", children=[node])
        elif t_type == 'leo':
            return self.parse_goto()
        elif t_type == 'label':
            return self.parse_label_dec()
        elif t_type == 'local':
            self.eat('local')
            declaration_node = self.parse_dec_and_init()
            return ParseNode("LocalDeclaration", children=[declaration_node])
        elif t_type == ';':
            self.eat(';')
            return ParseNode("EmptyStatement")
            
        elif t_type == 'identifier':
            next_t = self.peek_token()
            if next_t and next_t['type'] == '(':
                call_node = self.parse_func_call()
                self.eat(';') 
                return ParseNode("ExpressionStatement", children=[call_node])
            elif next_t and next_t['value'] in ['++', '--']:
                return self.parse_assignment_statement()
            return self.parse_assignment_statement()
        
        elif t_type in ['!', 'not'] or tok['value'] in ['++', '--']:
             return self.parse_assignment_statement()

        if t_type in ['zeta', 'kai', 'aster', 'flux', 'selene', 'blaze', 'lani', 'let', 'hubble']:
             return self.parse_dec_and_init()

        self.validate_token('Statement') 

    # --- Control Flow ---

    def parse_conditional(self):
        self.eat('sol')
        cond = self.parse_conditions()
        true_block = self.parse_statements()
        self.eat('mos')
        
        children = [ParseNode("Condition", children=[cond]), ParseNode("TrueBlock", children=[true_block])]
        
        while self.current_token() and self.current_token()['type'] in ['soluna', 'luna']:
            if self.current_token()['type'] == 'soluna':
                self.eat('soluna')
                elif_cond = self.parse_conditions()
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

    def parse_conditions(self):
        if self.current_token()['type'] == '(':
            return self.parse_expression()
        return self.parse_expression()

    def parse_while_loop(self):
        self.eat('orbit')
        cond = self.parse_conditions()
        self.eat('cos')
        body = self.parse_statements()
        self.eat('mos')
        return ParseNode("WhileLoop", children=[cond, body])

    def parse_for_loop(self):
        self.eat('phase')
        has_paren = False
        if self.current_token()['type'] == '(':
            self.eat('(')
            has_paren = True

        self.eat('kai') 
        tok = self.eat('identifier')
        id_val = self.get_val(tok)
        self.eat('=')
        
        init_val = self.parse_expr_factor() 
        
        start_node = ParseNode("ForInit", children=[
            ParseNode("DataType", value="kai"),
            ParseNode("Identifier", value=id_val),
            init_val
        ])
        
        self.eat(',')
        limit = self.parse_expr_factor()
        
        step = None
        if self.current_token()['type'] == ',':
            self.eat(',')
            step = self.parse_expr_factor()
        
        if has_paren:
            self.eat(')')

        self.eat('cos')
        body = self.parse_statements()
        self.eat('mos')
        
        return ParseNode("ForLoop", children=[start_node, limit, step if step else ParseNode("EmptyStep"), body])

    def parse_repeat_loop(self):
        self.eat('wax')
        body = self.parse_statements()
        self.eat('wane')
        cond = self.parse_conditions()
        return ParseNode("RepeatUntil", children=[body, cond])

    # --- I/O ---

    def parse_input_expression(self):
        self.eat('lumina')
        self.eat('(')
        args = []
        if self.current_token()['type'] != ')':
            val = self.parse_expression()
            args.append(val)
            while self.current_token()['type'] == ',':
                self.eat(',')
                args.append(self.parse_expression())
        
        # Validate input close
        if self.current_token()['type'] != ')':
             self.require_one_of({',', ')'})

        self.eat(')')
        return ParseNode("InputExpression", children=args)

    def parse_output(self):
        out_type = self.current_token()['type']
        self.eat(out_type)
        self.eat('(')
        arg = self.parse_expression()
        self.eat(')')
        self.eat(';')
        return ParseNode("Output", value=out_type, children=[arg])

    def parse_goto(self):
        self.eat('leo')
        tok = self.eat('label') 
        self.eat(';')
        return ParseNode("Goto", value=self.get_val(tok))

    def parse_label_dec(self):
        tok = self.eat('label')
        self.eat(';')
        return ParseNode("LabelDec", value=self.get_val(tok))

    # --- Expressions & Assignments ---

    def parse_assignment_statement(self):
        start_token = self.eat('identifier')
        first_id = ParseNode("Identifier", value=self.get_val(start_token))

        if self.current_token()['type'] == '[':
            target = first_id
            while self.current_token()['type'] == '[':
                self.eat('[')
                idx = self.parse_expression()
                self.eat(']')
                target = ParseNode("TableAccess", children=[target, idx])
            
            if self.current_token()['value'] in ['++', '--']:
                op = self.eat(self.current_token()['type'])['value']
                self.eat(';')
                return ParseNode("UnaryStatement", value="postfix", children=[target, ParseNode("Operator", value=op)])

            op_node = self.parse_assignment_op()
            val = self.parse_expression()
            self.eat(';')
            return ParseNode("Assignment", value=op_node.value, children=[target, val])

        targets = [first_id]
        while self.current_token()['type'] == ',':
            self.eat(',')
            tok = self.eat('identifier')
            targets.append(ParseNode("Identifier", value=self.get_val(tok)))

        if self.current_token()['value'] in ['++', '--']:
             op = self.eat(self.current_token()['type'])['value']
             self.eat(';')
             return ParseNode("UnaryStatement", value="postfix", children=[ParseNode("Targets", children=targets), ParseNode("Operator", value=op)])
        
        op_node = self.parse_assignment_op()

        values = []
        values.append(self.parse_value()) 
        while self.current_token()['type'] == ',':
            self.eat(',')
            values.append(self.parse_value())

        self.eat(';')
        return ParseNode("Assignment", value=op_node.value, children=[
            ParseNode("Targets", children=targets),
            ParseNode("Values", children=values)
        ])

    def parse_assignment_op(self):
        tok = self.current_token()
        if tok['value'] in PREDICT_SETS['AssignmentOp']:
            self.eat(tok['type'])
            return ParseNode("Op", value=tok['value'])
        
        self.validate_token('AssignmentOp')

    def parse_func_call(self):
        tok = self.eat('identifier')
        name = self.get_val(tok)
        self.eat('(')
        args = []
        if self.current_token()['type'] != ')':
            args.append(self.parse_expression())
            while self.current_token()['type'] == ',':
                self.eat(',')
                args.append(self.parse_expression())
        
        # Validate call close
        if self.current_token()['type'] != ')':
            self.require_one_of({',', ')'})

        self.eat(')')
        return ParseNode("FunctionCall", value=name, children=args)

    def parse_expression(self):
        return self.parse_simple_expr()

    def parse_simple_expr(self):
        left = self.parse_expr_factor()
        while self.current_token() and self.current_token()['value'] in PREDICT_SETS['GeneralOp']:
            op = self.current_token()['value']
            self.eat(self.current_token()['type'])
            right = self.parse_expr_factor()
            left = ParseNode("BinaryExpr", value=op, children=[left, right])
        return left

    def parse_expr_factor(self):
        tok = self.current_token()
        if tok['type'] in ['!', 'not']:
            op = tok['value']
            self.eat(tok['type'])
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
                ident = ParseNode("Identifier", value=self.get_val(self.eat('identifier')))
                node = ident
                while self.current_token()['type'] == '[':
                    self.eat('[')
                    idx = self.parse_expression()
                    self.eat(']')
                    node = ParseNode("TableAccess", children=[node, idx])
                
                if self.current_token()['value'] in ['++', '--']:
                    op = self.eat(self.current_token()['type'])['value']
                    return ParseNode("UnaryExpr", value="postfix " + op, children=[node])
                return node
            
            if nt and nt['value'] in ['++', '--']:
                ident = ParseNode("Identifier", value=self.get_val(self.eat('identifier')))
                op = self.eat(self.current_token()['type'])['value']
                return ParseNode("UnaryExpr", value="postfix " + op, children=[ident])

            return ParseNode("Identifier", value=self.get_val(self.eat('identifier')))

        elif t_type in ['int', 'float', 'double', 'char', 'string', 'iris', 'sage']:
            return ParseNode("Literal", value=self.eat(t_type)['value'])
            
        elif t_type == 'lumina':
            return self.parse_input_expression()

        elif t_type == '(':
            self.eat('(')
            node = self.parse_expression()
            self.eat(')')
            return node
            
        self.validate_token('Value')

    def parse_value(self):
        return self.parse_expression()