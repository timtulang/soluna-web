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

    for token_tuple, meta in raw_tokens_with_metadata:
        value, type_tag = token_tuple
        
        # Comments are for humans, not parsers. Yeet them.
        if type_tag == 'comment':
            continue

        # If it's in the map, use the generic name. 
        # Otherwise (keywords, symbols), keep the original tag.
        grammar_type = TYPE_MAP.get(type_tag, type_tag)

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