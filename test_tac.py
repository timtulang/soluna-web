#!/usr/bin/env python3
"""
Quick test of TAC interpreter with sample code.
"""
import sys
import asyncio
sys.path.insert(0, '/home/tim/Code/soluna-web/backend')

from app.codegen.tac_interpreter import TACInterpreter

# Simple test: Basic arithmetic and output
simple_tac = """
kai = 5
flux = 3.14
sum = kai + flux
param sum
call nova, 1
"""

# Test with function
function_tac = """
func add(x, y):
t0 = x + y
return t0
endfunc

param 3
param 4
t1 = call add, 2
param t1
call nova, 1
"""

# Test with conditional
conditional_tac = """
kai = 10
t0 = kai > 5
ifFalse t0 goto L0
param "big"
call nova, 1
goto L1
L0:
param "small"
call nova, 1
L1:
"""

async def test():
    print("Test 1: Simple arithmetic")
    outputs = []
    async def out(text):
        outputs.append(text)
        print(f"Output: {text.strip()}")
    
    interp = TACInterpreter(simple_tac, output_callback=out)
    try:
        await interp.run()
        print("✓ Test 1 passed\n")
    except Exception as e:
        print(f"✗ Test 1 failed: {e}\n")
    
    print("Test 2: Function call")
    outputs = []
    interp = TACInterpreter(function_tac, output_callback=out)
    try:
        await interp.run()
        print("✓ Test 2 passed\n")
    except Exception as e:
        print(f"✗ Test 2 failed: {e}\n")
    
    print("Test 3: Conditional")
    outputs = []
    interp = TACInterpreter(conditional_tac, output_callback=out)
    try:
        await interp.run()
        print("✓ Test 3 passed\n")
    except Exception as e:
        print(f"✗ Test 3 failed: {e}\n")

if __name__ == "__main__":
    asyncio.run(test())
