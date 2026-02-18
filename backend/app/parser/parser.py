class Token:
    """
    Standard token object. 
    Keeps track of line/col for error messages so we don't go insane debugging.
    """
    def __init__(self, type_name, value, line=0, col=0):
        self.type = type_name
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type}, '{self.value}')"

class EarleyItem:
    """
    Represents a single state in the chart.
    production: The rule we're trying to match.
    dot_index: How much of the rule we've matched (the dot position).
    start_index: Where in the input stream we started matching this rule.
    """
    def __init__(self, production, dot_index, start_index):
        self.production = production
        self.dot_index = dot_index
        self.start_index = start_index

    # What symbol is the dot sitting in front of?
    def next_symbol(self):
        if self.dot_index < len(self.production.rhs):
            return self.production.rhs[self.dot_index]
        return None

    # Is the dot at the end? (Rule matched!)
    def is_complete(self):
        return self.dot_index >= len(self.production.rhs)

    # Equality check for set deduplication (Earley relies on this).
    def __eq__(self, other):
        return (self.production == other.production and
                self.dot_index == other.dot_index and
                self.start_index == other.start_index)

    def __hash__(self):
        return hash((self.production, self.dot_index, self.start_index))

    def __repr__(self):
        rhs = list(map(str, self.production.rhs))
        rhs.insert(self.dot_index, ".")
        return f"[{self.start_index}] {self.production.lhs} -> {' '.join(rhs)}"

class EarleyParser:
    def __init__(self, grammar, start_symbol):
        self.grammar = grammar
        self.start_symbol = start_symbol
        self.chart = []

    def parse(self, tokens):
        # The chart is a list of sets. 
        # chart[i] contains all valid partial parses after processing token i.
        self.chart = [set() for _ in range(len(tokens) + 1)]
        
        # Init: Add the start symbol to chart[0]
        if self.start_symbol not in self.grammar:
            raise Exception(f"Start symbol '{self.start_symbol}' not found in grammar.")
            
        for rule in self.grammar[self.start_symbol]:
            self.chart[0].add(EarleyItem(rule, 0, 0))

        # We track this to give better error messages (where did it stall?).
        max_processed_index = 0

        # Main Loop: Iterate through each token position
        for i in range(len(tokens) + 1):
            
            # If the chart is empty, it means no rule could be applied. Syntax error.
            if len(self.chart[i]) == 0 and i > 0:
                self._handle_error(i - 1, tokens)
                return False

            max_processed_index = i
            processed = set()
            
            # Iterate until no new items are added to the current chart set.
            while True:
                # IMPORTANT: Use a LIST copy. We're modifying the set while iterating.
                # Without this, Python throws "Set changed size during iteration".
                current_chart_items = list(self.chart[i])
                added_something = False
                
                for item in current_chart_items:
                    if item in processed:
                        continue
                    
                    if not item.is_complete():
                        next_sym = item.next_symbol()
                        if next_sym in self.grammar:
                            # 1. PREDICT: We expect a non-terminal (like <statement>).
                            # Add all possible rules for <statement> to the chart.
                            self._predict(next_sym, i)
                        elif i < len(tokens):
                            # 2. SCAN: We expect a terminal (like 'kai').
                            # If the next token matches, advance state to chart[i+1].
                            self._scan(item, tokens[i], i)
                    else:
                        # 3. COMPLETE: We finished a rule.
                        # Go back to where it started and advance the parent rule.
                        self._complete(item, i)
                    
                    processed.add(item)
                
                if len(self.chart[i]) > len(current_chart_items):
                    added_something = True
                
                if not added_something:
                    break
        
        # Check if the start symbol is fully matched in the final chart.
        if self._check_success(tokens):
            return True
        else:
            self._handle_error(len(tokens), tokens)
            return False

    def _predict(self, non_terminal, index):
        for rule in self.grammar[non_terminal]:
            new_item = EarleyItem(rule, 0, index)
            self.chart[index].add(new_item)

    def _scan(self, item, token, index):
        next_sym = item.next_symbol()
        # Check if the token type matches what the rule expects
        if next_sym == token.type:
            new_item = EarleyItem(item.production, item.dot_index + 1, item.start_index)
            self.chart[index + 1].add(new_item)

    def _complete(self, completed_item, index):
        lhs = completed_item.production.lhs
        origin = completed_item.start_index
        
        # Again, list copy is crucial here for nullable rules (rules that can be empty).
        # If origin == index, we are reading and writing to the same set.
        items_to_check = list(self.chart[origin])
        
        for item in items_to_check:
            # If 'item' was waiting for the rule we just finished ('lhs'), advance it.
            if item.next_symbol() == lhs:
                new_item = EarleyItem(item.production, item.dot_index + 1, item.start_index)
                self.chart[index].add(new_item)

    def _check_success(self, tokens):
        # Look at the final chart state. Did we finish the 'program' rule starting at 0?
        for item in self.chart[-1]:
            if (item.production.lhs == self.start_symbol and 
                item.is_complete() and 
                item.start_index == 0):
                return True
        return False

    def _handle_error(self, error_index, tokens):
        """
        Builds a decent error message by checking what the parser WAS expecting
        when it crashed.
        """
        if error_index < len(tokens):
            token = tokens[error_index]
            line = token.line
            col = token.col
            unexpected_desc = f"'{token.value}'"
        else:
            # Error at EOF
            if len(tokens) > 0:
                last_token = tokens[-1]
                line = last_token.line
                col = last_token.col + len(str(last_token.value))
            else:
                line = 1
                col = 1
            unexpected_desc = "End of Input"

        expected_symbols = set()
        
        # Check the chart state where it failed. What were we looking for?
        if error_index < len(self.chart):
            for item in self.chart[error_index]:
                next_sym = item.next_symbol()
                # We only care about terminals (actual tokens) for the error message
                if next_sym and next_sym not in self.grammar:
                    expected_symbols.add(f"'{next_sym}'")

        expected_str = ", ".join(sorted(expected_symbols))

        error_msg = (
            f"Syntax Error at Line {line}, Col {col}: "
            f"Unexpected {unexpected_desc}. "
            f"Expected one of: [{expected_str}]"
        )
        raise Exception(error_msg)