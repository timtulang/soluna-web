#!/usr/bin/env python3
"""
Test TAC interpreter with simple Soluna file.
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

async def main():
    # Read test file
    with open('/home/tim/Code/soluna-web/test_simple.sl', 'r') as f:
        soluna_code = f.read()
    
    print(f"Source code:\n{soluna_code}\n")
    
    # Lexing
    print("Lexing...")
    lexer = Lexer(soluna_code)
    tokens, errors = lexer.tokenize_all()
    if errors:
        print(f"Lexer errors: {errors}")
        for e in errors:
            print(f"  - {e}")
        return
    print(f"✓ Lexed {len(tokens)} tokens\n")
    
    # Parsing
    print("Parsing...")
    clean_tokens = adapter(tokens)
    parser = EarleyParser(SOLUNA_GRAMMAR, 'program')
    if not parser.parse(clean_tokens):
        print("✗ Parse error")
        return
    print("✓ Parse successful\n")
    
    # Build tree
    print("Building AST...")
    builder = ParseTreeBuilder(parser, clean_tokens)
    tree = builder.build()
    if not tree:
        print("✗ Failed to build tree")
        return
    print("✓ AST built\n")
    
    # Semantic analysis
    print("Semantic analysis...")
    analyzer = SemanticAnalyzer()
    analyzer.analyze(tree)
    print(f"✓ Analysis complete (warnings: {len(analyzer.warnings)})\n")
    
    # TAC generation
    print("TAC generation...")
    tac_gen = TACGenerator()
    tac_code = tac_gen.generate(tree)
    print(f"Generated TAC:\n{tac_code}\n")
    
    # Execution
    print("Executing...")
    outputs = []
    async def out_cb(text):
        outputs.append(text)
        print(f"[Output] {text.rstrip()}")
    
    interp = TACInterpreter(tac_code, output_callback=out_cb)
    try:
        await interp.run()
        print("\n✓ Execution successful!")
    except Exception as e:
        import traceback
        print(f"\n✗ Execution failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
