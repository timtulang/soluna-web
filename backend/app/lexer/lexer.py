#
# lexer.py
#
# This is the main lexer engine. It contains the Lexer class that
# I designed to run the Finite Automaton (FA) defined in `td.py`.
#
# Its job is to:
# 1. Take the source code as input.
# 2. Skip whitespace.
# 3. Use the FA (`_get_next_token`) to find the longest valid raw lexeme.
# 4. Handle errors ("panic and recover") using `lexer_errors.py`.
# 5. Collect all valid lexemes and their metadata (line, col).
# 6. Pass the list of raw lexemes to `token.py` for final classification.
#

import sys
from .td import STATES, ID_END_STATES # My FA state machine
from .token import tokenize        # The second-pass classifier
from . import lexer_errors        # My error handling module

class Lexer:
    # Defining ignorable whitespace characters
    WHITESPACE = {' ', '\n', '\t', '\r'}
    
    def __init__(self, source_code: str):
        """
        Initializes the lexer.
        I set up the internal state: the code, and the pointers
        for our current position (cursor, line, col).
        """
        self.source_code = source_code
        self.cursor = 0
        self.line = 1
        self.col = 1

    # --- Private Utility Methods ---

    def _get_char_at(self, index: int) -> str:
        """
        A simple helper to safely get a character from the source code.
        If the index is out of bounds, I return the null character ('\0'),
        which I use to signal the End-of-File (EOF).
        """
        if index < len(self.source_code): 
            return self.source_code[index]
        return '\0' # EOF marker

    def _check_char_in_state_chars(self, char: str, state_chars) -> bool:
        """
        A helper to check if a character matches a state's acceptance criteria.
        This handles the fact that `state_chars` is a list (from my State class).
        The try/except is a safety net for any weird character comparisons.
        """
        try: 
            return char in state_chars
        except: 
            return False

    def _skip_ignorable_whitespace(self):
        """
        I use this method to advance the main `self.cursor` past any
        whitespace. It also correctly increments `self.line` and resets
        `self.col` when it encounters a newline.
        """
        while self.cursor < len(self.source_code):
            char = self.source_code[self.cursor]
            if char in self.WHITESPACE:
                if char == '\n': 
                    self.line += 1
                    self.col = 1
                else: 
                    self.col += 1
                self.cursor += 1
            else: 
                break
    
    def _get_next_token(self):
        """
        This is the core FA simulation loop.
        It attempts to find the *longest* valid lexeme starting from
        the current `self.cursor`.
        
        Returns:
            (str, int, set): (lexeme, new_cursor_pos, accepted_states) on success.
            (None, tuple, None): (None, error_tuple, None) on failure.
        """
        # Start the FA simulation from state 0
        active_states = {0}
        current_lexeme = ""
        
        # This search_index is a *lookahead* cursor.
        # The main `self.cursor` doesn't move yet.
        search_index = self.cursor
        
        # These variables track the *last valid token* we've found.
        # This is how I implement "longest match".
        # e.g., for "letx", it will find "let" as the last_accepted_lexeme.
        last_accepted_lexeme = None
        last_accepted_end_index = self.cursor
        last_good_active_states = {0}
        char_that_killed_it = '\0' # The char that stopped the simulation
        
        # NEW: Track which states accepted the token
        last_accepted_states = set()
        
        while active_states:
            # Store the current state before advancing
            last_good_active_states = active_states
            
            # Look at the *next* character
            lookahead_char = self._get_char_at(search_index)
            char_that_killed_it = lookahead_char
            
            next_active_states = set()

            # --- Delimiter Check ---
            # This is crucial. I check if the `lookahead_char` is a
            # valid *delimiter* for any *end state* we're currently in.
            for state_id in active_states:
                for next_state_id in STATES[state_id].branches:
                    next_state = STATES[next_state_id]
                    if next_state.isEnd and self._check_char_in_state_chars(lookahead_char, next_state.chars):
                        # If it is, this is a potential token.
                        # I record it *only if* it's longer than (or equal to) the
                        # one I've already found.
                        
                        # Logic Update: Track states accurately
                        if last_accepted_lexeme is None or len(current_lexeme) > len(last_accepted_lexeme):
                            last_accepted_lexeme = current_lexeme
                            last_accepted_end_index = search_index
                            last_accepted_states = {next_state_id} # Reset for new longest match
                        elif len(current_lexeme) == len(last_accepted_lexeme):
                            last_accepted_states.add(next_state_id) # Add to existing match
            
            # Stop if we hit the end of the file
            if lookahead_char == '\0':
                # NEW FEATURE: Handle Unclosed Comments at EOF
                # If the file ends but we are inside a multi-line comment state (314, 315),
                # we accept the current lexeme as valid instead of triggering an error.
                if not active_states.isdisjoint(lexer_errors.UNCLOSED_COMMENT_STATES):
                    last_accepted_lexeme = current_lexeme
                    last_accepted_end_index = search_index
                    last_accepted_states = {317} # 317 is the normal comment end state
                break
            
            # --- State Transition ---
            # Now, I find all *non-end* states that can transition
            # on the current `lookahead_char`.
            for state_id in active_states:
                for next_state_id in STATES[state_id].branches:
                    next_state = STATES[next_state_id]
                    if not next_state.isEnd and self._check_char_in_state_chars(lookahead_char, next_state.chars):
                        next_active_states.add(next_state_id)
            
            # If there are no next states, the simulation is over.
            if not next_active_states: 
                break
                
            # Advance the simulation
            active_states = next_active_states
            current_lexeme += lookahead_char
            search_index += 1
        
        # --- Post-Loop Analysis ---
        # The loop is over. Now I decide what happened.
        
        start_meta = (self.line, self.col, self.cursor, last_accepted_end_index)

        # Case 1: The loop broke, but we *never* found a valid end state.
        # This checks for "dead ends" like "123."
        if last_accepted_lexeme is not None and len(current_lexeme) > len(last_accepted_lexeme):
            error = lexer_errors.check_for_dead_end_error(last_good_active_states, current_lexeme, start_meta)
            if error: 
                return None, error, None # Return the "UNFINISHED_FLUX" error

        # Case 2: Success. We found at least one valid token.
        # The `last_accepted_lexeme` holds the longest one.
        if last_accepted_lexeme is not None:
            lexeme = last_accepted_lexeme
            new_cursor_pos = last_accepted_end_index
            return lexeme, new_cursor_pos, last_accepted_states
        
        # Case 3: Total failure. No valid state transitions *at all*
        # from the start, or an invalid delimiter.
        failed_char = self._get_char_at(self.cursor)
        error = lexer_errors.check_for_total_failure_error(
            last_good_active_states,
            char_that_killed_it,
            current_lexeme,
            start_meta,
            failed_char # Pass the char that *caused* the error
        )
        return None, error, None

    def tokenize_all(self):
        """
        This is the main public method I designed to run the lexer
        over the entire source code.
        
        It implements "panic and recover" error handling: if it
        finds an error, it logs it, advances the cursor by one,
        and tries to lex again.
        
        Returns:
            A tuple: (list_of_tokens, list_of_errors)
        """
        lexemes = []  # Stores the raw lexeme strings
        metadata = [] # Stores their {line, col, start, end}
        errors = []   # Stores any formatted error dicts
        
        # Loop until we've consumed the entire file
        while self.cursor < len(self.source_code):
            # 1. Skip all ignorable whitespace
            self._skip_ignorable_whitespace()
            if self.cursor >= len(self.source_code): 
                break # Re-check for EOF after skipping
                
            # 2. Store our starting position *before* trying to get a token
            start_cursor = self.cursor
            start_line, start_col = self.line, self.col
            
            # 3. Try to get the next token
            lexeme, result, accepted_states = self._get_next_token()
            
            # 4. Handle Failure ("Panic and Recover")
            if lexeme is None:
                error_tuple = result # This is the error from _get_next_token
                formatted_err = lexer_errors.format_error(error_tuple)
                
                # UPDATE: Capture the range of the error (start, end)
                # so we can filter these regions out in the output.
                advance_amount = 0
                if error_tuple[0] == 'INVALID_DELIMITER':
                    # Data is (lexeme, delim)
                    bad_lexeme, _ = error_tuple[2]
                    advance_amount = len(bad_lexeme)
                else:
                    advance_amount = 1

                formatted_err['start'] = start_cursor
                formatted_err['end'] = self.cursor + advance_amount
                errors.append(formatted_err)
                
                # Now actually advance the cursor
                # Handle INVALID_DELIMITER specially to separate the invalid token from the next error
                if error_tuple[0] == 'INVALID_DELIMITER':
                    bad_lexeme, _ = error_tuple[2]
                    
                    # Advance by the length of the lexeme (consuming the "valid" part)
                    # so the next iteration starts at the bad delimiter.
                    # We must update line/col correctly for the skipped text.
                    for char in bad_lexeme:
                        if char == '\n':
                            self.line += 1
                            self.col = 1
                        else:
                            self.col += 1
                    self.cursor += len(bad_lexeme)
                else:
                    # Standard panic: Advance by 1
                    char_at_cursor = self._get_char_at(self.cursor)
                    if char_at_cursor == '\n':
                        self.line += 1
                        self.col = 1
                    else:
                        self.col += 1
                    self.cursor += 1 # Advance!
                
                continue # Go to the next loop iteration
            
            # 5. Handle Success
            end_cursor = result
            
            # Determine if this token is forced to be an Identifier
            # This happens when a Reserved Word string (e.g. "kai") is accepted
            # by an Identifier state (because of a specific delimiter like '*')
            # but rejected by the Keyword state.
            is_forced_id = False
            if accepted_states and accepted_states.issubset(ID_END_STATES):
                is_forced_id = True

            lexemes.append(lexeme)
            metadata.append({
                'line': start_line, 
                'col': start_col, 
                'start': start_cursor, 
                'end': end_cursor,
                'force_id': is_forced_id # Pass this hint to token.py
            })
            
            # 6. Advance the main cursor and line/col counts
            # I set the cursor to the *end* of the lexeme
            self.cursor = end_cursor
            
            # Then, I update line/col based on the content of the lexeme
            # (this is mainly for handling multi-line comments)
            for char in lexeme:
                if char == '\n': 
                    self.line += 1
                    self.col = 1
                else: 
                    self.col += 1

        # 7. After the loop, pass the raw lexemes to Pass 2 for classification
        tokens = tokenize(lexemes, metadata)
        return tokens, errors # Return both tokens and errors