# app/parser/lark_parser.py
from lark import Lark, Transformer, v_args, Token, exceptions
from lark.lexer import Lexer as LarkLexer

# =========================================================================
#  1. TERMINAL NAME MAPPING (For Pretty Error Messages)
# =========================================================================
TERMINAL_NAMES = {
    # Keywords (Lowercase)
    'ZETA': 'zeta', 'KAI': 'kai', 'FLUX': 'flux', 'SELENE': 'selene',
    'BLAZE': 'blaze', 'LANI': 'lani', 'LET': 'let', 'VOID': 'void',
    'HUBBLE': 'hubble', 'ORBIT': 'orbit', 'WAX': 'wax', 'WARP': 'warp',
    'MOS': 'mos', 'WANE': 'wane', 'COS': 'cos', 'SOL': 'sol',
    'SOLUNA': 'soluna', 'LUNA': 'luna', 'NOVA': 'nova', 'LUMEN': 'lumen',
    'LUMINA': 'lumina', 'LEO': 'leo', 'LOCAL': 'local', 'ZARA': 'zara',
    'PHASE': 'phase', 'IRIS': 'iris', 'SAGE': 'sage',
    'AND_WORD': 'and', 'OR_WORD': 'or', 'NOT': 'not',
    
    # Literals
    'IDENTIFIER': 'identifier', 'LABEL': 'label',
    'INT_LIT': 'int_lit', 'FLOAT_LIT': 'float_lit', 
    'STRING_LIT': 'string_lit', 'CHAR_LIT': 'char_lit',

    # Symbols (Display as symbols)
    'PLUS': '+', 'MINUS': '-', 'STAR': '*', 'SLASH': '/', 'DSLASH': '//',
    'MOD': '%', 'CARET': '^',
    'ASSIGN': '=', 'PLUSEQ': '+=', 'MINUSEQ': '-=', 'MULEQ': '*=',
    'DIVEQ': '/=', 'MODEQ': '%=',
    'EQ': '==', 'NEQ': '!=', 'GT': '>', 'LT': '<', 'GTE': '>=', 'LTE': '<=',
    'AND': '&&', 'OR': '||', 'EXCLAM': '!',
    'PLUSPLUS': '++', 'MINUSMINUS': '--', 'CONCAT': '..',
    'LPAREN': '(', 'RPAREN': ')', 'LBRACE': '{', 'RBRACE': '}',
    'LBRACKET': '[', 'RBRACKET': ']',
    'COMMA': ',', 'SEMICOLON': ';'
}

# =========================================================================
#  2. GRAMMAR DEFINITION
# =========================================================================
SOLUNA_GRAMMAR = r"""
    start: global_dec func_dec statements -> program

    // --- Declarations ---
    global_dec: (dec_and_init)*
    
    dec_and_init: var_dec 
                | table_dec 
                | assignment_stmt

    var_dec: mutability? data_type var_init -> variable_declaration

    mutability: ZETA

    data_type: KAI | FLUX | SELENE | BLAZE | LANI | LET

    var_init: IDENTIFIER multi_identifiers value_init? SEMICOLON -> var_initialization

    // Special rule for tables: allows declarations without semicolons
    var_init_no_semi: IDENTIFIER multi_identifiers value_init? -> var_initialization

    multi_identifiers: (COMMA IDENTIFIER)*
    
    value_init: ASSIGN values

    values: value (COMMA value)*
    value: expression
         | input_expr

    table_dec: HUBBLE data_type IDENTIFIER ASSIGN LBRACE hubble_elements? RBRACE SEMICOLON -> table_declaration

    hubble_elements: hubble_element (COMMA hubble_element)*
                   | LBRACE hubble_elements RBRACE (COMMA hubble_elements)*

    hubble_element: expression 
                  | func_def 
                  | var_dec          // Strict (with semicolon)
                  | table_var_dec    // Relaxed (no semicolon)

    table_var_dec: mutability? data_type var_init_no_semi -> variable_declaration

    // --- Functions ---
    func_dec: (func_def)*

    // func_return is optional (?) because statements can consume it
    func_def: func_data_type IDENTIFIER LPAREN parameters? RPAREN statements MOS -> function_definition

    func_data_type: VOID | data_type

    parameters: param (COMMA param)*
    
    param: data_type IDENTIFIER

    func_return: ZARA expression? SEMICOLON -> return_statement

    // --- Statements ---
    statements: statement* -> block

    statement: sol_stmt
             | orbit_stmt
             | phase_stmt
             | wax_stmt
             | warp_stmt
             | io_stmt
             | goto_stmt
             | label_dec
             | local_dec
             | dec_and_init  // Updated to allow declarations as statements
             | expr_stmt
             | func_return
             | empty_stmt

    sol_stmt: SOL expression statements MOS (soluna_block)* (luna_block)? -> if_statement
    soluna_block: SOLUNA expression statements MOS
    luna_block: LUNA statements MOS

    orbit_stmt: ORBIT expression COS statements MOS -> while_loop

    phase_stmt: PHASE for_init COMMA expression (COMMA expression)? COS statements MOS -> for_loop
    for_init: KAI IDENTIFIER ASSIGN expression

    wax_stmt: WAX statements WANE expression -> repeat_until

    warp_stmt: WARP SEMICOLON -> break_statement

    io_stmt: output_stmt # | input_stmt

    output_stmt: (NOVA | LUMEN) LPAREN expression RPAREN SEMICOLON -> output
    
    # input_stmt: LUMINA LPAREN (expression (COMMA expression)*)? RPAREN SEMICOLON -> expression_statement

    goto_stmt: LEO LABEL SEMICOLON -> goto
    
    label_dec: LABEL SEMICOLON -> label_dec

    local_dec: LOCAL dec_and_init -> local_declaration

    empty_stmt: SEMICOLON -> empty_statement

    expr_stmt: (func_call | unary_expr) SEMICOLON -> expression_statement

    // --- Assignments & Expressions ---
    assignment_stmt: targets assignment_op values SEMICOLON -> assignment
                   | targets post_unary_op SEMICOLON -> post_unary_statement
                   | post_unary_op targets SEMICOLON -> pre_unary_statement
                   | table_access ASSIGN expression SEMICOLON -> assignment

    targets: target (COMMA target)*
    target: IDENTIFIER | table_access

    table_access: IDENTIFIER (LBRACKET expression RBRACKET)+

    assignment_op: ASSIGN | PLUSEQ | MINUSEQ | MULEQ | DIVEQ | MODEQ

    expression: simple_expr

    simple_expr: expr_factor (general_op expr_factor)* 
    expr_factor: unary_negation? factor_value

    factor_value: literal
                | func_call
                | LPAREN expression RPAREN
                | post_unary_op? table_access
                | table_access post_unary_op?
                | post_unary_op? IDENTIFIER
                | IDENTIFIER post_unary_op?
                # | input_expr

    unary_expr: IDENTIFIER post_unary_op

    # input_expr: LUMINA LPAREN (expression (COMMA expression)*)? RPAREN
    input_expr: LUMINA LPAREN RPAREN

    func_call: IDENTIFIER LPAREN args? RPAREN
    args: expression (COMMA expression)*

    literal: INT_LIT | FLOAT_LIT | CHAR_LIT | STRING_LIT | IRIS | SAGE

    unary_negation: NOT | EXCLAM

    post_unary_op: PLUSPLUS | MINUSMINUS

    general_op: PLUS | MINUS | STAR | SLASH | DSLASH | MOD | CARET 
              | AND | OR | AND_WORD | OR_WORD
              | EQ | NEQ | GT | LT | GTE | LTE | CONCAT

    // --- Terminals Declaration ---
    %declare ZETA KAI FLUX SELENE BLAZE LANI LET VOID
    %declare HUBBLE ORBIT WAX WARP MOS WANE COS
    %declare SOL SOLUNA LUNA
    %declare NOVA LUMEN LUMINA
    %declare LEO LOCAL ZARA
    %declare PHASE
    %declare IDENTIFIER LABEL
    %declare INT_LIT FLOAT_LIT STRING_LIT CHAR_LIT IRIS SAGE
    %declare PLUS MINUS STAR SLASH DSLASH MOD CARET
    %declare ASSIGN PLUSEQ MINUSEQ MULEQ DIVEQ MODEQ
    %declare EQ NEQ GT LT GTE LTE
    %declare AND OR AND_WORD OR_WORD NOT EXCLAM
    %declare PLUSPLUS MINUSMINUS CONCAT
    %declare LPAREN RPAREN LBRACE RBRACE LBRACKET RBRACKET
    %declare COMMA SEMICOLON

"""

# =========================================================================
#  3. LEXER ADAPTER
# =========================================================================

TOKEN_MAP = {
    'zeta': 'ZETA', 'kai': 'KAI', 'flux': 'FLUX', 'selene': 'SELENE',
    'blaze': 'BLAZE', 'lani': 'LANI', 'let': 'LET', 'void': 'VOID',
    'hubble': 'HUBBLE', 'orbit': 'ORBIT', 'wax': 'WAX', 'warp': 'WARP',
    'mos': 'MOS', 'wane': 'WANE', 'cos': 'COS', 'sol': 'SOL',
    'soluna': 'SOLUNA', 'luna': 'LUNA', 'nova': 'NOVA', 'lumen': 'LUMEN',
    'lumina': 'LUMINA', 'leo': 'LEO', 'local': 'LOCAL', 'zara': 'ZARA',
    'phase': 'PHASE', 'iris': 'IRIS', 'sage': 'SAGE',
    'and': 'AND_WORD', 'or': 'OR_WORD', 'not': 'NOT', 

    'identifier': 'IDENTIFIER', 'label': 'LABEL',
    'int_lit': 'INT_LIT', 'float_lit': 'FLOAT_LIT', 'double': 'FLOAT_LIT',
    'string_lit': 'STRING_LIT', 'char_lit': 'CHAR_LIT',
    
    '+': 'PLUS', '-': 'MINUS', '*': 'STAR', '/': 'SLASH', '//': 'DSLASH',
    '%': 'MOD', '^': 'CARET',
    '=': 'ASSIGN', '+=': 'PLUSEQ', '-=': 'MINUSEQ', '*=': 'MULEQ',
    '/=': 'DIVEQ', '%=': 'MODEQ',
    '==': 'EQ', '!=': 'NEQ', '>': 'GT', '<': 'LT', '>=': 'GTE', '<=': 'LTE',
    '&&': 'AND', '||': 'OR', '!': 'EXCLAM',
    '++': 'PLUSPLUS', '--': 'MINUSMINUS', '..': 'CONCAT',
    '(': 'LPAREN', ')': 'RPAREN', '{': 'LBRACE', '}': 'RBRACE',
    '[': 'LBRACKET', ']': 'RBRACKET',
    ',': 'COMMA', ';': 'SEMICOLON'
}

class SolunaAdapter(LarkLexer):
    def __init__(self, lexer_conf):
        pass

    def lex(self, token_stream):
        for t in token_stream:
            t_type = t['type']
            t_val = t['value']
            
            if t_type in ('whitespace', 'tab', 'newline', 'comment'):
                continue

            lark_type = TOKEN_MAP.get(t_type)
            if not lark_type:
                lark_type = TOKEN_MAP.get(t_val)

            if lark_type:
                yield Token(lark_type, t_val, line=t['line'], column=t['col'])
            else:
                raise Exception(f"Lark Adapter Error: Unknown token type '{t_type}' value '{t_val}'")

# =========================================================================
#  4. TREE TO DICT TRANSFORMER
# =========================================================================

class TreeToDict(Transformer):
    def _node(self, type_name, children, value=None):
        return {"type": type_name, "children": children, "value": value}

    # Previously existing rule methods: program, global_dec, etc.
    def program(self, children): return self._node("Program", children)
    def global_dec(self, children): return self._node("GlobalDeclarations", children)
    def variable_declaration(self, children): return self._node("VariableDeclaration", children)
    def var_initialization(self, children): return self._node("VarInitialization", children)
    def table_declaration(self, children): return self._node("TableDeclaration", children)
    def function_definition(self, children): return self._node("FunctionDefinition", children)
    def block(self, children): return self._node("Block", children)
    def if_statement(self, children): return self._node("IfStatement", children)
    def while_loop(self, children): return self._node("WhileLoop", children)
    def for_loop(self, children): return self._node("ForLoop", children)
    def return_statement(self, children): return self._node("ReturnStatement", children)
    def expression_statement(self, children): return self._node("ExpressionStatement", children)
    def assignment(self, children): return self._node("Assignment", children)
    def pre_unary_statement(self, children): return self._node("UnaryStatement", children)
    def post_unary_statement(self, children): return self._node("UnaryStatement", children)
    def empty_statement(self, children): return self._node("EmptyStatement", [])

    # Explicit Token Handlers
    def IDENTIFIER(self, tok): return {"type": "Identifier", "value": tok.value, "children": []}
    def INT_LIT(self, tok): return {"type": "Literal", "value": tok.value, "children": []}
    def FLOAT_LIT(self, tok): return {"type": "Literal", "value": tok.value, "children": []}
    def STRING_LIT(self, tok): return {"type": "Literal", "value": tok.value, "children": []}
    def CHAR_LIT(self, tok): return {"type": "Literal", "value": tok.value, "children": []}

    # Handling for other tokens (reserved words)
    def __default_token__(self, tok):
        return {"type": tok.type, "value": tok.value, "children": []}
    
    def __default__(self, data, children, meta):
        return {"type": data, "children": children}

# =========================================================================
#  5. PARSER CLASS WITH ERROR FORMATTING
# =========================================================================

class LarkParser:
    def __init__(self):
        # Using Earley
        self.lark = Lark(SOLUNA_GRAMMAR, parser='earley', lexer=SolunaAdapter)
        self.transformer = TreeToDict()

    def parse(self, token_list):
        try:
            tree = self.lark.parse(token_list)
        except exceptions.UnexpectedInput as e:
            # INTERCEPT AND FORMAT ERROR HERE
            self._raise_formatted_error(e)
        except Exception as e:
            raise e
            
        return self.transformer.transform(tree)

    def _raise_formatted_error(self, e):
        """
        Translates internal Lark token names (e.g. 'RBRACE', 'ORBIT') 
        into user-friendly strings (e.g. '}', 'orbit') using TERMINAL_NAMES.
        """
        token = getattr(e, 'token', None)
        expected = getattr(e, 'expected', set())
        
        # 1. Format the "Unexpected X" part
        if token:
            unexpected_desc = f"'{token.value}'"
        else:
            unexpected_desc = "End of Input"

        # 2. Format the "Expected Y" part (UPDATED)
        expected_names = set()
        for t in expected:
            # Look up friendly name, default to lowercase title if missing
            name = TERMINAL_NAMES.get(t, t.lower())
            expected_names.add(f"'{name}'")
        
        # Sort for consistent display
        sorted_expected = sorted(list(expected_names))
        expected_str = ", ".join(sorted_expected)

        # 3. Construct Final Message
        # Handle cases where line/col are -1 or missing (common in EOF errors)
        line = getattr(e, 'line', -1)
        col = getattr(e, 'column', -1)
        
        if line == -1: line = "?"
        if col == -1: col = "?"

        error_msg = (
            f"Syntax Error at Line {line}, Col {col}: "
            f"Unexpected {unexpected_desc}. "
            f"Expected one of: [{expected_str}]"
        )
        
        # Raise a standard Exception which main.py will catch and display
        raise Exception(error_msg)