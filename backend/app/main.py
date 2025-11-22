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
    
    It also intelligently inserts "WHITESPACE" tokens for the gaps
    between the tokens my lexer finds. This is crucial for
    reconstructing the *entire* code block on the frontend,
    including all the original spacing and newlines.
    
    Returns:
        (list, list): A tuple containing the list of final tokens
                      and the list of any errors.
    """
    # 1. Initialize and run my lexer from lexer.py
    lexer = Lexer(code)
    # This captures both the classified tokens (from token.py) and any errors
    tokens_from_lexer, errors = lexer.tokenize_all()

    # 2. Process the lexer's output into a cleaner list of dictionaries.
    # The output from tokenize_all() is [((value, type), meta), ...],
    # so I flatten it into [{type, value, start, end, line, col}, ...].
    processed_tokens = []
    for token_pair, meta in tokens_from_lexer:
        value, token_type = token_pair
        processed_tokens.append({
            "type": token_type.upper(), # I uppercase the type for consistency
            "value": value,
            "start": meta['start'],
            "end": meta['end'],
            "line": meta['line'], # Added line
            "col": meta['col']    # Added col
        })

    # 3. Insert WHITESPACE tokens.
    # My lexer *skips* whitespace, but the frontend needs it.
    # I iterate through my processed tokens and check for gaps.
    
    final_tokens = []
    last_end = 0
    
    # We initialize trackers for line/col to calculate positions for whitespace
    current_line = 1
    current_col = 1

    for token in processed_tokens:
        start_index = token["start"]

        # Check if there's a gap between the last token and this one
        if start_index > last_end:
            whitespace_value = code[last_end:start_index]
            
            # Add the whitespace token with calculated line/col
            final_tokens.append({
                "type": "WHITESPACE",
                "value": whitespace_value,
                "start": last_end,
                "end": start_index,
                "line": current_line,
                "col": current_col
            })
            
            # Advance our position trackers past the whitespace
            newlines = whitespace_value.count('\n')
            if newlines > 0:
                current_line += newlines
                current_col = len(whitespace_value) - whitespace_value.rfind('\n')
            else:
                current_col += len(whitespace_value)

        # Add the current (non-whitespace) token
        final_tokens.append(token)
        
        # Sync our trackers to the token's actual end position 
        # so the NEXT whitespace starts at the right place.
        # We start at the token's 'line' and 'col' (authoritative source)
        current_line = token['line']
        current_col = token['col']
        
        # Add the length of the token to find where it ends
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
        whitespace_value = code[last_end:]
        final_tokens.append({
            "type": "WHITESPACE",
            "value": whitespace_value,
            "start": last_end,
            "end": len(code),
            "line": current_line,
            "col": current_col
        })

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