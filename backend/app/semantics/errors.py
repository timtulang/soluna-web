class SemanticError(Exception):
    def __init__(self, message, line=0, col=0):
        self.message = message
        self.line = line
        self.col = col
        super().__init__(f"Semantic Error at [{line}:{col}]: {message}")