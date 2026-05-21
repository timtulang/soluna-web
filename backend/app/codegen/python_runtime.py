"""
Runtime helpers for Python-transpiled Soluna code execution.
"""

class SolunaList(list):
    """List that auto-expands when accessing out-of-bounds indices."""
    def __setitem__(self, key, value):
        if key >= len(self):
            self.extend([0] * (key - len(self) + 1))
        super().__setitem__(key, value)
    
    def __getitem__(self, key):
        if key >= len(self):
            self.extend([0] * (key - len(self) + 1))
        return super().__getitem__(key)


async def soluna_input_async(input_callback, expected_type):
    """Async wrapper for input with type validation."""
    return await input_callback(expected_type)


def soluna_index(idx):
    """Validate 1-based list index and convert to 0-based."""
    if idx < 1:
        raise RuntimeError("Runtime Error: list index out of range")
    return idx - 1


def soluna_set(arr, idx, val):
    """Set array value with 1-based indexing."""
    actual_idx = soluna_index(idx)
    arr[actual_idx] = val
