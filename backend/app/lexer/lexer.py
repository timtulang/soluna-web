import sys
from .td import STATES, ID_END_STATES 
from .token import tokenize        
from . import lexer_errors        

class Lexer:
    WHITESPACE = {' ', '\n', '\t', '\r'}
    
    def __init__(self, source_code: str):
        # PREPROCESSING: Convert 4 spaces into 1 tab character
        # This normalizes the input before lexing begins.
        self.source_code = source_code.replace("    ", "\t")
        self.cursor = 0
        self.line = 1
        self.col = 1

    def _get_char_at(self, index: int) -> str:
        if index < len(self.source_code): 
            return self.source_code[index]
        return '\0' # EOF marker

    def _check_char_in_state_chars(self, char: str, state_chars) -> bool:
        try: 
            return char in state_chars
        except: 
            return False

    def _skip_ignorable_whitespace(self):
        while self.cursor < len(self.source_code):
            char = self.source_code[self.cursor]
            if char in self.WHITESPACE:
                if char == '\n': 
                    self.line += 1
                    self.col = 1
                elif char == '\t':
                    # Treat a tab as 4 columns for accurate visual tracking
                    self.col += 4
                else: 
                    self.col += 1
                self.cursor += 1
            else: 
                break
    
    def _get_next_token(self):
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

            # --- Delimiter Check ---
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
            
            if lookahead_char == '\0':
                if not active_states.isdisjoint(lexer_errors.UNCLOSED_COMMENT_STATES):
                    last_accepted_lexeme = current_lexeme
                    last_accepted_end_index = search_index
                    last_accepted_states = {317} 
                break
            
            # --- State Transition ---
            for state_id in active_states:
                for next_state_id in STATES[state_id].branches:
                    next_state = STATES[next_state_id]
                    if not next_state.isEnd and self._check_char_in_state_chars(lookahead_char, next_state.chars):
                        next_active_states.add(next_state_id)
            
            if not next_active_states: 
                break
                
            active_states = next_active_states
            current_lexeme += lookahead_char
            search_index += 1
        
        start_meta = (self.line, self.col, self.cursor, last_accepted_end_index)

        # Dead End Check (e.g. "123." or "sky')
        if last_accepted_lexeme is not None and len(current_lexeme) > len(last_accepted_lexeme):
            error = lexer_errors.check_for_dead_end_error(last_good_active_states, current_lexeme, start_meta)
            if error: 
                return None, error, None 
        
        # Check for dead end even if NO token was accepted
        if last_accepted_lexeme is None and len(current_lexeme) > 0:
             error = lexer_errors.check_for_dead_end_error(last_good_active_states, current_lexeme, start_meta)
             if error:
                 return None, error, None

        # Success
        if last_accepted_lexeme is not None:
            lexeme = last_accepted_lexeme
            new_cursor_pos = last_accepted_end_index
            return lexeme, new_cursor_pos, last_accepted_states
        
        # Total Failure
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
        lexemes = []  
        metadata = [] 
        errors = []   
        
        while self.cursor < len(self.source_code):
            self._skip_ignorable_whitespace()
            if self.cursor >= len(self.source_code): 
                break 
                
            start_cursor = self.cursor
            start_line, start_col = self.line, self.col
            
            lexeme, result, accepted_states = self._get_next_token()
            
            if lexeme is None:
                error_tuple = result 
                formatted_err = lexer_errors.format_error(error_tuple)
                
                advance_amount = 0
                # --- Error Recovery ---
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
                
                # Cursor Adjustment
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
                    # Standard panic (1 char)
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
            
            end_cursor = result
            
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
            
            for char in lexeme:
                if char == '\n': 
                    self.line += 1
                    self.col = 1
                elif char == '\t':
                    self.col += 4
                else: 
                    self.col += 1

        tokens = tokenize(lexemes, metadata)
        return tokens, errors