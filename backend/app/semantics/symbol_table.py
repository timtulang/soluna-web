# app/semantics/symbol_table.py
import re
from .errors import SemanticError

class SymbolTable:
    """
    SYMBOL TABLE: Keeps Track of All Declared Variables and Functions
    
    A symbol table is like a dictionary in a book. When you declare a variable,
    it gets added to the "dictionary". When you use that variable, we look it up
    in the dictionary to make sure it exists and has the right type.
    
    KEY CONCEPTS:
    
    1. SCOPES: Variables can be declared at different "levels"
       - Global scope (level 0): Variables declared at the top of the program
       - Function scope (level 1): Variables declared inside a function
       - Block scope (level 2+): Variables declared inside if/while/for blocks
       
       When a scope exits, its variables "disappear" (they can't be used outside that scope)
    
    2. SYMBOL INFO: Each symbol (variable/function) stores:
       - category: "variable" or "function"
       - type: "kai", "flux", "let", etc.
       - is_const: True if declared with 'zeta' keyword
       - is_initialized: True if it was given a starting value
       - is_used: True if the variable was actually referenced somewhere
       - line/col: Where was it declared? (for error reporting)
    
    3. LOOP TRACKING: Keeps count of how deep we are in nested loops
       (This is needed because 'break' can only be used inside loops)
    """
    
    def __init__(self):
        """
        Initialize the symbol table at the start of analysis.
        
        The scope stack starts with just one empty scope (the global scope).
        As we enter functions and blocks, we push new scopes.
        As we exit them, we pop the scopes.
        """
        # List of scope dictionaries: scopes[0] is global, scopes[-1] is current
        # Each scope is a dict: { "varname": {symbol_info}, "funcname": {symbol_info}, ... }
        self.scopes = [{}] 
        
        # How deep are we in nested scopes? 0 = global, 1 = inside function, 2+ = inside blocks
        self.current_scope_level = 0
        
        # How many nested loops are we inside? 0 = not in loop, 1 = 1 loop, 2+ = nested loops
        self.in_loop_counter = 0 

    # ========================================================================
    # SCOPING: Managing nested scopes (global, function, block)
    # ========================================================================
    
    def enter_scope(self):
        """
        Enter a new scope (like opening a new chapter in the dictionary).
        
        Called when entering:
        - A function body
        - An if/else block
        - A loop body
        
        After this, all declarations are in the NEW scope.
        Example:
            Scopes: [{}]                    Global scope
            Call enter_scope()
            Scopes: [{}, {}]                Global + Function scope
            Call enter_scope() again
            Scopes: [{}, {}, {}]            Global + Function + If block scope
        """
        # Add a new empty scope to the stack
        self.scopes.append({})
        # Increment the depth counter
        self.current_scope_level += 1

    def exit_scope(self):
        """
        Exit the current scope (closing the chapter, returning to parent scope).
        
        Called when exiting:
        - A function body
        - An if/else block
        - A loop body
        
        All variables declared in this scope become inaccessible.
        Returns the scope that just exited (so we can check for unused variables).
        
        Example:
            Scopes: [{}, {}, {}]
            Call exit_scope()
            Scopes: [{}, {}]
            Returns: {}  (the popped scope)
        """
        if self.current_scope_level > 0:
            # Pop the most recent scope (the innermost one)
            popped_scope = self.scopes.pop() 
            # Decrement the depth counter
            self.current_scope_level -= 1
            # Return the popped scope (so caller can check for unused variables)
            return popped_scope 
        return {}
    
    def is_global(self):
        """Check if we're at the global scope (not inside any function or block)."""
        return self.current_scope_level == 0

    # ========================================================================
    # LOOP TRACKING: Knowing when we're inside loops (for 'break' validation)
    # ========================================================================
    
    def enter_loop(self):
        """
        Enter a loop (while, for, repeat-until).
        
        This counter lets us know if 'break' statements are legal.
        You can only use 'break' inside a loop, not in regular code.
        """
        self.in_loop_counter += 1

    def exit_loop(self):
        """
        Exit a loop.
        
        Decrements the loop counter. After all nested loops are exited,
        'break' statements will be invalid again.
        """
        self.in_loop_counter -= 1

    def is_inside_loop(self):
        """
        Are we currently inside a loop?
        
        Returns True if we're nested inside any loop (while, for, or repeat-until).
        Used to validate that 'break' is only used in loops.
        """
        return self.in_loop_counter > 0

    # ========================================================================
    # IDENTIFIER VALIDATION: Checking variable name rules
    # ========================================================================
    
    def validate_identifier(self, name, line, col):
        """
        Check if a variable/function name follows Soluna's naming rules.
        
        RULES:
        1. Must be 1-20 characters long
        2. Must start with lowercase letter or underscore (a-z, _)
        3. Can contain letters, digits, and underscores (a-zA-Z0-9_)
        
        VALID names:     x, myVar, _private, count123
        INVALID names:   X (uppercase), my-var (hyphen), 123num (starts with digit)
        
        Raises: SemanticError if the name breaks the rules
        """
        # Check length
        if not (1 <= len(name) <= 20):
             raise SemanticError(f"Identifier '{name}' must be 1-20 characters long.", line, col)
        
        # Check format with regex: start with [a-z_], followed by [a-zA-Z0-9_]*
        # Example: "myVar_123" matches, "MyVar" doesn't (starts with uppercase)
        if not re.match(r'^[a-z_][a-zA-Z0-9]*$', name):
             raise SemanticError(f"Invalid identifier format '{name}'. Must start with lowercase/underscore.", line, col)

    # ========================================================================
    # DECLARATION & LOOKUP: Adding and finding symbols
    # ========================================================================
    
    def declare(self, name, symbol_info, line, col, is_local=False):
        """
        Declare a new variable or function.
        
        Adds it to the symbol table so we can look it up later.
        
        Args:
            name: The variable/function name (e.g., "x", "myFunc")
            symbol_info: A dictionary with metadata like:
                {
                    "category": "variable" or "function",
                    "type": "kai", "flux", "let", etc.,
                    "is_const": True if declared with 'zeta',
                    "is_initialized": True if it has a starting value,
                    "params": [...] (for functions)
                }
            line: Line number where it was declared (for error reporting)
            col: Column number where it was declared
            is_local: True = add to current scope, False = add to global scope
        
        Raises: SemanticError if:
            - Name doesn't follow identifier rules
            - Name is already declared in the same scope (redeclaration)
        
        Example:
            declare("x", {"category": "variable", "type": "kai"}, 5, 10, is_local=True)
            This adds variable 'x' to the current scope.
        """
        # First, validate the name follows the rules
        self.validate_identifier(name, line, col)
        
        # Decide which scope to add it to
        # If is_local=True, add to current (innermost) scope
        # If is_local=False, add to global (outermost) scope
        target_scope = self.scopes[-1] if is_local else self.scopes[0]

        # Check if already declared in THIS scope (not in parent scopes)
        if name in target_scope:
            raise SemanticError(f"Identifier '{name}' is already declared in this scope.", line, col)
            
        # Add line/col info for error messages and tracking usage
        symbol_info["line"] = line
        symbol_info["col"] = col
        symbol_info["is_used"] = False  # Not used yet (will be set to True when we see it referenced)
        
        # Store it in the target scope
        target_scope[name] = symbol_info

    def lookup(self, name):
        """
        Look up a variable or function by name.
        
        Searches from the CURRENT scope backwards to the GLOBAL scope.
        This implements variable shadowing: if a name exists in multiple scopes,
        we get the innermost one.
        
        Args:
            name: The variable/function name to find
        
        Returns:
            The symbol_info dictionary if found, or None if not found
        
        Side Effect:
            Marks the symbol as "used" (sets is_used = True)
            This helps us warn about unused variables.
        
        Example:
            Global scope:  {"x": {...}, "myFunc": {...}}
            Function scope: {"y": {...}}
            
            lookup("x") → Returns global x (found going backwards)
            lookup("y") → Returns function y (found in current scope)
            lookup("z") → Returns None (not found in any scope)
        """
        # Search from innermost (current) scope to outermost (global)
        for scope in reversed(self.scopes):
            if name in scope:
                # Found it! Mark as used
                scope[name]["is_used"] = True 
                # Return the symbol info
                return scope[name]
        # Not found in any scope
        return None