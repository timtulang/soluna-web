#!/usr/bin/env python3
"""
Test TAC interpreter with actual Soluna code compilation.
"""
import sys
import asyncio
sys.path.insert(0, '/home/tim/Code/soluna-web/backend')

from app.lexer.lexer import Lexer
from app.parser.parser import EarleyParser
from app.parser.grammar import SOLUNA_GRAMMAR
from app.parser.adapter import adapter
from app.parser.tree_builder import ParseTreeBuilder
from app.semantics.analyzer import SemanticAnalyzer
from app.codegen.tacgen import TACGenerator
from app.codegen.tac_interpreter import TACInterpreter

async def compile_and_run(soluna_code: str):
    """Compile and run Soluna code."""
    print(f"Source code:\n{soluna_code}\n")
    
    # Lexing
    lexer = Lexer(soluna_code)
    tokens, errors = lexer.tokenize_all()
    if errors:
        print(f"Lexer errors: {errors}")
        return
    
    # Parsing
    clean_tokens = adapter(tokens)
    parser = EarleyParser(SOLUNA_GRAMMAR, 'program')
    if not parser.parse(clean_tokens):
        print("Parse error")
        return
    
    # Build tree
    builder = ParseTreeBuilder(parser, clean_tokens)
    tree = builder.build()
    
    # Semantic analysis
    analyzer = SemanticAnalyzer()
    analyzer.analyze(tree)
    
    # TAC generation
    tac_gen = TACGenerator()
    tac_code = tac_gen.generate(tree)
    print(f"Generated TAC:\n{tac_code}\n")
    
    # Execution
    outputs = []
    async def out_cb(text):
        outputs.append(text)
        print(f"Output: {text.rstrip()}")
    
    interp = TACInterpreter(tac_code, output_callback=out_cb)
    try:
        await interp.run()
        print("✓ Execution successful\n")
    except Exception as e:
        print(f"✗ Execution failed: {e}\n")

async def main():
    # Test 1: Simple variable and output
    code1 = """
kai x = 42
nova(x)
"""
    await compile_and_run(code1)
    
    # Test 2: Arithmetic
    code2 = """
kai a = 10
kai b = 5
kai c = a + b
nova(c)
"""
    await compile_and_run(code2)
    
    # Test 3: Conditionals
    code3 = """
kai x = 15
selene (x > 10) {
    nova("big")
} flux {
    nova("small")
}
"""
    await compile_and_run(code3)
    
    # Test 4: Loops
    code4 = """
kai i = 0
blaze (i < 3) {
    nova(i)
    i += 1
}
"""
    await compile_and_run(code4)

if __name__ == "__main__":
    asyncio.run(main())
