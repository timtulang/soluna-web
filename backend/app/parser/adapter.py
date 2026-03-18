from .parser import Token

# Pre-compute reserved words as frozenset (O(1) lookup, faster than list/set membership)
RESERVED_WORDS = frozenset({
    'kai', 'flux', 'selene', 'blaze', 'lani', 'let', 'zeta', 'void', 'hubble', 'local',  # Type keywords and modifiers
    'sol', 'soluna', 'luna', 'orbit', 'cos', 'phase', 'wax', 'wane', 'warp', 'mos',      # Control flow keywords
    'nova', 'lumen', 'lumina', 'zara', 'iris', 'sage', 'and', 'or', 'not', 'leo', 'label'  # I/O and misc
})

# Map the Lexer's specific types to the generic Grammar types (cached at module level for performance)
TYPE_MAP = {
    'kai_lit':    'integer',     # Integer literal (like 5, 42, -3)
    'flux_lit':   'float',       # Float literal (like 3.14)
    'blaze_lit':  'char',        # Character literal (like 'a')
    'selene_lit': 'string',      # String literal (like "hello")
    'identifier': 'identifier',  # Variable names (like x, myVar)
    'label':      'label',       # Labels for goto statements
}

def adapter(raw_tokens_with_metadata):
    """
    TRANSLATOR BETWEEN LEXER AND PARSER
    
    The Lexer (the tokenizer) and Parser are like two people speaking different dialects.
    The Lexer identifies things like "kai_lit" (a literal integer), but the Parser 
    expects a more generic name like "integer".
    
    This function is the translator that converts the Lexer's output into a form 
    the Parser can understand.
    
    Input:  List of tuples like [("5", "kai_lit"), ("x", "identifier"), ...]
    Output: List of Token objects that the Parser can process
    
    PERFORMANCE: Uses frozenset for O(1) keyword lookup instead of list membership.
    """
    clean_stream = []

    # Loop through each token from the lexer
    for token_tuple, meta in raw_tokens_with_metadata:
        value, type_tag = token_tuple
        
        # SKIP COMMENTS: Comments are for humans to read, not for the parser
        # So we throw them away here before passing to the parser
        if type_tag == 'comment':
            continue

        # TRANSLATE TYPE NAMES: Convert lexer-specific type names to generic parser type names
        # If not in the map, just use the original tag (for symbols like '+', '-', etc.)
        grammar_type = TYPE_MAP.get(type_tag, type_tag)

        # HANDLE RESERVED WORDS (THE KEY STEP)
        # If the token's value (like "kai") is a reserved word, use the word itself as the type.
        # This tells the parser "this is a 'kai' keyword" instead of just "this is an identifier".
        # Example: Token("kai", "kai") instead of Token("identifier", "kai")
        # O(1) lookup using frozenset instead of list
        if value in RESERVED_WORDS:
            grammar_type = value

        # BUILD TOKEN OBJECT with position info for better error messages
        # When the parser fails, it can tell the user exactly where (line/column) the problem is
        line = meta.get('line', 0)
        col = meta.get('col', 0)
        
        token = Token(
            type_name=grammar_type,  # What kind of token is this?
            value=value,              # The actual text (like "5" or "x")
            line=line,                # Which line in source code
            col=col                   # Which column in source code
        )
        
        clean_stream.append(token)

    return clean_stream