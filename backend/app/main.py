from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import re
import io
import sys

from app.lexer.lexer import Lexer 
from app.parser.parser import EarleyParser
from app.parser.grammar import SOLUNA_GRAMMAR
from app.parser.adapter import adapter
from app.parser.tree_builder import ParseTreeBuilder
from app.semantics.analyzer import SemanticAnalyzer
from app.semantics.errors import SemanticError
from app.codegen.transpiler import PythonTranspiler

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://soluna-web-theta.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def execute_soluna_code(python_code):
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()

    try:
        exec(python_code, {}) 
        output = redirected_output.getvalue()
    except Exception as e:
        output = f"Runtime Error: {str(e)}"
    finally:
        sys.stdout = old_stdout

    return output

def run_pipeline(code: str):
    lexer = Lexer(code)
    tokens_from_lexer, lexer_errors = lexer.tokenize_all()

    processed_tokens = []
    for token_pair, meta in tokens_from_lexer:
        value, token_type = token_pair
        processed_tokens.append({
            "type": token_type,
            "value": value,
            "start": meta['start'],
            "end": meta['end'],
            "line": meta['line'], 
            "col": meta['col']    
        })

    identifier_map = {}
    id_counter = 1
    for token in processed_tokens:
        if token['type'] == 'identifier':
            original_val = token['value']
            if original_val not in identifier_map:
                identifier_map[original_val] = f"identifier{id_counter}"
                id_counter += 1
            token['alias'] = identifier_map[original_val]

    final_tokens = []
    last_end = 0
    current_line = 1
    current_col = 1
    
    def emit_text(text, start_pos):
        nonlocal current_line, current_col
        parts = re.split(r'(\n|    )', text)
        curr = start_pos
        for part in parts:
            if not part: continue
            if part == '\n': t_type = "newline"
            elif part == "    ": t_type = "tab" 
            else: t_type = "whitespace"
            final_tokens.append({
                "type": t_type, "value": part, "start": curr, "end": curr + len(part),
                "line": current_line, "col": current_col
            })
            curr += len(part)
            if part == '\n': current_line += 1; current_col = 1
            else: current_col += len(part)

    def process_gap(start, end):
        nonlocal current_line, current_col
        if start >= end: return
        chunk_start = start
        relevant_errors = [e for e in lexer_errors if e.get('start', -1) < end and e.get('end', -1) > start]
        relevant_errors.sort(key=lambda x: x['start'])
        
        for err in relevant_errors:
            err_start = max(err['start'], chunk_start)
            err_end = min(err['end'], end)
            if err_start > chunk_start: emit_text(code[chunk_start:err_start], chunk_start)
            if err_end > err_start:
                err_val = code[err_start:err_end]
                newlines = err_val.count('\n')
                if newlines > 0: current_line += newlines; current_col = len(err_val) - err_val.rfind('\n')
                else: current_col += len(err_val)
            chunk_start = max(chunk_start, err_end)
        if chunk_start < end: emit_text(code[chunk_start:end], chunk_start)

    for token in processed_tokens:
        start_index = token["start"]
        if start_index > last_end: process_gap(last_end, start_index)
        final_tokens.append(token)
        current_line = token['line']
        current_col = token['col']
        token_val = token['value']
        newlines = token_val.count('\n')
        if newlines > 0: current_line += newlines; current_col = len(token_val) - token_val.rfind('\n')
        else: current_col += len(token_val)
        last_end = token["end"]
        
    if last_end < len(code): process_gap(last_end, len(code))

    parse_tree = None
    parser_error = None
    warnings = []
    console_output = ""
    transpiled_code = ""
    
    if len(lexer_errors) == 0 and len(tokens_from_lexer) > 0:
        try:
            clean_parser_tokens = adapter(tokens_from_lexer)

            parser = EarleyParser(SOLUNA_GRAMMAR, 'program')
            is_valid = parser.parse(clean_parser_tokens)
            
            if is_valid:
                builder = ParseTreeBuilder(parser, clean_parser_tokens)
                parse_tree = builder.build()

                if parse_tree:
                    analyzer = SemanticAnalyzer()
                    try:
                        analyzer.analyze(parse_tree)
                        warnings = [{"type": "WARNING", "message": w} for w in analyzer.warnings]
                        
                        transpiler = PythonTranspiler()
                        transpiled_code = transpiler.generate(parse_tree)
                        
                        console_output = execute_soluna_code(transpiled_code)
                        
                    except SemanticError as se:
                        lexer_errors.append({
                            "type": "SEMANTIC_ERROR",
                            "message": se.message,
                            "line": se.line,
                            "col": se.col,
                            "start": 0, "end": 0 
                        })
                        parse_tree = None
            else:
                parser_error = "Syntax Error: The code does not match the Soluna grammar."

        except Exception as e:
            parser_error = str(e).strip()

    return final_tokens, lexer_errors, parse_tree, parser_error, warnings, console_output, transpiled_code


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                code = payload.get("code", "")
            except (json.JSONDecodeError, AttributeError):
                code = data

            tokens, errors, parse_tree, parser_err, warnings, console_output, transpiled_code = run_pipeline(code)

            if parser_err:
                errors.append({
                    "type": "PARSER_ERROR",
                    "message": parser_err,
                    "line": 0, "col": 0, "start": 0, "end": 0
                })

            response_payload = {
                "tokens": tokens,
                "errors": errors,
                "warnings": warnings, 
                "parseTree": parse_tree,
                "output": console_output,
                "transpiledCode": transpiled_code
            }
            await websocket.send_text(json.dumps(response_payload))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        pass