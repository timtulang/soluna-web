#
# token.py
#
# This module handles the *second pass* of tokenization: Classification.
#
# The `lexer.py` module just extracts raw lexeme strings. This module's
# `tokenize` function takes that list of strings and assigns a specific
# token type to each one (e.g., 'let', 'id', 'kai_lit').
#

# --- Reserved Words and Symbols ---
# I define these as sets for fast O(1) lookups.
# This is much faster than checking against a list.

RESERVED_WORDS = {
    'and', 'aster', 'blaze', 'cos', 'flux', 'hubble', 'iris', 'ixion', 
    'kai', 'lani', 'leo', 'let', 'lumen', 'lumina', 'luna', 'mos', 'not', 
    'nova', 'or', 'orbit', 'phase', 'sage', 'selene', 'sol', 'soluna', 
    'star', 'void', 'wane', 'warp', 'wax', 'zara', 'zeru'
}
RESERVED_SYMBOLS = {
    '+', '++', '+=', '-', '--', '-=', '*', '*=', '/', '/=', '//', '^', 
    '%', '%=', '=', '==', '!', '!=', '<', '<=', '>', '>=', '&&', '||', 
    '..', '#', '(', ')', '[', ']', '{', '}', ',', ';'
}

def is_leo_label(lexeme):
    """
    A custom validator for my special '::label::' syntax.
    It checks the format (starts/ends with '::') and ensures the
    middle part is 1-5 chars and alphanumeric/underscore.
    """
    if not (lexeme.startswith('::') and lexeme.endswith('::')):
        return False
    middle = lexeme[2:-2]
    if not (1 <= len(middle) <= 5):
        return False
    if not all(c.isalnum() or c == '_' for c in middle):
        return False
    return True

def tokenize(lexemes: list[str], metadata: list):
    """
    This is the main function of this module. It takes the list of
    raw lexemes from the lexer and classifies them.
    
    Args:
        lexemes (list[str]): The list of raw lexeme strings.
        metadata (list[dict]): The list of metadata dicts (line, col, etc.)
                               corresponding to each lexeme.
                               
    Returns:
        A list of classified tokens, zipped with their metadata.
        Format: [ ( (value, type), metadata ), ... ]
    """
    token_stream = []
    
    for lexeme in lexemes:
        # This is a safe-guard, though my current lexer.py doesn't
        # pass tuples.
        if isinstance(lexeme, tuple):
            token_stream.append(lexeme)
            continue
            
        # --- Classification Cascade ---
        # I use a simple, fast cascade of checks, starting
        # with the most common and cheapest checks.
        
        # 1. Is it a reserved word?
        if lexeme in RESERVED_WORDS:
            token_stream.append((lexeme, lexeme))
            continue
            
        # 2. Is it a reserved symbol?
        if lexeme in RESERVED_SYMBOLS:
            token_stream.append((lexeme, lexeme))
            continue
            
        # 3. Is it a comment?
        if lexeme.startswith('\\\\'):
            token_stream.append((lexeme, 'comment'))
            continue
        if lexeme.startswith('\\*') and lexeme.endswith('*\\'):
            token_stream.append((lexeme, 'comment'))
            continue
            
        # 4. Is it my custom 'leo_label'?
        if is_leo_label(lexeme):
            token_stream.append((lexeme, 'leo_label'))
            continue
            
        # 5. Is it a string literal?
        if lexeme.startswith('"') and lexeme.endswith('"'):
            token_stream.append((lexeme, 'selene_literal'))
            continue
            
        # 6. Is it a char literal?
        if lexeme.startswith("'") and lexeme.endswith("'"):
            token_stream.append((lexeme, 'blaze_literal'))
            continue
            
        # 7. Is it a number?
        # I use replace() to check for at most one decimal point.
        if lexeme.replace('.', '', 1).isdigit():
            if '.' in lexeme:
                # It's a float ('flux_lit')
                # I normalize the value here (e.g., "05.10" -> "5.1")
                integer_part, fractional_part = lexeme.split('.')
                integer_part = integer_part.lstrip('0') or '0'
                fractional_part = fractional_part.rstrip('0') or '0'
                normalized = integer_part + '.' + fractional_part
                token_stream.append((normalized, 'flux_lit')) 
            else:
                # It's an integer ('kai_lit')
                # I normalize this too (e.g., "007" -> "7")
                normalized = lexeme.lstrip('0') or '0'
                token_stream.append((normalized, 'kai_lit')) 
            continue
        
        # 8. If it's none of the above, it must be an identifier.
        token_stream.append((lexeme, 'id'))

    # Finally, I re-combine the newly classified tokens
    # with their original metadata (line, col, index).
    if metadata and len(metadata) == len(token_stream):
        return [(tok, meta) for tok, meta in zip(token_stream, metadata)]
        
    # Fallback if metadata wasn't provided for some reason
    return token_stream