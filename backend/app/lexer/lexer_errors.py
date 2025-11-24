#
# lexer_errors.py
#
import sys
from .td import STATES 

# State 240 is the state right after seeing a '.', (e.g., "123.")
UNFINISHED_FLUX_STATES = {240}

# States 304/308 are inside a string literal.
UNCLOSED_STRING_STATES = {304, 308}

# States 298/302 are inside a char literal.
UNCLOSED_CHAR_STATES = {298, 302}

# States 314/315 are inside a multi-line comment.
UNCLOSED_COMMENT_STATES = {314, 315, 3150}


def check_for_dead_end_error(last_good_active_states, current_lexeme, start_metadata):
    """
    Checks for errors where the lexer dies in a non-end state.
    """
    line, col, _, _ = start_metadata
    
    if not last_good_active_states.isdisjoint(UNFINISHED_FLUX_STATES):
        return ('UNFINISHED_FLUX', (line, col), current_lexeme)
        
    return None

def check_for_total_failure_error(
    last_good_active_states,
    char_that_killed_it,
    current_lexeme,
    start_metadata,
    cursor_char 
):
    """
    Checks for errors where NO valid token was found.
    """
    line, col, _, _ = start_metadata

    # --- NEW FIX ---
    # Check if we died in an unfinished float state (State 240).
    # This handles "999." where "999" is no longer accepted as an int.
    if not last_good_active_states.isdisjoint(UNFINISHED_FLUX_STATES):
        return ('UNFINISHED_FLUX', (line, col), current_lexeme)

    # --- Invalid Delimiter Check ---
    if char_that_killed_it != '\0' and last_good_active_states:
        potential_end_state_reachable = False
        for state_id in last_good_active_states:
            if state_id not in STATES: continue
            
            if STATES[state_id].isEnd:
                potential_end_state_reachable = True
                break

            for branch_id in STATES[state_id].branches:
                if branch_id in STATES and STATES[branch_id].isEnd:
                    potential_end_state_reachable = True
                    break
            if potential_end_state_reachable:
                break

        if potential_end_state_reachable:
            return ('INVALID_DELIMITER', (line, col), (current_lexeme, char_that_killed_it))

    # --- End-of-File (EOF) Error Check ---
    if char_that_killed_it == '\0':
        if not last_good_active_states.isdisjoint(UNCLOSED_STRING_STATES):
            return ('UNCLOSED_STRING', (line, col), current_lexeme)
        if not last_good_active_states.isdisjoint(UNCLOSED_CHAR_STATES):
            return ('UNCLOSED_CHAR', (line, col), current_lexeme)
        if not last_good_active_states.isdisjoint(UNCLOSED_COMMENT_STATES):
            return ('UNCLOSED_COMMENT', (line, col), current_lexeme)

    # --- Catch-All: Unrecognized Character ---
    return ('UNRECOGNIZED_CHAR', (line, col), cursor_char)

def format_error(error_tuple):
    error_type, (line, col), data = error_tuple
    
    error_info = {"type": error_type, "line": line, "col": col}
    
    if error_type == 'UNFINISHED_FLUX':
        error_info["message"] = f"Unfinished float literal '{data}'."
    elif error_type == 'INVALID_DELIMITER':
        lexeme, delim = data
        error_info["col"] = col + len(lexeme)
        error_info["message"] = f"Invalid delimiter '{delim}' after token \"{lexeme}\"."
    elif error_type in ['UNCLOSED_STRING', 'UNCLOSED_COMMENT']:
        error_info["message"] = f"Unclosed {error_type.split('_')[1].lower()}."
    elif error_type == 'UNCLOSED_CHAR':
        error_info["message"] = "Unclosed char literal."
    else: 
        error_info["message"] = f"Unrecognized character '{data}'."

    return error_info