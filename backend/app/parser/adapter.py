from .parser import Token

def adapter(raw_tokens_with_metadata):
    """
    The Lexer speaks one language ('kai_lit'), the Parser speaks another ('integer').
    This function translates between them.
    """
    clean_stream = []

    # Map the Lexer's specific types to the generic Grammar types
    TYPE_MAP = {
        'kai_lit':    'integer',
        'flux_lit':   'float',
        'blaze_lit':  'char',
        'selene_lit': 'string',
        'identifier': 'identifier',
        'label':      'label',
    }

    # ALL Soluna reserved words that the parser expects as literal token types
    RESERVED_WORDS = {
        'kai', 'flux', 'selene', 'blaze', 'lani', 'let', 'zeta', 'void', 'hubble', 'local', 
        'sol', 'soluna', 'luna', 'orbit', 'cos', 'phase', 'wax', 'wane', 'warp', 'mos', 
        'nova', 'lumen', 'lumina', 'zara', 'iris', 'sage', 'and', 'or', 'not', 'leo', 'label'
    }

    for token_tuple, meta in raw_tokens_with_metadata:
        value, type_tag = token_tuple
        
        # Comments are for humans, not parsers. Yeet them.
        if type_tag == 'comment':
            continue

        # If it's in the map, use the generic name. 
        # Otherwise (keywords, symbols), keep the original tag.
        grammar_type = TYPE_MAP.get(type_tag, type_tag)

        # --- THE FIX ---
        # Force all reserved keywords and functions to use their literal string value 
        # as their token type, overriding whatever generic category the Lexer gave them.
        if value in RESERVED_WORDS:
            grammar_type = value

        # Build the clean Token object with metadata for error reporting
        line = meta.get('line', 0)
        col = meta.get('col', 0)
        
        token = Token(
            type_name=grammar_type, 
            value=value, 
            line=line, 
            col=col
        )
        
        clean_stream.append(token)

    return clean_stream