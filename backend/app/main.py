#
# main.py
#
# This is the heart of the backend server. I built this using FastAPI
# to create a real-time WebSocket endpoint. Its main purpose is to
# receive code from a frontend (like a web-based code editor),
# run my lexer on that code, and send back the results (both tokens
# and any errors) instantly.
#

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import re  # NEW: Imported regex module for splitting newlines
# This is the main import that connects my server to the lexer system I built.
from app.lexer.lexer import Lexer 

# Initialize my FastAPI application
app = FastAPI()

# --- CORS Middleware ---
# I added this middleware to allow my frontend application (running on
# localhost:5173 or :3000) to communicate with this backend server.
# Without this, the browser would block the requests for security reasons.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run_lexer(code: str):
    """
    This is my main helper function that acts as a bridge between the
    server and my lexer module. It takes the raw code string,
    runs the lexer, and then transforms the output into a
    JSON-friendly format for the frontend.
    
    It also intelligently inserts "WHITESPACE" and "NEWLINE" tokens 
    for the gaps between the tokens my lexer finds.
    
    Returns:
        (list, list): A tuple containing the list of final tokens
                      and the list of any errors.
    """
    # 1. Initialize and run my lexer from lexer.py
    lexer = Lexer(code)
    # This captures both the classified tokens (from token.py) and any errors
    tokens_from_lexer, errors = lexer.tokenize_all()

    # 2. Process the lexer's output into a cleaner list of dictionaries.
    processed_tokens = []
    for token_pair, meta in tokens_from_lexer:
        value, token_type = token_pair
        processed_tokens.append({
            "type": token_type.upper(), # I uppercase the type for consistency
            "value": value,
            "start": meta['start'],
            "end": meta['end'],
            "line": meta['line'], 
            "col": meta['col']    
        })

    # 3. Insert WHITESPACE/NEWLINE tokens, skipping errors.
    final_tokens = []
    last_end = 0
    
    # We initialize trackers for line/col to calculate positions for whitespace
    current_line = 1
    current_col = 1
    
    # NEW: Helper function to emit valid whitespace/newline tokens
    def emit_text(text, start_pos):
        nonlocal current_line, current_col
        
        # Split the text by newline characters, keeping the delimiters
        # r'(\n)' splits "a\nb" into ["a", "\n", "b"]
        parts = re.split(r'(\n)', text)
        
        curr = start_pos
        for part in parts:
            if not part: continue
            
            # Determine token type
            t_type = "NEWLINE" if part == '\n' else "WHITESPACE"
            
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

    # Helper function to process a gap
    def process_gap(start, end):
        nonlocal current_line, current_col
        
        if start >= end: return

        chunk_start = start
        
        # Find errors completely or partially inside this gap
        relevant_errors = [
            e for e in errors 
            if e.get('start', -1) < end and e.get('end', -1) > start
        ]
        # Sort by start to handle sequentially
        relevant_errors.sort(key=lambda x: x['start'])
        
        for err in relevant_errors:
            # The error might start before our chunk_start if overlaps, 
            # but we only care about the part inside [start, end).
            err_start = max(err['start'], chunk_start)
            err_end = min(err['end'], end)
            
            # If there is valid text before this error starts, emit it
            if err_start > chunk_start:
                # Use the new emit_text helper
                emit_text(code[chunk_start:err_start], chunk_start)

            # Now process the ERROR text (skip emitting, but update line/col)
            if err_end > err_start:
                err_val = code[err_start:err_end]
                newlines = err_val.count('\n')
                if newlines > 0:
                    current_line += newlines
                    current_col = len(err_val) - err_val.rfind('\n')
                else:
                    current_col += len(err_val)
            
            chunk_start = max(chunk_start, err_end)

        # Emit any remaining valid text after the last error
        if chunk_start < end:
            emit_text(code[chunk_start:end], chunk_start)

    # Iterate through tokens and fill gaps
    for token in processed_tokens:
        start_index = token["start"]

        # Check if there's a gap between the last token and this one
        if start_index > last_end:
            process_gap(last_end, start_index)

        # Add the current (non-whitespace) token
        final_tokens.append(token)
        
        # Sync our trackers to the token's end
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
        
    # 4. Add any trailing whitespace after the very last token.
    if last_end < len(code):
        process_gap(last_end, len(code))

    # 5. Return both the final list of tokens (with whitespace) and errors.
    return final_tokens, errors


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    This is my main WebSocket endpoint.
    It establishes a persistent connection with a client (e.g., the browser).
    When the client sends a message (containing code), this function
    runs the lexer and sends the token/error results right back.
    """
    await websocket.accept()
    print("Client connected")
    try:
        # This loop keeps the connection alive, waiting for messages.
        while True:
            # Wait for a message (the code) from the client
            data = await websocket.receive_text()
            
            # I added this try/except to handle different payload formats.
            try:
                payload = json.loads(data)
                code = payload.get("code", "")
            except (json.JSONDecodeError, AttributeError):
                code = data # It was just a raw string

            # Run my lexer logic on the received code
            tokens, errors = run_lexer(code)

            # Construct the JSON response payload
            response_payload = {
                "tokens": tokens,
                "errors": errors
            }

            # Send the JSON-serialized results back to the client
            await websocket.send_text(json.dumps(response_payload))

    except WebSocketDisconnect:
        # This handles when the client (e.g., browser tab) closes.
        print("Client disconnected")
    except Exception as e:
        # A general catch-all for any other unexpected errors.
        print(f"An unexpected error occurred: {e}")
    finally:
        # This just helps me see when a connection is fully torn down.
        print("Closing connection")