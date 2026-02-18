from .errors import SemanticError

class SymbolTable:
    def __init__(self):
        # Stack of scopes. 
        # Index 0 = Global Scope.
        # Each scope is a dict: { "var_name": {type, is_const, ...} }
        self.scopes = [{}] 

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare(self, name, type_name, is_const, line, col):
        current_scope = self.scopes[-1]
        
        # Rule: Identifiers must be unique in the current scope
        if name in current_scope:
            raise SemanticError(f"Variable '{name}' is already declared in this scope.", line, col)
        
        # Rule A.4: Identifier length 1-20 characters
        if len(name) > 20:
            raise SemanticError(f"Identifier '{name}' exceeds maximum length of 20 characters.", line, col)

        current_scope[name] = {
            "category": "variable",
            "type": type_name,
            "is_const": is_const
        }

    def declare_function(self, name, return_type, params, line, col):
        # Functions are usually declared in the global scope or current scope
        current_scope = self.scopes[-1]
        
        if name in current_scope:
            raise SemanticError(f"Function '{name}' is already declared.", line, col)

        current_scope[name] = {
            "category": "function",
            "type": return_type,  # Return type
            "params": params      # List of param types e.g. ['kai', 'flux']
        }

    def lookup(self, name):
        # Search from inner-most (local) to outer-most (global)
        # This implicitly handles Shadowing (Rule 1497)
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None