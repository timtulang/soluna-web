#
# lexer_errors.py
#
# This module centralizes all error detection and formatting for my lexer.
# When the lexer's FA simulation fails, it calls functions from this
# module to determine *why* it failed and to create a
# human-readable error message.
#

import sys
from .td import STATES # I need STATES to check if states are end states

#
# --- Error State Definitions ---
# I've defined these sets to easily check if the lexer died
# in a specific "unfinished" state.
#

# State 240 is the state right after seeing a '.', (e.g., "123.")
# It's waiting for a digit. If it dies here, it's an unfinished float.
UNFINISHED_FLUX_STATES = {240}

# States 304/308 are inside a string literal.
UNCLOSED_STRING_STATES = {304, 308}

# States 298/302 are inside a char literal.
UNCLOSED_CHAR_STATES = {298, 302}

# States 314/315 are inside a multi-line comment.
UNCLOSED_COMMENT_STATES = {314, 315}


def check_for_dead_end_error(last_good_active_states, current_lexeme, start_metadata):
    """
    I call this function when the FA runs out of transitions, but *before*
    it found an "accepted" lexeme. (e.g., "123." or "::my_la")
    This checks if the state it died in was a known "unfinished" state.
    
    Args:
        last_good_active_states (set): The set of state IDs active just before failure.
        current_lexeme (str): The text of the lexeme being processed.
        start_metadata (tuple): (line, col, start_index, end_index)
        
    Returns:
        An error tuple (type, location, data) or None.
    """
    line, col, _, _ = start_metadata
    
    # Check for unfinished float (e.g., "123.")
    if not last_good_active_states.isdisjoint(UNFINISHED_FLUX_STATES):
        return ('UNFINISHED_FLUX', (line, col), current_lexeme)
        
    # Other dead-end errors could be added here
    
    return None

def check_for_total_failure_error(
    last_good_active_states,
    char_that_killed_it,
    current_lexeme,
    start_metadata,
    cursor_char 
):
    """
    I call this function when the lexer fails completely from its
    starting position or when a valid lexeme is followed by an
    invalid delimiter.
    
    Args:
        last_good_active_states (set): The set of state IDs active just before failure.
        char_that_killed_it (str): The lookahead char that caused the FA to stop.
        current_lexeme (str): The text of the lexeme being processed.
        start_metadata (tuple): (line, col, start_index, end_index)
        cursor_char (str): The *actual* character at the cursor (for UNRECOGNIZED_CHAR).
        
    Returns:
        A formatted error tuple (type, location, data).
    """
    line, col, _, _ = start_metadata

    # --- Invalid Delimiter Check ---
    # This is for when a *valid* token was found, but the *next*
    # character was not a valid delimiter. (e.g., "letx" or "123a")
    if char_that_killed_it != '\0' and last_good_active_states:
        # Check if *all* states we were in were end states.
        all_were_end_states = all(
            state_id in STATES and STATES[state_id].isEnd
            for state_id in last_good_active_states
        )
        if all_were_end_states:
            # This is the classic invalid delimiter error.
            return ('INVALID_DELIMITER', (line, col), (current_lexeme, char_that_killed_it))

    # --- End-of-File (EOF) Error Check ---
    # This block handles errors that happen when the file ends
    # unexpectedly (e.g., an unclosed string).
    if char_that_killed_it == '\0':
        if not last_good_active_states.isdisjoint(UNCLOSED_STRING_STATES):
            return ('UNCLOSED_STRING', (line, col), current_lexeme)
        if not last_good_active_states.isdisjoint(UNCLOSED_CHAR_STATES):
            return ('UNCLOSED_CHAR', (line, col), current_lexeme)
        if not last_good_active_states.isdisjoint(UNCLOSED_COMMENT_STATES):
            return ('UNCLOSED_COMMENT', (line, col), current_lexeme)

    # --- Catch-All: Unrecognized Character ---
    # If no other error condition was met, it means the character
    # at the *start* of the cursor (cursor_char) is not a valid
    # starting character for any token. (e.g., '$' or '?')
    return ('UNRECOGNIZED_CHAR', (line, col), cursor_char)

def format_error(error_tuple):
    """
    This is a helper function to convert my internal error tuples
    into a clean, serializable dictionary. This is what I'll
    eventually send to the user/frontend.
    
    Args:
        error_tuple (tuple): The (type, location, data) tuple from a check function.
        
    Returns:
        A dictionary with "type", "line", "col", and "message".
    """
    error_type, (line, col), data = error_tuple
    
    error_info = {"type": error_type, "line": line, "col": col}
    
    if error_type == 'UNFINISHED_FLUX':
        error_info["message"] = f"Unfinished float literal '{data}'."
    elif error_type == 'INVALID_DELIMITER':
        lexeme, delim = data
        # Adjust column to point *after* the lexeme, at the bad delimiter.
        error_info["col"] = col + len(lexeme)
        error_info["message"] = f"Invalid delimiter '{delim}' after token '{lexeme}'."
    elif error_type in ['UNCLOSED_STRING', 'UNCLOSED_COMMENT']:
        error_info["message"] = f"Unclosed {error_type.split('_')[1].lower()}."
    elif error_type == 'UNCLOSED_CHAR':
        error_info["message"] = "Unclosed char literal."
    else: # UNRECOGNIZED_CHAR
        error_info["message"] = f"Unrecognized character '{data}'."

    return error_info