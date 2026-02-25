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
RESERVED_WORDS = {
    'and', 'blaze', 'cos', 'flux', 'hubble', 'iris', 
    'kai', 'lani', 'leo', 'let', 'local', 'lumen', 'lumina', 'luna', 'mos', 'not', 
    'nova', 'or', 'orbit', 'phase', 'sage', 'selene', 'sol', 'soluna', 
    'star', 'void', 'wane', 'warp', 'wax', 'zara', 'zeru', 'zeta'
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
    token_stream = []
    new_metadata = []
    
    # Types of tokens that indicate the following '-' MUST be a SUBTRACTION operator,
    # not the start of a negative number.
    SUBTRACTION_PREDECESSORS = {
        'identifier', 'kai_lit', 'flux_lit', 'blaze_lit', 'selene_lit',
        ')', ']', '++', '--', 'iris', 'sage'
    }
    
    i = 0
    while i < len(lexemes):
        lexeme = lexemes[i]
        meta = metadata[i] if i < len(metadata) else {}

        # --- 1. Split Eagerly Grouped Negative Numbers (e.g., "a -5") ---
        # If the FA grouped "-5", but the previous token implies subtraction, SPLIT IT.
        if isinstance(lexeme, str) and lexeme.startswith('-') and len(lexeme) > 1:
            clean_test = lexeme[1:].replace('.', '', 1)
            if clean_test.isdigit():
                prev_type = token_stream[-1][1] if token_stream else None
                if prev_type in SUBTRACTION_PREDECESSORS:
                    # SPLIT: Yield '-' then process the rest as a positive number
                    token_stream.append(('-', '-'))
                    
                    meta_minus = dict(meta)
                    meta_minus['end'] = meta['start'] + 1
                    new_metadata.append(meta_minus)
                    
                    # Modify the current lexeme to be just the positive number part
                    lexeme = lexeme[1:]
                    meta = dict(meta)
                    meta['col'] += 1
                    meta['start'] += 1
        
        # --- 2. Merge Isolated Unary Minus (e.g., "a = - 5") ---
        # If the FA separated "-" and "5", but it should be a negative number, MERGE IT.
        if isinstance(lexeme, str) and lexeme == '-':
            prev_type = token_stream[-1][1] if token_stream else None
            if prev_type not in SUBTRACTION_PREDECESSORS:
                # It's unary! Check if the next lexeme is a number.
                if i + 1 < len(lexemes):
                    next_lexeme = lexemes[i+1]
                    if isinstance(next_lexeme, str):
                        next_clean = next_lexeme.replace('.', '', 1)
                        if next_clean.isdigit():
                            # MERGE: Glue them together
                            lexeme = "-" + next_lexeme
                            next_meta = metadata[i+1] if i+1 < len(metadata) else {}
                            meta = dict(meta)
                            meta['end'] = next_meta.get('end', meta['end']) # Span across
                            i += 1 # Skip the next token since we merged it

        # --- Classification Cascade ---
        if isinstance(lexeme, tuple):
            token_stream.append(lexeme)
            new_metadata.append(meta)
            i += 1
            continue
            
        if lexeme in RESERVED_WORDS and not meta.get('force_id'):
            token_stream.append((lexeme, lexeme))
            new_metadata.append(meta)
            i += 1
            continue
            
        if lexeme in RESERVED_SYMBOLS:
            token_stream.append((lexeme, lexeme))
            new_metadata.append(meta)
            i += 1
            continue
            
        if lexeme.startswith('\\\\') or lexeme.startswith('\\*'):
            token_stream.append((lexeme, 'comment'))
            new_metadata.append(meta)
            i += 1
            continue
            
        if is_leo_label(lexeme):
            token_stream.append((lexeme, 'label'))
            new_metadata.append(meta)
            i += 1
            continue
            
        if lexeme.startswith('"') and lexeme.endswith('"'):
            token_stream.append((lexeme, 'selene_lit'))
            new_metadata.append(meta)
            i += 1
            continue
            
        if lexeme.startswith("'") and lexeme.endswith("'"):
            token_stream.append((lexeme, 'blaze_lit'))
            new_metadata.append(meta)
            i += 1
            continue
            
        clean_lexeme = lexeme.lstrip('-')
        if clean_lexeme.replace('.', '', 1).isdigit():
            if '.' in clean_lexeme:
                parts = clean_lexeme.split('.')
                fractional_part = parts[1] if len(parts) > 1 else ""
                sign = "-" if lexeme.startswith("-") else ""
                integer_part = parts[0].lstrip('0') or '0'
                fractional_part_norm = fractional_part.rstrip('0') or '0'
                normalized = f"{sign}{integer_part}.{fractional_part_norm}"
                token_stream.append((normalized, 'flux_lit'))
            else:
                sign = "-" if lexeme.startswith("-") else ""
                normalized = sign + (clean_lexeme.lstrip('0') or '0')
                token_stream.append((normalized, 'kai_lit'))
            new_metadata.append(meta)
            i += 1
            continue
        
        token_stream.append((lexeme, 'identifier'))
        new_metadata.append(meta)
        i += 1

    if metadata and len(new_metadata) == len(token_stream):
        return [(tok, m) for tok, m in zip(token_stream, new_metadata)]
        
    return token_stream