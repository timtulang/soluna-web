#
# regdef.py
#
# This file serves as the foundational "alphabet" for my entire lexer.
# I've defined all the basic character sets here so they can be reused
# across the transition diagram (td.py) and delimiter definitions (delims.py).
# This keeps the definitions consistent and easy to modify.
#

REGDEF = {
    # --- Special ASCII Sets ---
    # These are used for specific, tricky states in the FA,
    # like handling string literals or comments where most characters
    # are allowed, but a few (like '\n' or '"') are special.

    # All ASCII characters
    'ascii': {chr(i) for i in range(128)},
    
    # ASCII excluding newline and null
    'ascii_no_newline': {chr(i) for i in range(128) if chr(i) not in ['\n', '\0']},
    
    # ASCII for char/string literals: excludes quotes, newline, and backslash
    'ascii_298_302': {chr(i) for i in range(128) if chr(i) not in ['\'', '"', '\n', '\\', '\0']},
    
    # ASCII for multi-line comments: excludes '*' and null
    'ascii_309': {chr(i) for i in range(128) if chr(i) not in ['*', '\0']},

    # --- Basic Character Sets ---
    'alphabet': {
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    },
    'digit': {
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
    },
    
    # Combined set of alphabet (both cases) and digits. Used for identifiers.
    'alphanumeric': {
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
    },

    # --- Operator Groupings ---
    # Grouping operators makes it easy to define delimiters for
    # expressions (e.g., "an identifier can be followed by any operator").
    'arithmetic_operators': {'+', '-', '/', '*', '%', '^'},
    'relational_operators': {'<', '>'}, 
    'general_operators': {'+', '-', '/', '*', '%', '^', '=', '!', '&', '|'},

    # --- Delimiter Sets ---
    # These are key for defining what *separates* tokens.
    
    # 'free_delim' is the most common set, representing whitespace,
    # newlines, or the end of the file.
    'free_delim': {' ', '\\', '\n', '\0' },
    
    # 'io_delim' is specific to my I/O keywords (lumen, lumina, nova)
    # which must be followed by a '(' or a comment start '\\'.
    'io_delim': {'(', '\\'}
}