# app/parser/grammar.py

# Just a wrapper to make rules hashable. 
# Sets need hashable objects, so we can't use plain lists.
class Production:
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = tuple(rhs) # Tuples are immutable, lists aren't. needed for set hashing later.

    def __repr__(self):
        # easy print format: S -> A B
        return f"{self.lhs} -> {' '.join(str(x) for x in self.rhs)}"

    def __eq__(self, other):
        return self.lhs == other.lhs and self.rhs == other.rhs

    def __hash__(self):
        return hash((self.lhs, self.rhs))

# The massive grammar dict. 
# Keys are non-terminals, values are lists of Production rules.
# We had to unroll the EBNF loops (the * and + stuff) into recursion 
# because standard Earley doesn't handle loops natively.
SOLUNA_GRAMMAR = {
    # 1. Main Entry Point
    'program': [
        Production('program', ['global_dec', 'func_dec', 'statements'])
    ],
    
    # 2. Global Scope Stuff
    # Recursive definition: global_dec is either a declaration AND more declarations,
    # or it's nothing (lambda/epsilon).
    'global_dec': [
        Production('global_dec', ['dec_and_init', 'global_dec']),
        Production('global_dec', []) 
    ],
    'dec_and_init': [
        Production('dec_and_init', ['var_dec']),
        Production('dec_and_init', ['table_dec'])
    ],
    # 3. Variables & Types
    'var_dec': [
        Production('var_dec', ['mutability', 'data_type', 'var_init'])
    ],
    'mutability': [
        Production('mutability', ['zeta']), # const
        Production('mutability', []) # optional
    ],
    # The standard types.
    'data_type': [
        Production('data_type', ['kai']),    # int
        Production('data_type', ['flux']),   # float
        Production('data_type', ['selene']), # double
        Production('data_type', ['blaze']),  # char
        Production('data_type', ['lani']),   # bool
        Production('data_type', ['let']),    # string
    ],

    # 4. Initialization Logic
    'var_init': [
        Production('var_init', ['identifier', 'multi_identifiers', 'value_init', ';'])
    ],
    # Recursive handling for comma-separated variables: "int x, y, z;"
    'multi_identifiers': [
        Production('multi_identifiers', [',', 'identifier', 'multi_identifiers']),
        Production('multi_identifiers', []) 
    ],
    'value_init': [
        Production('value_init', ['=', 'value', 'value_init_tail']),
        Production('value_init', []) 
    ],
    'value_init_tail': [
        Production('value_init_tail', [',', 'value', 'value_init_tail']),
        Production('value_init_tail', []) 
    ],

    # 5. Values & Expressions
    'value': [
        Production('value', ['expression']),
        Production('value', ['lumina', '(', ')']) # Input function
    ],

    # 6. Assignments
    # We allow standard assigns, unary ops (++), and table access.
    'assignment_statement': [
        Production('assignment_statement', ['identifier', 'multi_identifiers', 'assignment_value', ';']),
        Production('assignment_statement', ['unary_op', 'identifier', 'identifier_tail', ';']),
        Production('assignment_statement', ['identifier', 'identifier_tail', 'unary_op', ';']),
        Production('assignment_statement', ['table_nav'])
    ],
    'assignment_value': [
        Production('assignment_value', ['assignment_op', 'value', 'value_init_tail'])
    ],

    # 7. Functions
    'func_dec': [
        Production('func_dec', ['func_def', 'func_dec']),
        Production('func_dec', []) 
    ],
    'func_def': [
        Production('func_def', ['func_data_type', 'identifier', '(', 'func_params', ')', 'statements', 'mos'])
    ],
    'func_data_type': [
        Production('func_data_type', ['data_type']),
        Production('func_data_type', ['void'])
    ],
    'func_params': [
        Production('func_params', ['param', 'param_tail']),
        Production('func_params', []) 
    ],
    'param': [
        Production('param', ['data_type', 'identifier'])
    ],
    'param_tail': [
        Production('param_tail', [',', 'param', 'param_tail']),
        Production('param_tail', []) 
    ],
    'func_return': [
        Production('func_return', ['zara', 'return_val', ';'])
    ],
    'return_val': [
        Production('return_val', ['expression']),
        Production('return_val', ['func_call']),
        Production('return_val', []) 
    ],

    # 8. Statements (NORMAL BLOCKS - NO BREAKS ALLOWED)
    'statements': [
        Production('statements', ['statement', 'statements']),
        Production('statements', [])
    ],
    'statement': [
        Production('statement', ['dec_and_init']),
        Production('statement', ['assignment_statement']),
        Production('statement', ['local_dec']),
        Production('statement', ['func_def']),
        Production('statement', ['func_return']),
        Production('statement', ['func_call']),
        Production('statement', ['conditional_statement']),
        Production('statement', ['loop_while_statement']),
        Production('statement', ['loop_for_statement']),
        Production('statement', ['loop_repeat_until_statement']),
        Production('statement', ['output_statement']),
        Production('statement', ['empty_statement']),
        Production('statement', ['label_dec']),
        Production('statement', ['label_goto'])
    ],

    # NEW: Loop Statements (LOOP BLOCKS - BREAKS ALLOWED)
    'loop_statements': [
        Production('loop_statements', ['loop_statement', 'loop_statements']),
        Production('loop_statements', [])
    ],
    'loop_statement': [
        Production('loop_statement', ['dec_and_init']),
        Production('loop_statement', ['assignment_statement']),
        Production('loop_statement', ['local_dec']),
        Production('loop_statement', ['func_def']),
        Production('loop_statement', ['func_return']),
        Production('loop_statement', ['func_call']),
        Production('loop_statement', ['conditional_statement_in_loop']),
        Production('loop_statement', ['loop_while_statement']),
        Production('loop_statement', ['loop_for_statement']),
        Production('loop_statement', ['loop_repeat_until_statement']),
        Production('loop_statement', ['output_statement']),
        Production('loop_statement', ['empty_statement']),
        Production('loop_statement', ['label_dec']),
        Production('loop_statement', ['label_goto']),
        Production('loop_statement', ['break_statements'])
    ],
    'local_dec': [
        Production('local_dec', ['local', 'dec_and_init'])
    ],

    # 9. Function Calls
    'func_call': [
        Production('func_call', ['identifier', '(', 'func_call_args', ')', ';'])
    ],
    'func_call_args': [
        Production('func_call_args', ['expression', 'func_call_args_tail']),
        Production('func_call_args', []) 
    ],
    'func_call_args_tail': [
        Production('func_call_args_tail', [',', 'expression', 'func_call_args_tail']),
        Production('func_call_args_tail', []) 
    ],
    'func_call_in_expr': [
        Production('func_call_in_expr', ['identifier', '(', 'func_call_args', ')'])
    ],

    # 10. Expressions
    # This is a bit flat to support Earley without left-recursion issues.
    'expression': [
        Production('expression', ['simple_expr']),
        Production('expression', ['multi_expr'])
    ],
    'simple_expr': [
        Production('simple_expr', ['expr_factor', 'expr_tail'])
    ],
    'multi_expr': [
        Production('multi_expr', ['unary_negation', '(', 'expression', ')', 'expr_tail'])
    ],
    'expr_tail': [
        Production('expr_tail', ['general_op', 'expr_factor', 'expr_tail']),
        Production('expr_tail', []) 
    ],
    'expr_factor': [
        Production('expr_factor', ['unary_negation', 'factor_value'])
    ],
    'unary_negation': [
        Production('unary_negation', ['!']),
        Production('unary_negation', ['not']),
        Production('unary_negation', []) 
    ],
    'factor_value': [
        Production('factor_value', ['literals']),
        Production('factor_value', ['opt_unary_op', 'identifier', 'identifier_tail']),
        Production('factor_value', ['identifier', 'identifier_tail', 'opt_unary_op']),
        Production('factor_value', ['func_call_in_expr']),
        Production('factor_value', ['(', 'expression', ')'])
    ],
    'identifier_tail': [
        # Reuse nav_tail logic here (0 or more indices)
        Production('identifier_tail', ['table_index', 'identifier_tail']),
        Production('identifier_tail', []) 
        # OR simply: Production('identifier_tail', ['nav_tail']) if types align
    ],

    # 11. Literals
    'literals': [
        Production('literals', ['lani']),
        Production('literals', ['string_or_table_len']),
        Production('literals', ['integer']),
        Production('literals', ['float']),
        Production('literals', ['char']),
        Production('literals', ['string'])
    ],
    'lani': [
        Production('lani', ['iris']), # True
        Production('lani', ['sage'])  # False
    ],
    'string_or_table_len': [
        Production('string_or_table_len', ['#', 'identifier'])
    ],

    # 12. Tables (Hubble)
    # The 'hubble' keyword defines arrays/tables.
    'table_dec': [
        Production('table_dec', ['hubble', 'data_type', 'identifier', '=', '{', 'hubble_elements', 'hubble_element_tail', '}', ';'])
    ],
    'hubble_elements': [
        Production('hubble_elements', ['expression']),
        Production('hubble_elements', ['func_def']),
        Production('hubble_elements', ['table_var_dec']),
        Production('hubble_elements', ['{', 'hubble_elements', 'hubble_element_tail', '}']),
        Production('hubble_elements', []) 
    ],
    'hubble_element_tail': [
        Production('hubble_element_tail', [',', 'hubble_elements', 'hubble_element_tail']),
        Production('hubble_element_tail', []) 
    ],
    'table_var_dec': [
        Production('table_var_dec', ['mutability', 'data_type', 'var_init_no_semi'])
    ],
    'var_init_no_semi': [
        Production('var_init_no_semi', ['identifier', 'multi_identifiers', 'value_init'])
    ],
    'table_nav': [
        Production('table_nav', ['identifier', 'table_index', 'nav_tail', '=', 'expression', ';'])
    ],
    'table_index': [
        Production('table_index', ['[', 'index_val', ']'])
    ],
    'nav_tail': [
        Production('nav_tail', ['table_index', 'nav_tail']),
        Production('nav_tail', []) 
    ],
    'index_val': [
        Production('index_val', ['integer']),
        Production('index_val', ['identifier']),
        Production('index_val', ['string'])
    ],

    # 13. Operators
    'general_op': [
        Production('general_op', ['+']), Production('general_op', ['-']),
        Production('general_op', ['*']), Production('general_op', ['/']),
        Production('general_op', ['//']), Production('general_op', ['%']),
        Production('general_op', ['^']), 
        Production('general_op', ['&&']), Production('general_op', ['||']),
        Production('general_op', ['and']), Production('general_op', ['or']),
        Production('general_op', ['!=']), Production('general_op', ['==']),
        Production('general_op', ['>']), Production('general_op', ['<']),
        Production('general_op', ['>=']), Production('general_op', ['<=']),
        Production('general_op', ['..'])
    ],
    'assignment_op': [
        Production('assignment_op', ['=']), Production('assignment_op', ['-=']),
        Production('assignment_op', ['+=']), Production('assignment_op', ['*=']),
        Production('assignment_op', ['/=']), Production('assignment_op', ['%='])
    ],
    'unary_op': [
        Production('unary_op', ['++']), Production('unary_op', ['--'])
    ],
    'opt_unary_op': [
        Production('opt_unary_op', ['unary_op']),
        Production('opt_unary_op', []) 
    ],


    # 14 Conditional Statements
    'conditional_statement': [
        Production('conditional_statement', ['sol', 'conditions', 'statements', 'mos', 'conditional_tail'])
    ],
    'conditions': [
        Production('conditions', ['expression']),
        Production('conditions', ['(', 'conditions', ')'])
    ],
    'conditional_tail': [
        Production('conditional_tail', ['ifelse', 'conditional_tail']), 
        Production('conditional_tail', ['else']),
        Production('conditional_tail', []) 
    ],
    'ifelse': [
        Production('ifelse', ['soluna', 'conditions', 'statements', 'mos']),
    ],
    'else': [
        Production('else', ['luna', 'statements', 'mos']),
        Production('else', []) 
    ],

    'conditional_statement_in_loop': [
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

    # 15. Loops (Now using loop_statements)
    'loop_while_statement': [
        Production('loop_while_statement', ['orbit', 'conditions', 'cos', 'loop_statements', 'mos'])
    ],
    'loop_for_statement': [
        Production('loop_for_statement', ['phase', 'for_loop_params', 'cos', 'loop_statements', 'mos'])
    ],
    'loop_repeat_until_statement': [
        Production('loop_repeat_until_statement', ['wax', 'loop_statements', 'wane', 'conditions'])
    ],
    'break_statements': [
        Production('break_statements', ['warp', ';'])
    ],

    # 16. For Loop Helpers
    'for_loop_params': [
        Production('for_loop_params', ['for_start', 'for_limit', 'for_step']),
        Production('for_loop_params', ['(', 'for_loop_params', ')'])
    ],
    'for_start': [
        Production('for_start', ['kai', 'identifier', '=', 'expr_factor']),
        Production('for_start', ['identifier', '=', 'expr_factor']),
        Production('for_start', ['identifier'])
    ],
    'for_limit': [
        Production('for_limit', [',', 'expr_factor'])
    ],
    'for_step': [
        Production('for_step', [',', 'expr_factor']),
        Production('for_step', []) 
    ],

    # 17. Output & Misc
    'output_statement': [
        Production('output_statement', ['output_type', '(', 'output_arg', ')', ';'])
    ],
    'output_type': [
        Production('output_type', ['nova']), # print
        Production('output_type', ['lumen']) # println
    ],
    'output_arg': [
        Production('output_arg', ['expression'])
    ],
    'empty_statement': [
        Production('empty_statement', [';'])
    ],
    'label_goto': [
        Production('label_goto', ['leo', 'label_dec'])
    ],
    'label_dec': [
        Production('label_dec', ['label', ';'])
    ]
}