class Token:
    """
    WHAT IS A TOKEN?
    
    A token is a meaningful piece of source code. Think of it like a word in a sentence.
    
    Examples:
    - "kai" is a token (the integer type keyword)
    - "5" is a token (an integer literal)
    - "x" is a token (an identifier/variable name)
    - "+" is a token (an operator)
    
    Each token stores:
    - type: What kind of token is it? (keyword, number, operator, etc.)
    - value: The actual text (what does it say?)
    - line/col: Where in the source file did this token appear? (for error reporting)
    """
    def __init__(self, type_name, value, line=0, col=0):
        self.type = type_name  # What kind of token? (e.g., "kai", "integer", "+")
        self.value = value     # The actual text (e.g., "5", "myVariable", "+")
        self.line = line       # Which line in the source file? (1-indexed)
        self.col = col         # Which column in that line? (for pinpointing errors)

    def __repr__(self):
        # Easy-to-read format for printing: Token(kai, 'kai')
        return f"Token({self.type}, '{self.value}')"


class EarleyItem:
    """
    EARLEY ITEM: A Single Step in Parsing
    
    An EarleyItem represents the parser's current progress in matching a grammar rule.
    
    Analogy: If a grammar rule is a recipe, an EarleyItem is like a recipe you're 
    following with one finger pointing to where you are in the recipe.
    
    Example:
    Rule: statement -> if condition block
    Item: [2] statement -> if condition . block
           ^                              ^
           |                              |
    start_index (where this rule started)  dot_index (how far we've gotten)
    
    The dot (.) shows progress through the rule.
    """
    def __init__(self, production, dot_index, start_index):
        self.production = production  # The grammar rule we're trying to match
        self.dot_index = dot_index    # How many symbols of the rule have we matched?
        self.start_index = start_index  # Where did we start matching this rule in the input?

    def next_symbol(self):
        """What's the next thing the parser needs to find?"""
        if self.dot_index < len(self.production.rhs):
            # Return the symbol the dot is sitting in front of
            return self.production.rhs[self.dot_index]
        return None  # Dot is at the end, nothing left to match

    def is_complete(self):
        """Have we finished matching this rule? (Is the dot at the end?)"""
        return self.dot_index >= len(self.production.rhs)

    # Equality & Hashing (needed so we can store items in sets and avoid duplicates)
    def __eq__(self, other):
        return (self.production == other.production and
                self.dot_index == other.dot_index and
                self.start_index == other.start_index)

    def __hash__(self):
        return hash((self.production, self.dot_index, self.start_index))

    def __repr__(self):
        # Human-readable format for debugging
        rhs = list(map(str, self.production.rhs))
        rhs.insert(self.dot_index, ".")  # Insert dot at current position
        return f"[{self.start_index}] {self.production.lhs} -> {' '.join(rhs)}"


class EarleyParser:
    """
    THE EARLEY PARSER: A Universal Parsing Algorithm
    
    The Earley Parser can parse ANY context-free grammar (almost any language).
    It works in a single left-to-right pass, maintaining a "chart" of possible parses.
    
    THE CHART:
    - A list of sets (one set per position in the input)
    - chart[i] contains all valid partial parses after consuming the first i tokens
    
    THE ALGORITHM (Three Main Operations):
    1. PREDICT: When we expect a non-terminal, add all possible rules for it
    2. SCAN: When we expect a terminal (token), check if it matches and advance
    3. COMPLETE: When we finish a rule, update all waiting parent rules
    
    Example Input: "kai x = 5;"
    The parser builds up the chart step by step, until it recognizes the whole program.
    """
    
    def __init__(self, grammar, start_symbol):
        self.grammar = grammar          # The grammar dictionary
        self.start_symbol = start_symbol  # Where to start parsing (usually "program")
        self.chart = []                 # The chart (built during parsing)

    def parse(self, tokens):
        """
        Main entry point. Try to parse the token stream.
        
        Returns: True if successful, False if syntax error
        """
        # Create the chart: one set for each position (0 to len(tokens))
        self.chart = [set() for _ in range(len(tokens) + 1)]
        
        # Initialize: Add start symbol to chart[0]
        # This represents "we want to match 'program' starting at position 0"
        if self.start_symbol not in self.grammar:
            raise Exception(f"Start symbol '{self.start_symbol}' not found in grammar.")
            
        for rule in self.grammar[self.start_symbol]:
            # Create an item: [0] program -> . global_dec func_dec statements
            # (The dot is at the beginning - we haven't matched anything yet)
            self.chart[0].add(EarleyItem(rule, 0, 0))

        # Process each position in the token stream
        for i in range(len(tokens) + 1):
            
            # If chart[i] is empty, it means no rule could be applied
            # This is a syntax error
            if len(self.chart[i]) == 0 and i > 0:
                self._handle_error(i - 1, tokens)
                return False

            processed = set()  # Track which items we've already processed
            
            # Keep applying operations until no new items are added
            # This is necessary for nullable rules (rules that can match zero symbols)
            while True:
                # CRITICAL: Convert to list to avoid "set changed size during iteration" errors
                # (We're modifying chart[i] while iterating over it)
                current_chart_items = list(self.chart[i])
                added_something = False
                
                for item in current_chart_items:
                    if item in processed:
                        continue  # Skip if we've already handled this item
                    
                    if not item.is_complete():
                        # The item is incomplete (dot is not at the end)
                        next_sym = item.next_symbol()
                        
                        if next_sym in self.grammar:
                            # PREDICT: We expect a non-terminal (a grammar rule)
                            # Add all possible rules for this non-terminal
                            self._predict(next_sym, i)
                        elif i < len(tokens):
                            # SCAN: We expect a terminal (a token)
                            # Check if the next input token matches what we expect
                            self._scan(item, tokens[i], i)
                    else:
                        # COMPLETE: We finished matching a rule!
                        # Notify all parent rules that this rule succeeded
                        self._complete(item, i)
                    
                    processed.add(item)
                
                # If chart[i] got bigger, we added new items and need to process them
                if len(self.chart[i]) > len(current_chart_items):
                    added_something = True
                
                # Stop looping if nothing was added (convergence)
                if not added_something:
                    break
        
        # Check if we successfully parsed the entire input
        if self._check_success(tokens):
            return True
        else:
            self._handle_error(len(tokens), tokens)
            return False

    def _predict(self, non_terminal, index):
        """
        PREDICT OPERATION
        
        We're looking for a non-terminal (like 'statement' or 'expression').
        Add all possible grammar rules that could produce it.
        
        Example:
        If we're looking for 'statement', and the grammar has:
            statement -> assignment_statement
            statement -> conditional_statement
            statement -> ...
        Then add all of these to the chart[index].
        """
        for rule in self.grammar[non_terminal]:
            # Create a new item with the dot at the start of the rule
            new_item = EarleyItem(rule, 0, index)
            self.chart[index].add(new_item)

    def _scan(self, item, token, index):
        """
        SCAN OPERATION
        
        We're expecting a terminal (like 'kai' or '+' or an integer).
        Check if the current token matches what we expect.
        If it does, advance the dot and move to the next chart position.
        
        Example:
        Item: [0] statement -> . assignment_op identifier
        Token: 'kai'
        
        If 'assignment_op' matches the token type 'kai', advance:
        New Item: [0] statement -> assignment_op . identifier (move to chart[1])
        """
        next_sym = item.next_symbol()
        
        # Check if the token type matches what the rule expects
        if next_sym == token.type:
            # Match! Create a new item with the dot advanced by one
            new_item = EarleyItem(item.production, item.dot_index + 1, item.start_index)
            self.chart[index + 1].add(new_item)

    def _complete(self, completed_item, index):
        """
        COMPLETE OPERATION
        
        We just finished matching a rule. Now notify all the parent rules that
        were waiting for this rule.
        
        Example:
        We just completed: [5] expression -> . factor
        This rule started at position 5 and finished at position 7.
        
        Find all rules in chart[5] that were waiting for 'expression':
            [3] statement -> if . expression block
        
        And advance them:
            [3] statement -> if expression . block (move to chart[7])
        """
        lhs = completed_item.production.lhs  # What rule did we just complete?
        origin = completed_item.start_index  # Where did it start?
        
        # CRITICAL: Convert to list (same reason as in parse())
        # For nullable rules, origin == index (we're reading and writing the same set)
        items_to_check = list(self.chart[origin])
        
        for item in items_to_check:
            # Does this item expect the rule we just completed?
            if item.next_symbol() == lhs:
                # Yes! Advance its dot and add to chart[index]
                new_item = EarleyItem(item.production, item.dot_index + 1, item.start_index)
                self.chart[index].add(new_item)

    def _check_success(self, tokens):
        """
        Check if parsing was successful.
        
        Look at the final chart (after all tokens are consumed).
        Are there any completed rules for the start symbol that spanned the entire input?
        
        Success condition:
        - Rule: start_symbol
        - Is complete (dot at end)
        - Started at position 0
        - Ended at the last position
        """
        for item in self.chart[-1]:
            if (item.production.lhs == self.start_symbol and 
                item.is_complete() and 
                item.start_index == 0):
                return True
        return False

    def _handle_error(self, error_index, tokens):
        """
        Generate a helpful error message when parsing fails.
        
        Tell the user:
        1. Where the error occurred (line and column)
        2. What token caused the problem
        3. What the parser was expecting instead
        """
        # Get the problematic token
        if error_index < len(tokens):
            token = tokens[error_index]
            line = token.line
            col = token.col
            unexpected_desc = f"'{token.value}'"
        else:
            # Error at end of file
            if len(tokens) > 0:
                last_token = tokens[-1]
                line = last_token.line
                col = last_token.col + len(str(last_token.value))
            else:
                line = 1
                col = 1
            unexpected_desc = "End of Input"

        # Figure out what we were expecting
        # Look at the incomplete items in the chart at the error position
        expected_symbols = set()
        
        if error_index < len(self.chart):
            for item in self.chart[error_index]:
                next_sym = item.next_symbol()
                # Only show terminals (actual tokens) in the error message
                # (Non-terminals are internal to the grammar)
                if next_sym and next_sym not in self.grammar:
                    expected_symbols.add(f"'{next_sym}'")

        expected_str = ", ".join(sorted(expected_symbols))

        error_msg = (
            f"Syntax Error at Line {line}, Col {col}: "
            f"Unexpected {unexpected_desc}. "
            f"Expected one of: [{expected_str}]"
        )
        raise Exception(error_msg)