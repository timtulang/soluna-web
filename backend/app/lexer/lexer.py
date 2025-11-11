# backend/app/lexer.py (Modified)
import sys
from .td import STATES
from .token import tokenize
from . import lexer_errors

class Lexer:
    WHITESPACE = {' ', '\n', '\t', '\r'}
    
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.cursor = 0
        self.line = 1
        self.col = 1

    # ... (_get_char_at, _check_char_in_state_chars, _skip_ignorable_whitespace remain the same) ...
    def _get_char_at(self, index: int) -> str:
        if index < len(self.source_code): return self.source_code[index]
        return '\0'
    def _check_char_in_state_chars(self, char: str, state_chars) -> bool:
        try: return char in state_chars
        except: return False
    def _skip_ignorable_whitespace(self):
        while self.cursor < len(self.source_code):
            char = self.source_code[self.cursor]
            if char in self.WHITESPACE:
                if char == '\n': self.line += 1; self.col = 1
                else: self.col += 1
                self.cursor += 1
            else: break
    
    def _get_next_token(self):
        # This method's internal logic is correct, we just need to use its output
        # in tokenize_all to capture the start/end indices.
        # (The version from our previous discussion is perfect here)
        active_states = {0}
        current_lexeme = ""
        search_index = self.cursor
        last_accepted_lexeme = None
        last_accepted_end_index = self.cursor
        last_good_active_states = {0}
        char_that_killed_it = '\0'
        while active_states:
            last_good_active_states = active_states
            lookahead_char = self._get_char_at(search_index)
            char_that_killed_it = lookahead_char
            next_active_states = set()
            for state_id in active_states:
                for next_state_id in STATES[state_id].branches:
                    next_state = STATES[next_state_id]
                    if next_state.isEnd and self._check_char_in_state_chars(lookahead_char, next_state.chars):
                        if len(current_lexeme) >= len(last_accepted_lexeme or ""):
                            last_accepted_lexeme = current_lexeme
                            last_accepted_end_index = search_index
            if lookahead_char == '\0': break
            for state_id in active_states:
                for next_state_id in STATES[state_id].branches:
                    next_state = STATES[next_state_id]
                    if not next_state.isEnd and self._check_char_in_state_chars(lookahead_char, next_state.chars):
                        next_active_states.add(next_state_id)
            if not next_active_states: break
            active_states = next_active_states
            current_lexeme += lookahead_char
            search_index += 1
        
        # --- Error Detection Logic ---
        start_meta = (self.line, self.col, self.cursor, last_accepted_end_index)
        if last_accepted_lexeme is not None and len(current_lexeme) > len(last_accepted_lexeme):
            error = lexer_errors.check_for_dead_end_error(last_good_active_states, current_lexeme, start_meta)
            if error: return None, error
        if last_accepted_lexeme is not None:
            lexeme = last_accepted_lexeme
            new_cursor_pos = last_accepted_end_index
            return lexeme, new_cursor_pos
        error = lexer_errors.check_for_total_failure_error(last_good_active_states, char_that_killed_it, current_lexeme, start_meta)
        return None, error

    def tokenize_all(self):
        """
        Runs the lexer over the entire source code.
        Returns a tuple: (list_of_tokens, error_dictionary_or_None)
        """
        lexemes = []
        metadata = []
        
        while self.cursor < len(self.source_code):
            self._skip_ignorable_whitespace()
            if self.cursor >= len(self.source_code): break
                
            start_cursor = self.cursor
            start_line, start_col = self.line, self.col
            
            lexeme, result = self._get_next_token()
            
            if lexeme is None:
                # Error occurred
                error_tuple = result
                return [], lexer_errors.format_error(error_tuple)
            
            # Success
            end_cursor = result
            lexemes.append(lexeme)
            metadata.append({'line': start_line, 'col': start_col, 'start': start_cursor, 'end': end_cursor})
            
            # Advance main cursor and line/col counts
            self.cursor = end_cursor
            for char in lexeme:
                if char == '\n': self.line += 1; self.col = 1
                else: self.col += 1

        # Post-process into final tokens
        tokens = tokenize(lexemes, metadata)
        return tokens, None