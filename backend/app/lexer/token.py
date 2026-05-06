#
# token.py
#
# TOKEN CLASSIFICATION (SECOND PASS OF TOKENIZATION)
#
# The `lexer.py` module performs the *first pass* (recognition): it extracts raw
# lexeme strings using a finite state machine. This module performs the *second pass*
# (classification): it assigns a specific token type to each lexeme.
#
# Key Responsibilities:
#  - Classify lexemes as keywords, identifiers, literals, operators, etc.
#  - Handle unary vs. binary minus (e.g., distinguish "a - 5" from "a = -5")
#  - Normalize numeric literals (remove leading zeros, handle decimals)
#  - Detect special syntax like labels (::name::)
#
# This two-pass design keeps the DFA simple and error-focused, while centralizing
# semantic decisions (like which minus is unary) in this single location.
#

# --- Reserved Words and Symbols ---
# All Soluna keywords (type names, control flow, I/O, etc.)
# Any identifier matching these gets token type equal to the keyword itself.
RESERVED_WORDS = {
    'and', 'blaze', 'cos', 'flux', 'hubble', 'iris', 
    'kai', 'lani', 'leo', 'let', 'local', 'lumen', 'lumina', 'luna', 'mos', 'not', 
    'nova', 'or', 'orbit', 'phase', 'sage', 'selene', 'sol', 'soluna', 
    'spark', 'star', 'void', 'wane', 'warp', 'wax', 'zara', 'zeru', 'zeta'
}

# All Soluna operators and delimiters
# Any lexeme matching these gets token type equal to the symbol itself.
RESERVED_SYMBOLS = {
    '+', '++', '+=', '-', '--', '-=', '*', '*=', '/', '/=', '//', '^', 
    '%', '%=', '=', '==', '!', '!=', '<', '<=', '>', '>=', '&&', '||', 
    '..', '#', '(', ')', '[', ']', '{', '}', ',', ';', '.'
}

def is_leo_label(lexeme):
    """
    Validate Soluna's special label syntax: ::name::
    
    Labels are used with the 'leo' goto instruction for jumps. The format is:
    - Starts and ends with '::'
    - Middle part is 1-5 alphanumeric characters or underscores
    - Examples: ::L0::, ::loop::, ::end_label::
    
    Args:
        lexeme: The candidate lexeme to validate
        
    Returns:
        True if lexeme matches the label format, False otherwise
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
    Classify lexemes into typed tokens (second pass of tokenization).
    
    This function takes raw lexeme strings from the lexer and assigns semantic
    types. It also handles two critical cases where the DFA made different
    decisions than the grammar requires:
    
    1. SPLIT: When the DFA grouped a negative number (e.g., "-5") but context
              says it should be subtraction (e.g., "a -5" → "a", "-", "5")
    2. MERGE: When the DFA separated minus and number (e.g., "- 5") but context
              says they form a negative literal (e.g., "= - 5" → "= -5")
    
    These fixes depend on surrounding context:
    - After identifiers, numbers, closing parens/brackets, or ++/-- → minus is SUBTRACTION
    - After operators and assignment → minus is UNARY NEGATION
    
    Steps:
    1. Iterate through all lexemes
    2. Detect and SPLIT eagerly grouped negative numbers
    3. Detect and MERGE isolated unary minus with following number
    4. Classify remaining lexemes:
       - Tuples (pre-classified) → pass through
       - Keywords → use keyword as type
       - Symbols → use symbol as type
       - Comments (lines starting with \\ or blocks with \*...\*) → comment type
       - Labels (::name::) → label type
       - String literals (quoted) → selene_lit type
       - Char literals (single-quoted) → blaze_lit type
       - Numbers → kai_lit (integer) or flux_lit (float, normalized)
       - Everything else → identifier type
    5. Return paired (lexeme, type) tuples with metadata if available
    
    Args:
        lexemes: List of raw lexeme strings from lexer.tokenize_all()
        metadata: List of dicts with line, col, start, end, force_id info
        
    Returns:
        If metadata provided and lengths match:
            List of [(lexeme, token_type), metadata_dict] tuples
        Otherwise:
            List of (lexeme, token_type) tuples
    
    Example:
        lexemes = ["kai", "x", "=", "-5"]
        tokens = tokenize(lexemes, [])
        # Result: [("kai", "kai"), ("x", "identifier"), ("=", "="), ("-5", "kai_lit")]
    """
    new_metadata = []
    token_stream = []
    
    # --- CONTEXT RULES ---
    # Determine when '-' is SUBTRACTION vs. UNARY NEGATION based on what came before.
    # After these token types, minus is a binary operator (e.g., "x - 5").
    # Otherwise, minus is unary (e.g., "= -5").
    SUBTRACTION_PREDECESSORS = {
        'identifier', 'kai_lit', 'flux_lit', 'blaze_lit', 'selene_lit',
        ')', ']', '++', '--', 'iris', 'sage'
    }
    
    i = 0
    while i < len(lexemes):
        lexeme = lexemes[i]
        meta = metadata[i] if i < len(metadata) else {}

        # --- SPLIT: Eagerly Grouped Negative Numbers ---
        # The DFA may have recognized "-5" as a single negative number literal.
        # But if it comes after something that ends an expression (identifier, number, ),
        # then '-' should actually be SUBTRACTION, not negation.
        # Solution: Split into ('-', '-') and ('+5', 'number')
        # Example: "a -5" should become "a", "-", "5" (not "a", "-5")
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
        
        # --- MERGE: Isolated Unary Minus ---
        # The DFA may have recognized '-' and '5' as separate tokens.
        # But if '-' comes after an operator/assignment (not after an expression),
        # then '-' should be UNARY NEGATION, not subtraction.
        # Solution: Merge into '-5' (a single negative number literal)
        # Example: "= - 5" should become "=", "-5" (not "=", "-", "5")
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

        # --- CLASSIFICATION CASCADE ---
        # Assign a token type to the lexeme in order of specificity.
        # Each condition checks a different category and breaks on match.
        
        if isinstance(lexeme, tuple):
            # Pre-classified tuple: pass through unchanged
            token_stream.append(lexeme)
            new_metadata.append(meta)
            i += 1
            continue
            
        if lexeme in RESERVED_WORDS and not meta.get('force_id'):
            # Keyword: use the keyword itself as the token type
            # (unless force_id flag is set, which overrides to identifier)
            token_stream.append((lexeme, lexeme))
            new_metadata.append(meta)
            i += 1
            continue
            
        if lexeme in RESERVED_SYMBOLS:
            # Operator or delimiter: use the symbol itself as the token type
            token_stream.append((lexeme, lexeme))
            new_metadata.append(meta)
            i += 1
            continue
            
        if lexeme.startswith('\\\\') or lexeme.startswith('\\*'):
            # Comment: either line comment (\\) or block comment (\*...\*)
            token_stream.append((lexeme, 'comment'))
            new_metadata.append(meta)
            i += 1
            continue
            
        if is_leo_label(lexeme):
            # Label: special syntax ::name:: for jump targets
            token_stream.append((lexeme, 'label'))
            new_metadata.append(meta)
            i += 1
            continue
            
        if lexeme.startswith('"') and lexeme.endswith('"'):
            # String literal: selene_lit type (Soluna's string type)
            token_stream.append((lexeme, 'selene_lit'))
            new_metadata.append(meta)
            i += 1
            continue
            
        if lexeme.startswith("'") and lexeme.endswith("'"):
            # Character literal: blaze_lit type (Soluna's char type)
            token_stream.append((lexeme, 'blaze_lit'))
            new_metadata.append(meta)
            i += 1
            continue
            
        # --- NUMERIC LITERALS ---
        # Strip leading minus sign and check if the rest is a number
        clean_lexeme = lexeme.lstrip('-')
        if clean_lexeme.replace('.', '', 1).isdigit():
            if '.' in clean_lexeme:
                # Floating-point number: normalize decimal representation
                # Remove leading zeros from integer part, trailing zeros from fractional part
                # Examples: "042.500" → "42.5", "0.0" → "0.0"
                parts = clean_lexeme.split('.')
                fractional_part = parts[1] if len(parts) > 1 else ""
                sign = "-" if lexeme.startswith("-") else ""
                integer_part = parts[0].lstrip('0') or '0'
                fractional_part_norm = fractional_part.rstrip('0') or '0'
                normalized = f"{sign}{integer_part}.{fractional_part_norm}"
                token_stream.append((normalized, 'flux_lit'))
            else:
                # Integer number: normalize by removing leading zeros
                # Examples: "042" → "42", "0" → "0"
                sign = "-" if lexeme.startswith("-") else ""
                normalized = sign + (clean_lexeme.lstrip('0') or '0')
                token_stream.append((normalized, 'kai_lit'))
            new_metadata.append(meta)
            i += 1
            continue
        
        # --- DEFAULT: IDENTIFIER ---
        # Any lexeme that doesn't match a specific category is an identifier
        # (variable name, function name, undefined keyword, etc.)
        token_stream.append((lexeme, 'identifier'))
        new_metadata.append(meta)
        i += 1

    # --- RETURN WITH METADATA ---
    # If metadata is provided and counts match, return (token, metadata) pairs
    # Otherwise, return just the token stream
    if metadata and len(new_metadata) == len(token_stream):
        return [(tok, m) for tok, m in zip(token_stream, new_metadata)]
        
    return token_stream