class SemanticError(Exception):
    """
    SEMANTIC ERROR: Errors that occur during semantic analysis
    
    The semantic analyzer checks if code is "meaningful" - things like:
    - Using a variable before declaring it
    - Type mismatches (assigning a string to an integer)
    - Calling a function that doesn't exist
    - Using 'break' outside of a loop
    - Declaring the same variable twice in the same scope
    
    This class reports where the error occurred (line and column) for better debugging.
    
    Example:
        SemanticError("Variable 'x' is not declared", line=5, col=10)
        Output: "Semantic Error at [5:10]: Variable 'x' is not declared"
    """
    def __init__(self, message, line=0, col=0):
        # The error message (what went wrong?)
        self.message = message
        # Line number in source file (1-indexed)
        self.line = line
        # Column number in that line (for pinpointing the exact position)
        self.col = col
        # Call parent Exception class to format the message nicely
        super().__init__(f"Semantic Error at [{line}:{col}]: {message}")