#
# main.py
#

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import re  
from app.lexer.lexer import Lexer 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run_lexer(code: str):
    """
    Runs the lexer and fills in the gaps with WHITESPACE, TAB, or NEWLINE tokens.
    """
    lexer = Lexer(code)
    tokens_from_lexer, errors = lexer.tokenize_all()

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

    final_tokens = []
    last_end = 0
    
    current_line = 1
    current_col = 1
    
    # --- UPDATED HELPER FUNCTION ---
    def emit_text(text, start_pos):
        nonlocal current_line, current_col
        
        # FIX: Split by Newline OR 4-space blocks.
        # This ensures that "        " becomes two separate "    " tokens.
        parts = re.split(r'(\n|    )', text)
        
        curr = start_pos
        for part in parts:
            if not part: continue
            
            # Determine token type
            if part == '\n':
                t_type = "NEWLINE"
            elif part == "    ":
                t_type = "TAB" # Now this will hit for every 4-space block
            else:
                t_type = "WHITESPACE"
            
            final_tokens.append({
                "type": t_type,
                "value": part,
                "start": curr,
                "end": curr + len(part),
                "line": current_line,
                "col": current_col
            })
            
            # Update trackers
            curr += len(part)
            if part == '\n':
                current_line += 1
                current_col = 1
            else:
                current_col += len(part)

    def process_gap(start, end):
        nonlocal current_line, current_col
        
        if start >= end: return

        chunk_start = start
        
        relevant_errors = [
            e for e in errors 
            if e.get('start', -1) < end and e.get('end', -1) > start
        ]
        relevant_errors.sort(key=lambda x: x['start'])
        
        for err in relevant_errors:
            err_start = max(err['start'], chunk_start)
            err_end = min(err['end'], end)
            
            if err_start > chunk_start:
                emit_text(code[chunk_start:err_start], chunk_start)

            if err_end > err_start:
                err_val = code[err_start:err_end]
                newlines = err_val.count('\n')
                if newlines > 0:
                    current_line += newlines
                    current_col = len(err_val) - err_val.rfind('\n')
                else:
                    current_col += len(err_val)
            
            chunk_start = max(chunk_start, err_end)

        if chunk_start < end:
            emit_text(code[chunk_start:end], chunk_start)

    for token in processed_tokens:
        start_index = token["start"]

        if start_index > last_end:
            process_gap(last_end, start_index)

        final_tokens.append(token)
        
        current_line = token['line']
        current_col = token['col']
        token_val = token['value']
        newlines = token_val.count('\n')
        if newlines > 0:
            current_line += newlines
            current_col = len(token_val) - token_val.rfind('\n')
        else:
            current_col += len(token_val)

        last_end = token["end"]
        
    if last_end < len(code):
        process_gap(last_end, len(code))

    return final_tokens, errors


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

            tokens, errors = run_lexer(code)

            response_payload = {
                "tokens": tokens,
                "errors": errors
            }

            await websocket.send_text(json.dumps(response_payload))

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Closing connection")