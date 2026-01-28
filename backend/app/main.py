# app/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import re  
from app.lexer.lexer import Lexer 
from app.parser.lark_parser import LarkParser  # <--- Updated Import

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://soluna-web-theta.vercel.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run_pipeline(code: str):
    """
    Runs Lexer -> Identifier Iteration -> Lark Parser
    """
    # 1. Run Lexer
    lexer = Lexer(code)
    tokens_from_lexer, lexer_errors = lexer.tokenize_all()

    # 2. Convert to Dictionaries
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

    # --- Identifier Iteration Logic ---
    # Assigns identifier1, identifier2, etc. to unique identifiers for frontend coloring
    identifier_map = {}
    id_counter = 1
    
    for token in processed_tokens:
        if token['type'] == 'identifier':
            original_val = token['value']
            # If we haven't seen this identifier yet, assign a new ID
            if original_val not in identifier_map:
                identifier_map[original_val] = f"identifier{id_counter}"
                id_counter += 1
            
            # Attach the alias to the token
            token['alias'] = identifier_map[original_val]

    # 3. Gap Filling (for frontend highlighting of whitespace/errors)
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

    # 4. Run Parser (Lark)
    parse_tree = None
    parser_error = None
    
    # Only run parser if lexer succeeded and we have tokens
    if len(lexer_errors) == 0 and len(processed_tokens) > 0:
        try:
            # Instantiate the LarkParser wrapper
            parser = LarkParser()
            
            # Pass the list of token dictionaries to the parser
            # The adapter in lark_parser.py will read this list
            root = parser.parse(processed_tokens)
            
            # The result is already a dictionary suitable for the frontend
            parse_tree = root
            
        except Exception as e:
            # Capture the error message for the frontend
            # Lark errors can be verbose, so you might want to trim them
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