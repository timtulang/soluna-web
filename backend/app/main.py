# app/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import re  

# --- Custom Modules ---
from app.lexer.lexer import Lexer 

# Parser Modules
from app.parser.parser import EarleyParser
from app.parser.grammar import SOLUNA_GRAMMAR
from app.parser.adapter import adapter
from app.parser.tree_builder import ParseTreeBuilder

# Semantic Modules
from app.semantics.analyzer import SemanticAnalyzer
from app.semantics.errors import SemanticError

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://soluna-web-theta.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run_pipeline(code: str):
    """
    Runs the full compiler pipeline:
    1. Lexer (Raw text -> Tokens)
    2. Adapter (Lexer Tokens -> Parser Tokens)
    3. Earley Parser (Syntax Validation)
    4. Tree Builder (Chart -> CST)
    5. Semantic Analyzer (Logic & Scope Check)
    """
    # -------------------------------------------------------------------------
    # 1. Lexical Analysis
    # -------------------------------------------------------------------------
    lexer = Lexer(code)
    tokens_from_lexer, lexer_errors = lexer.tokenize_all()

    # -------------------------------------------------------------------------
    # 2. Frontend Data Prep (Coloring, Identifiers, Whitespace)
    # -------------------------------------------------------------------------
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

    # Identifier Aliasing (for rainbow highlighting)
    identifier_map = {}
    id_counter = 1
    for token in processed_tokens:
        if token['type'] == 'identifier':
            original_val = token['value']
            if original_val not in identifier_map:
                identifier_map[original_val] = f"identifier{id_counter}"
                id_counter += 1
            token['alias'] = identifier_map[original_val]

    # Gap Filling (restoring whitespace for the UI)
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

    # -------------------------------------------------------------------------
    # 3. Parsing & Semantics
    # -------------------------------------------------------------------------
    parse_tree = None
    parser_error = None
    
    # Only proceed if Lexer gave us clean tokens
    if len(lexer_errors) == 0 and len(tokens_from_lexer) > 0:
        try:
            # A. Adapter: Lexer Tokens -> Parser Tokens
            clean_parser_tokens = adapter(tokens_from_lexer)

            # B. Syntax Parsing (Earley Algorithm)
            parser = EarleyParser(SOLUNA_GRAMMAR, 'program')
            is_valid = parser.parse(clean_parser_tokens)
            
            if is_valid:
                # C. Tree Construction
                # Reconstructs the CST from the Earley Chart
                builder = ParseTreeBuilder(parser, clean_parser_tokens)
                parse_tree = builder.build()

                # D. Semantic Analysis
                # Checks for logic errors (e.g. redeclaration)
                if parse_tree:
                    analyzer = SemanticAnalyzer()
                    try:
                        analyzer.analyze(parse_tree)
                    except SemanticError as se:
                        # Convert Semantic Logic Error into a Frontend Error
                        lexer_errors.append({
                            "type": "SEMANTIC_ERROR",
                            "message": se.message,
                            "line": se.line,
                            "col": se.col,
                            "start": 0, "end": 0 # Logic errors often span multiple tokens, so we default 0
                        })
                        # IMPORTANT: Invalid semantics means the code is broken.
                        # Hide the success tree so the UI shows the error state.
                        parse_tree = None
            else:
                # This should technically be caught by parser.parse()'s exception handler,
                # but if it returns False without raising, we catch it here.
                parser_error = "Syntax Error: The code does not match the Soluna grammar."

        except Exception as e:
            # Captures Syntax Errors thrown by EarleyParser._handle_error
            parser_error = str(e).strip()

    return final_tokens, lexer_errors, parse_tree, parser_error


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                code = payload.get("code", "")
            except (json.JSONDecodeError, AttributeError):
                code = data

            tokens, errors, parse_tree, parser_err = run_pipeline(code)

            if parser_err:
                errors.append({
                    "type": "PARSER_ERROR",
                    "message": parser_err,
                    "line": 0, "col": 0, "start": 0, "end": 0
                })

            response_payload = {
                "tokens": tokens,
                "errors": errors,
                "parseTree": parse_tree
            }
            await websocket.send_text(json.dumps(response_payload))

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Closing connection")