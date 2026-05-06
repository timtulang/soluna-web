#
# lexer.py
#
# LEXICAL ANALYZER (TOKENIZER)
#
# This module converts raw source code into a stream of tokens.
# It uses a finite state machine (DFA) to recognize lexemes (keywords, identifiers,
# operators, literals, etc.) and converts them into structured Token objects.
#
# The lexer handles:
#  - Keywords and identifiers
#  - Numeric literals (integers, floats)
#  - String and character literals
#  - Operators and delimiters
#  - Comments (line and block)
#  - Error reporting for invalid syntax
#

import sys
from .td import STATES, ID_END_STATES 
from .token import tokenize        
from . import lexer_errors        

class Lexer:
    """
    TOKENIZER: Converts source code into a stream of tokens.
    
    The Lexer reads raw Soluna source code and identifies meaningful units (tokens)
    like keywords, operators, identifiers, and literals. It uses a deterministic finite
    automaton (DFA) where each state represents a position in recognizing a particular
    token pattern.
    
    Key Concepts:
    - **Lexeme**: The actual text matched (e.g., "kai", "42", "+")
    - **Token**: A (lexeme, type) pair (e.g., ("kai", "kai"), ("42", "kai_lit"))
    - **State Machine**: STATES dict (from td.py) defines all transitions. A transition
      is triggered when the next character matches a state's allowed chars.
    - **Acceptance**: When we reach an END state, we have a valid token
    - **Error Recovery**: If we hit a dead end, report the error and skip to next token
    
    Example Usage:
        lexer = Lexer("kai x = 5")
        tokens, errors = lexer.tokenize_all()
        # tokens: [("kai", "kai"), ("x", "identifier"), ("=", "="), ("5", "kai_lit")]
    """
    WHITESPACE = {' ', '\n', '\t', '\r'}
    
    def __init__(self, source_code: str):
        """
        Initialize the lexer with source code.
        
        Args:
            source_code: The raw Soluna program text to tokenize
        """
        self.source_code = source_code
        self.cursor = 0
        self.line = 1
        self.col = 1

    def _get_char_at(self, index: int) -> str:
        """
        Safely retrieve a character at the given index.
        
        Returns the EOF marker '\0' if index is out of bounds.
        
        Args:
            index: Position in source_code to read
            
        Returns:
            The character at index, or '\0' if past end of input
        """
        if index < len(self.source_code): 
            return self.source_code[index]
        return '\0' # EOF marker

    def _check_char_in_state_chars(self, char: str, state_chars) -> bool:
        """
        Check if a character is in the state's allowed character set.
        
        Safely handles None or invalid state_chars by returning False.
        
        Args:
            char: The character to test
            state_chars: A set/frozenset of allowed characters for this state
            
        Returns:
            True if char is in state_chars, False otherwise
        """
        try: 
            return char in state_chars
        except: 
            return False


    def _skip_ignorable_whitespace(self):
        """
        Advance past whitespace characters (spaces, tabs, newlines) without creating tokens.
        
        Updates cursor, line, and col tracking as we skip. Newlines increment the line
        counter and reset col to 1; tabs advance col by 4.
        """
        while self.cursor < len(self.source_code):
            char = self.source_code[self.cursor]
            if char in self.WHITESPACE:
                if char == '\n': 
                    self.line += 1
                    self.col = 1
                elif char == '\t':
                    self.col += 4
                else: 
                    self.col += 1
                self.cursor += 1
            else: 
                break
    
    def _get_next_token(self):
        """
        Extract the next token from the source code using DFA state transitions.
        
        This is the core of the lexer. It uses a deterministic finite automaton to
        identify tokens:
        
        Steps:
        1. Start with initial state {0} and empty lexeme
        2. For each lookahead character, check all active states for valid transitions
        3. A transition is valid if the next state accepts that character
        4. Track accepted tokens (when reaching an END state)
        5. Continue until no more valid transitions
        6. Return the longest accepted token or an error if none accepted
        
        Key Variables:
        - active_states: Set of states we're currently in (can be multiple due to ambiguity)
        - current_lexeme: Text accumulated so far
        - last_accepted_lexeme: The longest valid token found so far
        - last_accepted_states: The states where acceptance occurred
        
        Returns:
            (lexeme, result, accepted_states) tuple:
            - If success: (lexeme_str, new_cursor_pos, set_of_accepting_states)
            - If error: (None, error_tuple, None)
        """
        active_states = {0}
        current_lexeme = ""
        search_index = self.cursor
        last_accepted_lexeme = None
        last_accepted_end_index = self.cursor
        last_good_active_states = {0}
        char_that_killed_it = '\0' 
        last_accepted_states = set()
        
        while active_states:
            last_good_active_states = active_states
            lookahead_char = self._get_char_at(search_index)
            char_that_killed_it = lookahead_char
            
            next_active_states = set()

            # --- ACCEPTANCE CHECK ---
            # Try to match END states with the lookahead character
            # If successful, record this as a potential token (greedy matching)
            for state_id in active_states:
                for next_state_id in STATES[state_id].branches:
                    next_state = STATES[next_state_id]
                    if next_state.isEnd and self._check_char_in_state_chars(lookahead_char, next_state.chars):
                        if last_accepted_lexeme is None or len(current_lexeme) > len(last_accepted_lexeme):
                            last_accepted_lexeme = current_lexeme
                            last_accepted_end_index = search_index
                            last_accepted_states = {next_state_id} 
                        elif len(current_lexeme) == len(last_accepted_lexeme):
                            last_accepted_states.add(next_state_id) 
            
            # Handle EOF: Check if we're stuck in an unclosed comment or string
            if lookahead_char == '\0':
                if not active_states.isdisjoint(lexer_errors.UNCLOSED_COMMENT_STATES):
                    last_accepted_lexeme = current_lexeme
                    last_accepted_end_index = search_index
                    last_accepted_states = {317} 
                break
            
            # --- STATE TRANSITION ---
            # Try to move to the next state based on lookahead character
            # Only non-END states can transition (END states are accepting/final)
            for state_id in active_states:
                for next_state_id in STATES[state_id].branches:
                    next_state = STATES[next_state_id]
                    if not next_state.isEnd and self._check_char_in_state_chars(lookahead_char, next_state.chars):
                        next_active_states.add(next_state_id)
            
            # If we have no valid transitions, the DFA recognizes no more characters
            if not next_active_states: 
                break
                
            active_states = next_active_states
            current_lexeme += lookahead_char
            search_index += 1
        
        start_meta = (self.line, self.col, self.cursor, last_accepted_end_index)

        # --- ERROR DETECTION: DEAD END ---
        # We accepted a token but then the user typed more valid characters
        # Example: "123." - we accept "123" but then see "." which is not a valid continuation
        if last_accepted_lexeme is not None and len(current_lexeme) > len(last_accepted_lexeme):
            error = lexer_errors.check_for_dead_end_error(last_good_active_states, current_lexeme, start_meta)
            if error: 
                return None, error, None 
        
        # Check for dead end even if NO token was ever accepted
        # Example: "!!" where ! is not in the language
        if last_accepted_lexeme is None and len(current_lexeme) > 0:
             error = lexer_errors.check_for_dead_end_error(last_good_active_states, current_lexeme, start_meta)
             if error:
                 return None, error, None

        # --- SUCCESS ---
        # We found at least one valid token
        if last_accepted_lexeme is not None:
            lexeme = last_accepted_lexeme
            new_cursor_pos = last_accepted_end_index
            return lexeme, new_cursor_pos, last_accepted_states
        
        # --- TOTAL FAILURE ---
        # Not even a single character matched any valid path
        failed_char = self._get_char_at(self.cursor)
        error = lexer_errors.check_for_total_failure_error(
            last_good_active_states,
            char_that_killed_it,
            current_lexeme,
            start_meta,
            failed_char 
        )
        return None, error, None

    def tokenize_all(self):
        """
        Main entry point: Tokenize the entire source code.
        
        Steps:
        1. Skip whitespace to find the next token
        2. Call _get_next_token() to extract one token via DFA
        3. If error, record it and use error recovery to skip problematic characters
        4. If success, record the token and its metadata (line, col, position)
        5. Update cursor and line/col tracking as we consume characters
        6. Repeat until end of source code
        7. Convert lexemes to proper Token objects with type information
        
        Error Recovery:
        - For invalid delimiters, unclosed strings/chars: skip the entire problematic lexeme
        - For total failure (unrecognized char): skip just 1 character and continue
        - Maintains accurate line/col tracking even through errors
        
        Returns:
            (tokens, errors) tuple:
            - tokens: List of (lexeme, token_type) pairs with metadata dicts
            - errors: List of error dicts with location and message info
        
        Example:
            lexer = Lexer("kai x = 5")
            tokens, errors = lexer.tokenize_all()
            # tokens: [("kai", "kai"), ("x", "identifier"), ("=", "="), ("5", "kai_lit")]
            # errors: []
        """
        lexemes = []  
        metadata = [] 
        errors = []   
        
        while self.cursor < len(self.source_code):
            self._skip_ignorable_whitespace()
            if self.cursor >= len(self.source_code): 
                break 
                
            start_cursor = self.cursor
            start_line, start_col = self.line, self.col
            
            # --- TOKENIZATION ATTEMPT ---
            # Call the DFA to recognize the next token
            lexeme, result, accepted_states = self._get_next_token()
            
            # --- ERROR HANDLING ---
            if lexeme is None:
                error_tuple = result 
                formatted_err = lexer_errors.format_error(error_tuple)
                
                advance_amount = 0
                # Determine how many characters to skip based on error type
                if error_tuple[0] == 'INVALID_DELIMITER':
                    bad_lexeme, _ = error_tuple[2]
                    advance_amount = len(bad_lexeme)
                elif error_tuple[0] == 'UNFINISHED_FLUX':
                    bad_lexeme = error_tuple[2]
                    advance_amount = len(bad_lexeme)
                elif error_tuple[0] in ['UNCLOSED_STRING', 'UNCLOSED_CHAR']:
                     bad_lexeme = error_tuple[2]
                     advance_amount = len(bad_lexeme)
                else:
                    advance_amount = 1

                formatted_err['start'] = start_cursor
                formatted_err['end'] = self.cursor + advance_amount
                errors.append(formatted_err)
                
                # --- CURSOR AND POSITION TRACKING DURING ERROR RECOVERY ---
                # Skip the problematic characters and update line/col counters
                if error_tuple[0] in ['INVALID_DELIMITER', 'UNFINISHED_FLUX', 'UNCLOSED_STRING', 'UNCLOSED_CHAR']:
                    text_to_skip = error_tuple[2][0] if error_tuple[0] == 'INVALID_DELIMITER' else error_tuple[2]
                    
                    for char in text_to_skip:
                        if char == '\n':
                            self.line += 1
                            self.col = 1
                        elif char == '\t':
                            self.col += 4
                        else:
                            self.col += 1
                    self.cursor += len(text_to_skip)
                else:
                    # Standard panic (1 char) - skip the unexpected character
                    char_at_cursor = self._get_char_at(self.cursor)
                    if char_at_cursor == '\n':
                        self.line += 1
                        self.col = 1
                    elif char_at_cursor == '\t':
                        self.col += 4
                    else:
                        self.col += 1
                    self.cursor += 1 
                
                continue 
            
            # --- SUCCESSFUL TOKEN RECOGNITION ---
            end_cursor = result
            
            # Check if this token should be forced as an identifier
            # (e.g., when certain reserved patterns are broken)
            is_forced_id = False
            if accepted_states and accepted_states.issubset(ID_END_STATES):
                is_forced_id = True

            lexemes.append(lexeme)
            metadata.append({
                'line': start_line, 
                'col': start_col, 
                'start': start_cursor, 
                'end': end_cursor,
                'force_id': is_forced_id
            })
            
            self.cursor = end_cursor
            
            # Update line/col tracking as we consume the lexeme
            for char in lexeme:
                if char == '\n': 
                    self.line += 1
                    self.col = 1
                elif char == '\t':
                    self.col += 4
                else: 
                    self.col += 1

        # --- CONVERSION TO TOKEN OBJECTS ---
        # Convert raw lexemes and metadata to proper Token objects with type info
        tokens = tokenize(lexemes, metadata)
        return tokens, errors