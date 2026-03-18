# app/parser/tree_builder.py
from .parser import Token

class ParseTreeBuilder:
    """
    PARSE TREE BUILDER: Converting Parse Chart into a Tree
    
    The Earley parser produces a "chart" (a table of partial parse states).
    This builder converts that chart into a "parse tree" - a tree structure 
    that shows how the grammar rules were applied to the source code.
    
    PARSE TREE STRUCTURE:
    A parse tree is a tree where:
    - Leaf nodes (bottom) = tokens (actual source code: "kai", "5", "x", etc.)
    - Internal nodes (middle) = grammar rules (statement, expression, etc.)
    - Root node (top) = the start symbol (program)
    
    Example tree for "kai x = 5;":
    
                  program
                    |
            --------|--------
            |                |
        global_dec        statements
                          |
                      statement
                          |
                      var_dec
                    /  |  \  \
                  mut type var;
                      |      |
                      kai    id='x'
    
    The tree is represented as a dictionary with:
    - "type": The name of the rule (e.g., "statement", "expression")
    - "children": List of child nodes (or TOKEN for leaf nodes)
    - "start"/"end": Which tokens in the input this node spans
    """
    
    def __init__(self, parser, tokens):
        self.parser = parser  # The Earley parser (has the chart)
        self.tokens = tokens  # The original input tokens
        self.chart = parser.chart  # The parse chart (built during parsing)

    def build(self):
        """
        Entry point: Build the parse tree.
        
        Find the root of the tree (the completed start rule in the final chart),
        then recursively build the rest of the tree.
        """
        # 1. Find the completed start rule in chart[-1] (the final chart set)
        # This is the root of our parse tree
        root_item = None
        end_index = len(self.tokens)
        
        for item in self.chart[end_index]:
            # Look for: the start symbol, completed (dot at end), spanning the entire input
            if (item.production.lhs == self.parser.start_symbol and 
                item.is_complete() and 
                item.start_index == 0):
                root_item = item
                break
        
        if not root_item:
            # Parsing should have failed before we got here, but just in case...
            return None

        # 2. Recursively build the tree from the root
        return self._build_node(root_item, end_index)

    def _build_node(self, item, end_index):
        """
        Convert a completed EarleyItem into a tree node dictionary.
        
        A completed item represents a successfully matched grammar rule.
        We need to figure out which child nodes (sub-rules and tokens) 
        make up this rule.
        
        Args:
            item: A completed EarleyItem
            end_index: The position in the token stream where this rule ends
        
        Returns:
            A dictionary representing a tree node
        """
        start_index = item.start_index  # Where does this rule start?
        rhs = item.production.rhs  # The rule we matched (its right-hand side)
        
        # Create the tree node
        node = {
            "type": item.production.lhs,  # Name of the rule (e.g., "statement")
            "children": [],  # Will be filled with child nodes
            "start": start_index,  # Span in the token stream
            "end": end_index
        }

        # If this is an empty rule (Lambda/epsilon production),
        # it matches zero symbols, so just return it
        if not rhs:
            return node

        # Otherwise, find the children by working backwards through the rule.
        # This is the tricky part: we need to figure out where each symbol
        # in the rule corresponds to in the token stream.
        children = self._find_children(rhs, start_index, end_index)
        
        if children is None:
            raise Exception(f"Tree Reconstruction Failed at {item.production.lhs}")

        node["children"] = children
        return node

    def _find_children(self, symbols, start_index, end_index):
        """
        BACKTRACKING ALGORITHM: Figure out children from the span
        
        This is the core algorithm. We're given:
        - A list of symbols (what the rule expects): [A, B, C]
        - A span of input: (start_index...end_index)
        
        We need to find split points that divide the span into parts corresponding to each symbol:
        - A spans (start...split1)
        - B spans (split1...split2)
        - C spans (split2...end)
        
        Because multiple splits might be possible (the grammar is ambiguous),
        we use backtracking to try all possibilities.
        
        Args:
            symbols: List of symbols to match (e.g., ['expression', '+', 'term'])
            start_index: Where the span starts
            end_index: Where the span ends
        
        Returns:
            List of child nodes (one for each symbol), or None if no valid split exists
        """
        # BASE CASE: No more symbols to match
        if not symbols:
            # Success! Only if we've consumed all input
            return [] if start_index == end_index else None

        # RECURSIVE CASE: Work backwards (last symbol first)
        # This is more efficient than working forwards
        current_sym = symbols[-1]  # The LAST symbol in the rule
        remaining_syms = symbols[:-1]  # All symbols except the last

        # Try every possible position where the last symbol could start
        # Work backwards from end_index
        for split_point in range(end_index, start_index - 1, -1):
            
            # 1. Try to match the last symbol from split_point to end_index
            node = self._match_symbol(current_sym, split_point, end_index)
            
            if node is not None:
                # 2. If it matched, recursively try to match the remaining symbols
                # in the span (start_index...split_point)
                prefix_nodes = self._find_children(remaining_syms, start_index, split_point)
                
                if prefix_nodes is not None:
                    # Success! We found a valid split
                    # Combine the prefix and current symbol
                    return prefix_nodes + [node]

        # No valid split found
        return None

    def _match_symbol(self, symbol, start, end):
        """
        Try to match a single symbol (terminal or non-terminal) to a span.
        
        Two cases:
        1. Terminal (a token): Must match exactly one token
        2. Non-terminal (a rule): Look in the chart for a completed rule
        
        Args:
            symbol: The symbol to match (e.g., 'kai' or 'expression')
            start: Where the span starts
            end: Where the span ends
        
        Returns:
            A tree node (token or rule node), or None if no match
        """
        
        # CASE 1: TERMINAL (Token)
        # A terminal like 'kai' or '+' must match exactly ONE token
        if symbol not in self.parser.grammar:
            # Not a grammar rule, so it should be a token type
            if end - start == 1:
                # Span contains exactly one token
                token = self.tokens[start]
                
                # Check if the token type matches what we expect
                if token.type == symbol:
                    # Match! Return a leaf node
                    return {
                        "type": "TOKEN",
                        "token_type": token.type,
                        "value": token.value,
                        "line": token.line,
                        "col": token.col
                    }
            return None

        # CASE 2: NON-TERMINAL (Grammar Rule)
        # A non-terminal like 'statement' or 'expression' should match 
        # a completed rule in the chart
        
        # Check bounds
        if end >= len(self.chart):
            return None
        
        # Look in chart[end] for a completed rule of type 'symbol'
        # that started at position 'start'
        for item in self.chart[end]:
            if (item.production.lhs == symbol and  # Is this the rule we're looking for?
                item.is_complete() and             # Have we finished matching it?
                item.start_index == start):        # Does it span the right range?
                # Found it! Recursively build its tree node
                return self._build_node(item, end)
        
        return None