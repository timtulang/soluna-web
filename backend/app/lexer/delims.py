#
# delims.py
#
# This file is crucial for the lexer's state machine. It defines the
# valid "delimiter" characters for almost every token.
#
# A delimiter is a character that can validly *follow* a token.
# For example, after the keyword 'and', a space, newline, or parenthesis
# is valid, but a letter (like 'andx') is not.
#
# I import my foundational character sets from REGDEF to build these rules.
# Each key in the DELIMS dictionary corresponds to one or more
# "end states" in my transition diagram (td.py).
#

from .regdef import REGDEF

DELIMS = {
    # Delimiter for separator keywords ('and', 'or', 'not', 'wane', 'sol', 'soluna').
    # They can be followed by whitespace or an opening parenthesis.
    'separator_delim': {*REGDEF['free_delim'], '(' },

    # Delimiters for '&&' and '||'.
    'and_or_delim': {'(', '!', '"', '-', '\'', '_', *REGDEF['alphanumeric'], *REGDEF['free_delim']},

    # Delimiters for most arithmetic operators (+, *, /, //, %, ^).
    'arithmetic_delim': {'(', '!', '"', '-', '\'', '_', *REGDEF['alphanumeric'], *REGDEF['free_delim']},

    # Delimiters for ',' and '='.
    'comma_equal_delim': {'"', '+', '-', '!', '(', '{', *REGDEF['alphanumeric'], *REGDEF['free_delim']},

    # Delimiters for 'iris' and 'sage' (my input functions).
    'iris_sage_delim': {*REGDEF['free_delim'], *REGDEF['arithmetic_operators'], *REGDEF['relational_operators'], ')', ';', ',', '&', '|', '('},

    # Delimiter for my custom '::label::' syntax.
    'label_delim': {*REGDEF['free_delim'], ';'},

    # A general-purpose delimiter set for most symbols (==, !=, <=, >=, etc.).
    'most_symbol_delim': {'(', '!', '"', '-', '\'', '_', *REGDEF['alphanumeric'], *REGDEF['free_delim']},

    # Delimiters for control structure keywords.
    'control_structure_delim': {*REGDEF['io_delim'], *REGDEF['free_delim']},

    # Delimiter for the '!' (not) operator.
    'not_delim': {'"', '-', '!', '(', *REGDEF['alphanumeric']},

    # Delimiter for the '-' (minus) operator (to distinguish from '--').
    'minus_delim': {'(', '!', '"', '\'', '_', *REGDEF['alphanumeric'], *REGDEF['free_delim']},

    # Delimiter for the semicolon.
    'semicolon_delim': {*REGDEF['alphabet'], *REGDEF['free_delim']},

    # Delimiter for '..' (string concatenation).
    'string_concat_delim': {'(', '"', '\'', '_', *REGDEF['alphanumeric'], *REGDEF['free_delim']},

    # Delimiter for '#' (string length).
    'string_length_delim': {'(', '"', '\'', '_', *REGDEF['alphabet']},

    # Delimiters for unary operators '++' and '--'.
    'unary_delim': {'(', '+', '-', '*', '%', '/', *REGDEF['relational_operators'], ')', ';', '&', '|', '\'', '_', '=', *REGDEF['alphanumeric'], *REGDEF['free_delim']},

    # Delimiters for identifiers. An identifier can be followed by
    # almost anything: whitespace, operators, punctuation, etc.
    'identifier_delim': {*REGDEF['free_delim'], *REGDEF['arithmetic_operators'], *REGDEF['relational_operators'], '(', ')', '[', '}', '.', ';', ',', '&', '|', '='},

    # Delimiter for 'warp' (break). It must be followed by a semicolon.
    'warp_delim': {';'},

    # Delimiters for grouping symbols.
    'open_bracket_delim': {'"', '\'', '-', '(', '[', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'close_bracket_delim': {';', ',', ')', '}', *REGDEF['free_delim']},
    'open_square_delim': { '“', "‘" , '-', '(', '{', '!' , '_' , *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'close_square_delim': {'[' , '=' , *REGDEF['free_delim']},
    'open_parenthesis_delim': {'"', '+', '-', '!', '(', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'close_parenthesis_delim': {';', ',', *REGDEF['general_operators'], ')', ']', '}', *REGDEF['free_delim']},

    # A general delimiter for data types (literals, identifiers).
    'most_data_type_delim': {*REGDEF['general_operators'], *REGDEF['relational_operators'], ')', ']', '}', ';', ',', '.', *REGDEF['free_delim']},

    # Delimiter for 'leo' (goto).
    'leo_delim': {';'},

    # Delimiter for 'zeru' (false).
    'zeru_delim': {*REGDEF['free_delim'], ';', ')', *REGDEF['arithmetic_operators'], *REGDEF['relational_operators']},
    
    # Delimiter for 'zara' (true).
    'zara_delim': {*REGDEF['free_delim'], '(', ';'}
}