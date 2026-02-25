# app/semantics/symbol_table.py
import re
from .errors import SemanticError

class SymbolTable:
    def __init__(self):
        # Scope stack: Index 0 is Global.
        # Each scope is a dict: { "name": { "type": "...", "category": "...", ... } }
        self.scopes = [{}] 
        self.current_scope_level = 0
        self.in_loop_counter = 0 

    # --- SCOPING ---
    def enter_scope(self):
        self.scopes.append({})
        self.current_scope_level += 1

    def exit_scope(self):
        if self.current_scope_level > 0:
            self.scopes.pop()
            self.current_scope_level -= 1

    def is_global(self):
        return self.current_scope_level == 0

    def enter_loop(self):
        self.in_loop_counter += 1

    def exit_loop(self):
        self.in_loop_counter -= 1

    def is_inside_loop(self):
        return self.in_loop_counter > 0

    # --- IDENTIFIERS ---
    def validate_identifier(self, name, line, col):
        if not (1 <= len(name) <= 20):
             raise SemanticError(f"Identifier '{name}' must be 1-20 characters long.", line, col)
        
        # Regex: Starts with [a-z_], followed by [a-zA-Z0-9]
        if not re.match(r'^[a-z_][a-zA-Z0-9]*$', name):
             raise SemanticError(f"Invalid identifier format '{name}'. Must start with lowercase/underscore.", line, col)

    def declare(self, name, symbol_info, line, col, is_local=False):
        self.validate_identifier(name, line, col)
        
        target_scope = self.scopes[-1] if is_local else self.scopes[0]

        if name in self.scopes[-1]:
            raise SemanticError(f"Identifier '{name}' is already declared in this scope.", line, col)

        if name in target_scope:
            raise SemanticError(f"Identifier '{name}' is already declared in this scope.", line, col)
            
        target_scope[name] = symbol_info

    def lookup(self, name):
        # Search from inner-most to outer-most
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None