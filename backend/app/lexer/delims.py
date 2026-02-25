#
# delims.py
#
from .regdef import REGDEF

DELIMS = {
    'separator_delim': {*REGDEF['free_delim'], '(' },
    'and_or_delim': {'(', '!', '"', '-', '\'', '_', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'arithmetic_delim': {'(', '!', '"', '-', '\'', '_', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'comma_equal_delim': {'"', '+', '-', '!', '(', '{', '\'', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'iris_sage_delim': {*REGDEF['free_delim'], *REGDEF['arithmetic_operators'], *REGDEF['relational_operators'], ')', ';', ',', '&', '|', '('},
    'label_delim': {*REGDEF['free_delim'], ';'},
    'most_symbol_delim': {'(', '!', '"', '-', '\'', '_', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'control_structure_delim': {*REGDEF['io_delim'], *REGDEF['free_delim']},
    'not_delim': {'"', '-', '!', '(', *REGDEF['alphanumeric']},
    'minus_delim': {'(', '!', '"', '\'', '_', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'semicolon_delim': {*REGDEF['alphabet'], *REGDEF['free_delim']},
    'string_concat_delim': {'(', '"', '\'', '_', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'string_length_delim': {'(', '"', '\'', '_', *REGDEF['alphabet']},
    'unary_delim': {'(', '*', '%', '/', *REGDEF['relational_operators'], ')', ';', '&', '|', '_', '=', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'identifier_delim': {*REGDEF['free_delim'], *REGDEF['arithmetic_operators'], *REGDEF['relational_operators'], '(', ')', '[' , ']', '}', '.', ';', ',', '&', '|', '='},
    'warp_delim': {';'},
    'open_bracket_delim': {'"', '\'', '-', '(' , '{', '}', '+', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'close_bracket_delim': {';', ',', ')', '}', *REGDEF['free_delim']},
    'open_square_delim': { '"', "\'" , '(', '{', '!' , '_' , '+', '-', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'close_square_delim': {'[' , '=', '+', '-', ';', ')', ',', '}', *REGDEF['free_delim'], *REGDEF['general_operators'], *REGDEF['relational_operators']},
    'open_parenthesis_delim': {'"', '+', '-', '!', '(', ')', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'close_parenthesis_delim': {';', ',', *REGDEF['general_operators'], ')', ']', '}', *REGDEF['free_delim']},
    'most_data_type_delim': {*REGDEF['general_operators'], *REGDEF['relational_operators'], ')', ']', '}', ';', ',', '.', *REGDEF['free_delim']},
    'leo_delim': {';'},
    'mos_delim' : {*REGDEF['free_delim'], ',', '}'},
    'zeru_delim': {*REGDEF['free_delim'], ';', ')', *REGDEF['arithmetic_operators'], *REGDEF['relational_operators']},
    'zara_delim': {*REGDEF['free_delim'], '(', ';'},
    'number_delim': {*REGDEF['general_operators'], *REGDEF['relational_operators'], ')', ']', '}', ';', ',', *REGDEF['free_delim']},
}