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
    if not (lexeme.startswith('::') and lexeme.endswith('::')):
        return False
    # Check that middle part is valid (alphanumeric/underscore, 1-5 chars)
    middle = lexeme[2:-2]
    if not (1 <= len(middle) <= 5):
        return False
    if not all(c.isalnum() or c == '_' for c in middle):
        return False
    return True

def tokenize(lexemes: list[str], metadata: list):
    token_stream = []
    
    for lexeme in lexemes:
        
        # NOTE: Whitespace and newlines are now handled
        # by the Lexer's _skip_whitespace() method, so we
        # don't need to check for them here.

        # Pre-tokenized (tuple) - just in case
        if isinstance(lexeme, tuple):
            token_stream.append(lexeme)
            continue
            
        # Check Reserved Words
        if lexeme in RESERVED_WORDS:
            token_stream.append((lexeme, lexeme)) # e.g., ('kai', 'kai')
            continue
            
        # Check Reserved Symbols
        if lexeme in RESERVED_SYMBOLS:
            token_stream.append((lexeme, lexeme)) # e.g., ('+', '+')
            continue

    
        if lexeme.startswith('\\') and lexeme.endswith('\n'):
            token_stream.append((lexeme, 'comment'))
            continue
        if lexeme.startswith('\\*') and lexeme.endswith('*\\'):
            token_stream.append((lexeme, 'comment'))
            continue
            
        # Check for Leo Label
        if is_leo_label(lexeme):
            token_stream.append((lexeme, 'leo_label'))
            continue

        # String literal
        if lexeme.startswith('"') and lexeme.endswith('"'):
            token_stream.append((lexeme, 'selene_literal'))
            continue
            
        # Char literal
        if lexeme.startswith("'") and lexeme.endswith("'"):
            token_stream.append((lexeme, 'char_literal'))
            continue

        # Numeric literals
        if lexeme.replace('.', '', 1).isdigit():
            if '.' in lexeme:
                # Float
                integer_part, fractional_part = lexeme.split('.')
                integer_part = integer_part.lstrip('0') or '0'
                fractional_part = fractional_part.rstrip('0') or '0'
                normalized = integer_part + '.' + fractional_part
                token_stream.append((normalized, 'flux_lit')) 
            else:
                # Integer
                normalized = lexeme.lstrip('0') or '0'
                token_stream.append((normalized, 'kai_lit')) 
            continue

        token_stream.append((lexeme, 'id'))

    # Pair tokens with metadata (if lengths match)
    if metadata and len(metadata) == len(token_stream):
        return [(tok, meta) for tok, meta in zip(token_stream, metadata)]

    return token_stream