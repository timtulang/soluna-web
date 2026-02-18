# app/semantics/symbol_table.py
from .errors import SemanticError

class SymbolTable:
    def __init__(self):
        # Stack of scopes. Index 0 is Global.
        # Structure: { "name": { "type": "kai", "is_const": False, "category": "var" } }
        self.scopes = [{}] 

    # --- SCOPING SECTIONS ---
    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def is_global(self):
        return len(self.scopes) == 1

    # --- IDENTIFIERS SECTION ---
    def validate_identifier_name(self, name, line, col):
        # Rule A.4: Identifiers must have a length of 1-20 characters
        if not (1 <= len(name) <= 20):
            raise SemanticError(f"Identifier '{name}' must be between 1 and 20 characters.", line, col)
        
        # Rule A.5: Identifiers must not be reserved words (Handled by Lexer usually, but safe to check)
        # Rule A.3: No special symbols (Handled by Lexer)

    def declare(self, name, type_name, is_const, line, col):
        self.validate_identifier_name(name, line, col)
        
        current_scope = self.scopes[-1]
        
        # Rule A.6: Identifiers must be unique within scope
        if name in current_scope:
            raise SemanticError(f"Identifier '{name}' is already declared in this scope.", line, col)
        
        current_scope[name] = {
            "category": "variable",
            "type": type_name,
            "is_const": is_const
        }

    def declare_function(self, name, return_type, params, line, col):
        self.validate_identifier_name(name, line, col)
        
        # Functions are typically declared in the global scope or current scope
        # Rule: No Hoisting (must be declared before use)
        current_scope = self.scopes[-1] 
        
        if name in current_scope:
            raise SemanticError(f"Function '{name}' is already declared.", line, col)

        current_scope[name] = {
            "category": "function",
            "return_type": return_type,
            "params": params # List of parameter types
        }

    def lookup(self, name):
        # Searches from inner-most to outer-most (Shadowing allowed)
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None