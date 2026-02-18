# app/parser/tree_builder.py
from .parser import Token

class ParseTreeBuilder:
    def __init__(self, parser, tokens):
        self.parser = parser
        self.tokens = tokens
        self.chart = parser.chart

    def build(self):
        """
        Entry point. Finds the root 'program' rule and starts recursion.
        """
        # 1. Find the completed start rule in the final chart set
        root_item = None
        end_index = len(self.tokens)
        
        # Look in the last chart column
        for item in self.chart[end_index]:
            if (item.production.lhs == self.parser.start_symbol and 
                item.is_complete() and 
                item.start_index == 0):
                root_item = item
                break
        
        if not root_item:
            # Should be caught by the recognizer loop, but just in case
            return None

        # 2. Start the recursive descent
        return self._build_node(root_item, end_index)

    def _build_node(self, item, end_index):
        """
        Converts a completed EarleyItem into a Tree Node dictionary.
        This effectively "reverses" the rule to find children.
        """
        start_index = item.start_index
        rhs = item.production.rhs
        
        # The structure we want to return
        node = {
            "type": item.production.lhs,
            "children": [],
            "start": start_index,
            "end": end_index
        }

        # If it's an empty rule (Lambda), return immediately
        if not rhs:
            return node

        # We need to find "split points" for every symbol in the RHS.
        # Example: A -> B C D. We know A spans (start...end).
        # We need to find k1, k2 such that B is (start..k1), C is (k1..k2), D is (k2..end).
        children = self._find_children(rhs, start_index, end_index)
        
        if children is None:
            raise Exception(f"Tree Reconstruction Failed at {item.production.lhs}")

        node["children"] = children
        return node

    def _find_children(self, symbols, start_index, end_index):
        """
        Recursive helper to decompose a list of symbols into child nodes.
        Backtracking is required because of ambiguity.
        """
        # Base case: No symbols left. 
        # If we consumed all input (start == end), it's a valid match.
        if not symbols:
            return [] if start_index == end_index else None

        current_sym = symbols[-1] # Look at the LAST symbol
        remaining_syms = symbols[:-1] # The rest of the prefix

        # We iterate backwards from end_index to start_index to find a split point.
        # This determines where 'current_sym' started.
        for split_point in range(end_index, start_index - 1, -1):
            
            # 1. Try to match the Last Symbol (current_sym) from split_point to end_index
            node = self._match_symbol(current_sym, split_point, end_index)
            
            if node is not None:
                # 2. If successful, recurse for the remaining symbols
                prefix_nodes = self._find_children(remaining_syms, start_index, split_point)
                
                if prefix_nodes is not None:
                    # Found a valid split! Combine and return.
                    return prefix_nodes + [node]

        return None # No valid split found

    def _match_symbol(self, symbol, start, end):
        """
        Checks if a specific symbol (Terminal or Non-Terminal) matches the span.
        """
        # Case A: Terminal (Token)
        # It must match exactly one token in the input
        if symbol not in self.parser.grammar:
            if end - start == 1:
                token = self.tokens[start]
                # If the grammar expects 'kai', and the token is 'kai' (or 'integer' mapped to 'kai')
                if token.type == symbol:
                    return {
                        "type": "TOKEN",
                        "token_type": token.type,
                        "value": token.value,
                        "line": token.line,
                        "col": token.col
                    }
            return None

        # Case B: Non-Terminal (Rule)
        # We look in the Chart at 'end' for a completed rule for 'symbol' that started at 'start'.
        if end >= len(self.chart): return None
        
        for item in self.chart[end]:
            if (item.production.lhs == symbol and 
                item.is_complete() and 
                item.start_index == start):
                # Found the item! Now recursively build its node.
                return self._build_node(item, end)
        
        return None