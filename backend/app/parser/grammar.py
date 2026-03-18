# app/parser/grammar.py

# ============================================================================
# PRODUCTION CLASS: Represents a Grammar Rule
# ============================================================================

# Just a wrapper to make rules hashable. 
# Sets need hashable objects, so we can't use plain lists.
class Production:
    """
    A Production is a single grammar rule that describes how to build a parse tree.
    
    Think of it like a recipe:
        "A sandwich is made of: [bread, filling, bread]"
    
    In grammar terms:
        "sandwich" -> "bread" "filling" "bread"
        (This is a Production where LHS="sandwich", RHS=["bread", "filling", "bread"])
    
    The parser uses Productions to figure out how to break down the source code 
    into meaningful pieces.
    """
    def __init__(self, lhs, rhs):
        # lhs = "Left Hand Side" (what we're trying to build - like "statement")
        # rhs = "Right Hand Side" (what pieces we need - like ["if", "condition", "block"])
        self.lhs = lhs
        self.rhs = tuple(rhs) # Convert to tuple because tuples are immutable (needed for hashing)

    def __repr__(self):
        # Easy-to-read format: "statement -> if condition block"
        return f"{self.lhs} -> {' '.join(str(x) for x in self.rhs)}"

    def __eq__(self, other):
        # Two productions are equal if they have the same left side and right side
        return self.lhs == other.lhs and self.rhs == other.rhs

    def __hash__(self):
        # Makes Productions hashable so we can store them in sets (the parser needs this)
        return hash((self.lhs, self.rhs))


# ============================================================================
# THE SOLUNA GRAMMAR DICTIONARY
# ============================================================================
# Keys = Names of grammar rules (non-terminals like "statement", "expression")
# Values = Lists of Productions (different ways to build that rule)
#
# IMPORTANT CONCEPT: We unrolled the EBNF notation (the * and + symbols that mean 
# "zero or more" and "one or more") into plain recursion because the Earley parser 
# doesn't handle them directly.
#
# Example: Instead of "statements*" (0 or more statements), we write:
#   statements -> statement statements   (one statement, then more statements)
#   statements ->                        (or nothing - the base case)

SOLUNA_GRAMMAR = {
    # ========================================================================
    # 1. ENTRY POINT: This is where parsing starts
    # ========================================================================
    'program': [
        # A Soluna program consists of: global declarations, function declarations, and statements
        Production('program', ['global_dec', 'func_dec', 'statements'])
    ],
    
    # ========================================================================
    # 2. GLOBAL SCOPE: Variables declared at the top level (before any functions)
    # ========================================================================
    'global_dec': [
        # Global declarations can be recursive: one declaration followed by more declarations
        Production('global_dec', ['dec_and_init', 'global_dec']),
        # Or there can be no global declarations (base case)
        Production('global_dec', []) 
    ],
    'dec_and_init': [
        # A declaration is either a variable or a table
        Production('dec_and_init', ['var_dec']),
        Production('dec_and_init', ['table_dec'])
    ],
    
    # ========================================================================
    # 3. VARIABLES & TYPES: How to declare and initialize variables
    # ========================================================================
    'var_dec': [
        # Format: [optional const keyword] [type] [variable name and initialization]
        # Example: "zeta kai x = 5;" or "flux y = 3.14;"
        Production('var_dec', ['mutability', 'data_type', 'var_init'])
    ],
    'mutability': [
        # 'zeta' = const (cannot be changed), or nothing (can be changed)
        Production('mutability', ['zeta']),  # const
        Production('mutability', [])         # mutable (default)
    ],
    
    # The six types available in Soluna
    'data_type': [
        Production('data_type', ['kai']),    # integer
        Production('data_type', ['flux']),   # float
        Production('data_type', ['selene']), # double (extended precision float)
        Production('data_type', ['blaze']),  # character
        Production('data_type', ['lani']),   # boolean
        Production('data_type', ['let']),    # string
    ],

    # ========================================================================
    # 4. INITIALIZATION: Setting initial values for variables
    # ========================================================================
    'var_init': [
        # Format: variable_name = value ;
        # Can have multiple comma-separated variables: int x, y, z = 1, 2, 3;
        Production('var_init', ['identifier', 'multi_identifiers', 'value_init', ';'])
    ],
    'multi_identifiers': [
        # Handle comma-separated variable names: ", y, z" after the first variable
        Production('multi_identifiers', [',', 'identifier', 'multi_identifiers']),
        Production('multi_identifiers', [])  # Or no additional variables
    ],
    'value_init': [
        # Optionally assign values: "= 5, 10, 15"
        Production('value_init', ['=', 'value', 'value_init_tail']),
        Production('value_init', [])  # Or no assignment
    ],
    'value_init_tail': [
        # Handle the remaining values in a comma-separated list
        Production('value_init_tail', [',', 'value', 'value_init_tail']),
        Production('value_init_tail', []) 
    ],

    # ========================================================================
    # 5. VALUES & EXPRESSIONS: What can appear on the right side of =
    # ========================================================================
    'value': [
        Production('value', ['expression']),           # Any expression like "x + y"
        Production('value', ['lumina', '(', ')'])      # User input function
    ],

    # ========================================================================
    # 6. ASSIGNMENTS: Changing the value of a variable
    # ========================================================================
    'assignment_statement': [
        # Standard assignment: "x = 5;"
        Production('assignment_statement', ['identifier', 'multi_identifiers', 'assignment_value', ';']),
        # Pre/post increment: "++x;" or "x++;"
        Production('assignment_statement', ['unary_op', 'identifier', 'identifier_tail', ';']),
        Production('assignment_statement', ['identifier', 'identifier_tail', 'unary_op', ';']),
        # Table assignment: "arr[0] = 5;"
        Production('assignment_statement', ['table_nav'])
    ],
    'assignment_value': [
        # Assignment with operators like +=, -=, *=, etc.
        # Example: "x += 10" means "x = x + 10"
        Production('assignment_value', ['assignment_op', 'value', 'value_init_tail'])
    ],

    # ========================================================================
    # 7. FUNCTIONS: Named blocks of code that can be reused
    # ========================================================================
    'func_dec': [
        # Multiple function declarations, one after another
        Production('func_dec', ['func_def', 'func_dec']),
        Production('func_dec', [])  # Or no functions
    ],
    'func_def': [
        # Format: [return_type] function_name ( parameters ) { body }
        # Example: "kai add(kai a, kai b) cos ... mos"
        Production('func_def', ['func_data_type', 'identifier', '(', 'func_params', ')', 'statements', 'mos'])
    ],
    'func_data_type': [
        # What does this function return? A type, or nothing (void)?
        Production('func_data_type', ['data_type']),
        Production('func_data_type', ['void'])
    ],
    'func_params': [
        # The parameters inside the parentheses: (type1 param1, type2 param2, ...)
        Production('func_params', ['param', 'param_tail']),
        Production('func_params', [])  # Or no parameters
    ],
    'param': [
        # A single parameter: type and name (like "kai x")
        Production('param', ['data_type', 'identifier'])
    ],
    'param_tail': [
        # Handle additional parameters after the first one
        Production('param_tail', [',', 'param', 'param_tail']),
        Production('param_tail', []) 
    ],
    'func_return': [
        # Return statement: "zara value;" (return the value to the caller)
        Production('func_return', ['zara', 'return_val', ';'])
    ],
    'return_val': [
        # What to return: an expression, function call, or nothing (void functions)
        Production('return_val', ['expression']),
        Production('return_val', ['func_call']),
        Production('return_val', []) 
    ],

    # ========================================================================
    # 8. STATEMENTS: Individual lines of code that do something
    # ========================================================================
    # Regular statements (NOT in a loop - no breaks allowed)
    'statements': [
        # Statements are recursive: one statement followed by more statements
        Production('statements', ['statement', 'statements']),
        Production('statements', [])  # Or no statements
    ],
    'statement': [
        # All the types of things that can be a statement
        Production('statement', ['dec_and_init']),
        Production('statement', ['assignment_statement']),
        Production('statement', ['local_dec']),
        Production('statement', ['func_return']),
        Production('statement', ['func_call']),
        Production('statement', ['conditional_statement']),
        Production('statement', ['loop_while_statement']),
        Production('statement', ['loop_for_statement']),
        Production('statement', ['loop_repeat_until_statement']),
        Production('statement', ['output_statement']),
        Production('statement', ['label_dec']),
        Production('statement', ['label_goto'])
    ],

    # Loop statements (SAME as regular statements, but also allow 'break')
    'loop_statements': [
        Production('loop_statements', ['loop_statement', 'loop_statements']),
        Production('loop_statements', [])
    ],
    'loop_statement': [
        # All regular statements PLUS the ability to break out of loops
        Production('loop_statement', ['assignment_statement']),
        Production('loop_statement', ['dec_and_init']),
        Production('loop_statement', ['local_dec']),
        Production('loop_statement', ['func_return']),
        Production('loop_statement', ['func_call']),
        Production('loop_statement', ['conditional_statement_in_loop']),
        Production('loop_statement', ['loop_while_statement']),
        Production('loop_statement', ['loop_for_statement']),
        Production('loop_statement', ['loop_repeat_until_statement']),
        Production('loop_statement', ['output_statement']),
        Production('loop_statement', ['label_dec']),
        Production('loop_statement', ['label_goto']),
        Production('loop_statement', ['break_statements'])
    ],
    'local_dec': [
        # Variables declared inside functions/blocks with 'local' keyword
        Production('local_dec', ['local', 'dec_and_init'])
    ],

    # ========================================================================
    # 9. FUNCTION CALLS: Using a function (passing arguments)
    # ========================================================================
    'func_call': [
        # Format: function_name ( arguments ) ;
        # Example: "add(5, 3);"
        Production('func_call', ['identifier', '(', 'func_call_args', ')', ';'])
    ],
    'func_call_args': [
        # The values being passed to the function
        Production('func_call_args', ['expression', 'func_call_args_tail']),
        Production('func_call_args', [])  # Or no arguments
    ],
    'func_call_args_tail': [
        # Handle multiple arguments: arg2, arg3, ...
        Production('func_call_args_tail', [',', 'expression', 'func_call_args_tail']),
        Production('func_call_args_tail', []) 
    ],
    'func_call_in_expr': [
        # Function calls can also appear inside expressions (without the semicolon)
        Production('func_call_in_expr', ['identifier', '(', 'func_call_args', ')'])
    ],

    # ========================================================================
    # 10. EXPRESSIONS: Mathematical/logical calculations
    # ========================================================================
    # We avoid left-recursion here because Earley handles it differently than some other parsers
    'expression': [
        Production('expression', ['simple_expr']),
        Production('expression', ['multi_expr'])
    ],
    'simple_expr': [
        # Basic expression: a factor followed by operations
        Production('simple_expr', ['expr_factor', 'expr_tail'])
    ],
    'multi_expr': [
        # Expression with negation and parentheses: !(x + y)
        Production('multi_expr', ['unary_negation', '(', 'expression', ')', 'expr_tail'])
    ],
    'expr_tail': [
        # The operations that continue the expression: + - * / etc.
        Production('expr_tail', ['general_op', 'expr_factor', 'expr_tail']),
        Production('expr_tail', [])  # Or the expression ends here
    ],
    'expr_factor': [
        # A building block of an expression (can be negated with ! or not)
        Production('expr_factor', ['unary_negation', 'factor_value'])
    ],
    'unary_negation': [
        # Logical NOT operation: ! or "not"
        Production('unary_negation', ['!', 'unary_negation']),
        Production('unary_negation', ['not', 'unary_negation']),
        Production('unary_negation', [])  # Or no negation
    ],
    'factor_value': [
        # The smallest units of an expression (can't be broken down further)
        Production('factor_value', ['literals']),                              # Numbers, strings, etc.
        Production('factor_value', ['opt_unary_op', 'identifier', 'identifier_tail']),  # Variables
        Production('factor_value', ['identifier', 'identifier_tail', 'opt_unary_op']),
        Production('factor_value', ['func_call_in_expr']),                      # Function results
        Production('factor_value', ['(', 'expression', ')'])                    # Parenthesized expressions
    ],
    'identifier_tail': [
        # Handle array indexing: var[0] or var[0][1]
        Production('identifier_tail', ['table_index', 'identifier_tail']),
        Production('identifier_tail', []) 
    ],

    # ========================================================================
    # 11. LITERALS: Fixed values (constants)
    # ========================================================================
    'literals': [
        Production('literals', ['iris']),                    # Boolean true
        Production('literals', ['sage']),                    # Boolean false
        Production('literals', ['string_or_table_len']),     # String or array length (#)
        Production('literals', ['integer']),                 # Integer like 42
        Production('literals', ['float']),                   # Float like 3.14
        Production('literals', ['char']),                    # Character like 'a'
        Production('literals', ['string'])                   # String like "hello"
    ],
    'string_or_table_len': [
        # The # operator gets the length of a string or table
        Production('string_or_table_len', ['#', 'identifier'])
    ],

    # ========================================================================
    # 12. TABLES (ARRAYS): Collections of values
    # ========================================================================
    'table_dec': [
        # Format: hubble [type] [name] = { elements } ;
        # Example: "hubble kai numbers = {1, 2, 3};"
        Production('table_dec', ['hubble', 'data_type', 'identifier', '=', '{', 'hubble_elements', 'hubble_element_tail', '}', ';'])
    ],
    'hubble_elements': [
        # What can go inside a table: expressions, functions, nested tables, etc.
        Production('hubble_elements', ['expression']),
        Production('hubble_elements', ['func_def']),
        Production('hubble_elements', ['table_var_dec']),
        Production('hubble_elements', ['{', 'hubble_elements', 'hubble_element_tail', '}']),
        Production('hubble_elements', [])  # Or empty table
    ],
    'hubble_element_tail': [
        # Multiple elements separated by commas
        Production('hubble_element_tail', [',', 'hubble_elements', 'hubble_element_tail']),
        Production('hubble_element_tail', []) 
    ],
    'table_var_dec': [
        # Variables declared inside a table
        Production('table_var_dec', ['mutability', 'data_type', 'var_init_no_semi'])
    ],
    'var_init_no_semi': [
        # Variable initialization (without semicolon, because we're inside a table)
        Production('var_init_no_semi', ['identifier', 'multi_identifiers', 'value_init'])
    ],
    'table_nav': [
        # Assigning to an array element: arr[0] = 5;
        Production('table_nav', ['identifier', 'table_index', 'nav_tail', '=', 'expression', ';'])
    ],
    'table_index': [
        # The bracket notation: [0] or [x] or ["key"]
        Production('table_index', ['[', 'index_val', ']'])
    ],
    'nav_tail': [
        # Multiple levels of indexing: arr[0][1][2]
        Production('nav_tail', ['table_index', 'nav_tail']),
        Production('nav_tail', []) 
    ],
    'index_val': [
        # What can be used as an index: numbers, variables, strings
        Production('index_val', ['integer']),
        Production('index_val', ['identifier']),
        Production('index_val', ['string'])
    ],

    # ========================================================================
    # 13. OPERATORS: Symbols that do operations
    # ========================================================================
    'general_op': [
        # Arithmetic: +, -, *, /, //, %
        Production('general_op', ['+']), Production('general_op', ['-']),
        Production('general_op', ['*']), Production('general_op', ['/']),
        Production('general_op', ['//']), Production('general_op', ['%']),
        # Exponentiation
        Production('general_op', ['^']), 
        # Logical (both symbols and words): && ||, and, or
        Production('general_op', ['&&']), Production('general_op', ['||']),
        Production('general_op', ['and']), Production('general_op', ['or']),
        # Comparison: !=, ==, >, <, >=, <=
        Production('general_op', ['!=']), Production('general_op', ['==']),
        Production('general_op', ['>']), Production('general_op', ['<']),
        Production('general_op', ['>=']), Production('general_op', ['<=']),
        # String concatenation
        Production('general_op', ['..'])
    ],
    'assignment_op': [
        # Assignment and compound assignment: =, +=, -=, *=, /=, %=
        Production('assignment_op', ['=']), Production('assignment_op', ['-=']),
        Production('assignment_op', ['+=']), Production('assignment_op', ['*=']),
        Production('assignment_op', ['/=']), Production('assignment_op', ['%='])
    ],
    'unary_op': [
        # Increment and decrement: ++, --
        Production('unary_op', ['++']), Production('unary_op', ['--'])
    ],
    'opt_unary_op': [
        # Unary operator may or may not be present
        Production('opt_unary_op', ['unary_op']),
        Production('opt_unary_op', []) 
    ],

    # ========================================================================
    # 14. CONDITIONAL STATEMENTS: if-else-if-else logic
    # ========================================================================
    'conditional_statement': [
        # Format: if (condition) { statements } else if (...) { ... } else { ... }
        # In Soluna: sol condition cos statements mos conditional_tail
        Production('conditional_statement', ['sol', 'conditions', 'statements', 'mos', 'conditional_tail'])
    ],
    'conditions': [
        # What can be a condition: an expression or a parenthesized condition
        Production('conditions', ['expression']),
        Production('conditions', ['(', 'conditions', ')'])
    ],
    'conditional_tail': [
        # The optional else-if and else parts
        Production('conditional_tail', ['ifelse', 'conditional_tail']),  # else-if
        Production('conditional_tail', ['else']),                         # else
        Production('conditional_tail', [])                               # or nothing
    ],
    'ifelse': [
        # Format: else if (condition) { statements }
        Production('ifelse', ['soluna', 'conditions', 'statements', 'mos']),
    ],
    'else': [
        # Format: else { statements }
        Production('else', ['luna', 'statements', 'mos']),
        Production('else', []) 
    ],

    'conditional_statement_in_loop': [
        # Same as above, but allows break statements inside the body
        Production('conditional_statement_in_loop', ['sol', 'conditions', 'loop_statements', 'mos', 'conditional_tail_in_loop'])
    ],
    'conditional_tail_in_loop': [
        Production('conditional_tail_in_loop', ['ifelse_in_loop', 'conditional_tail_in_loop']), 
        Production('conditional_tail_in_loop', ['else_in_loop']),
        Production('conditional_tail_in_loop', []) 
    ],
    'ifelse_in_loop': [
        Production('ifelse_in_loop', ['soluna', 'conditions', 'loop_statements', 'mos']),
    ],
    'else_in_loop': [
        Production('else_in_loop', ['luna', 'loop_statements', 'mos']),
        Production('else_in_loop', []) 
    ],

    # ========================================================================
    # 15. LOOPS: Repeat code multiple times
    # ========================================================================
    'loop_while_statement': [
        # Format: while (condition) { statements }
        # In Soluna: orbit condition cos statements mos
        Production('loop_while_statement', ['orbit', 'conditions', 'cos', 'loop_statements', 'mos'])
    ],
    'loop_for_statement': [
        # Format: for (init; limit; step) { statements }
        # In Soluna: phase [type] var = start, limit, step cos statements mos
        Production('loop_for_statement', ['phase', 'for_loop_params', 'cos', 'loop_statements', 'mos'])
    ],
    'loop_repeat_until_statement': [
        # Format: do { statements } until (condition)
        # In Soluna: wax statements wane condition
        Production('loop_repeat_until_statement', ['wax', 'loop_statements', 'wane', 'conditions'])
    ],
    'break_statements': [
        # Break out of the nearest loop
        Production('break_statements', ['warp', ';'])
    ],

    # ========================================================================
    # 16. FOR LOOP PARAMETERS: The initialization, condition, and increment
    # ========================================================================
    'for_loop_params': [
        Production('for_loop_params', ['for_start', 'for_limit', 'for_step']),
        Production('for_loop_params', ['(', 'for_loop_params', ')'])
    ],
    'for_start': [
        # How to initialize the loop variable: "kai i = 0" or "i = 0"
        Production('for_start', ['kai', 'identifier', '=', 'expr_factor']),
        Production('for_start', ['identifier', '=', 'expr_factor']),
        Production('for_start', ['identifier'])
    ],
    'for_limit': [
        # The stopping condition: ", 10" (go up to 10)
        Production('for_limit', [',', 'expr_factor'])
    ],
    'for_step': [
        # The increment: ", 1" (go up by 1 each time)
        Production('for_step', [',', 'expr_factor']),
        Production('for_step', [])  # Or default to 1
    ],

    # ========================================================================
    # 17. OUTPUT & MISC: Printing and other utility operations
    # ========================================================================
    'output_statement': [
        # Format: print(expression); or println(expression);
        Production('output_statement', ['output_type', '(', 'output_arg', ')', ';'])
    ],
    'output_type': [
        Production('output_type', ['nova']),   # print (no newline)
        Production('output_type', ['lumen'])   # println (with newline)
    ],
    'output_arg': [
        # What to print: any expression
        Production('output_arg', ['expression'])
    ],
    'label_goto': [
        # Jump to a label: "leo ::myLabel::"
        Production('label_goto', ['leo', 'label_dec'])
    ],
    'label_dec': [
        # Define a label: "::myLabel::"
        Production('label_dec', ['label', ';'])
    ]
}