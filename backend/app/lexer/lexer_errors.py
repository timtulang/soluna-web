# backend/app/lexer_errors.py (Modified)
import sys
from .td import STATES

# --- State Definitions (Magic Numbers are up-to-date) ---
UNFINISHED_FLUX_STATES = {240}
UNCLOSED_STRING_STATES = {304, 308}
UNCLOSED_CHAR_STATES = {298, 302}
UNCLOSED_COMMENT_STATES = {314, 315}


def check_for_dead_end_error(last_good_active_states, current_lexeme, start_metadata):
    line, col, _, _ = start_metadata
    if not last_good_active_states.isdisjoint(UNFINISHED_FLUX_STATES):
        return ('UNFINISHED_FLUX', (line, col), current_lexeme)
    return None


def check_for_total_failure_error(
    last_good_active_states,
    char_that_killed_it,
    current_lexeme,
    start_metadata
):
    line, col, _, _ = start_metadata
    if char_that_killed_it != '\0' and last_good_active_states:
        all_were_end_states = all(
            state_id in STATES and STATES[state_id].isEnd
            for state_id in last_good_active_states
        )
        if all_were_end_states:
            return ('INVALID_DELIMITER', (line, col), (current_lexeme, char_that_killed_it))

    if char_that_killed_it == '\0':
        if not last_good_active_states.isdisjoint(UNCLOSED_STRING_STATES):
            return ('UNCLOSED_STRING', (line, col), current_lexeme)
        if not last_good_active_states.isdisjoint(UNCLOSED_CHAR_STATES):
            return ('UNCLOSED_CHAR', (line, col), current_lexeme)
        if not last_good_active_states.isdisjoint(UNCLOSED_COMMENT_STATES):
            return ('UNCLOSED_COMMENT', (line, col), current_lexeme)

    return ('UNRECOGNIZED_CHAR', (line, col), char_that_killed_it)


def format_error(error_tuple):
    """ Returns a dictionary representing the error instead of printing. """
    error_type, (line, col), data = error_tuple
    
    error_info = {"type": error_type, "line": line, "col": col}
    
    if error_type == 'UNFINISHED_FLUX':
        error_info["message"] = f"Unfinished float literal '{data}'."
    elif error_type == 'INVALID_DELIMITER':
        lexeme, delim = data
        error_info["col"] = col + len(lexeme) # Adjust column to point at the delimiter
        error_info["message"] = f"Invalid delimiter '{delim}' after token '{lexeme}'."
    elif error_type in ['UNCLOSED_STRING', 'UNCLOSED_COMMENT']:
        error_info["message"] = f"Unclosed {error_type.split('_')[1].lower()}."
    elif error_type == 'UNCLOSED_CHAR':
        error_info["message"] = "Unclosed char literal."
    else: # UNRECOGNIZED_CHAR
        error_info["message"] = f"Unrecognized character '{data}'."

    return error_info