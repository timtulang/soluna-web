# --- backend/app/main.py (New Version) ---
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json

# --- Import your custom lexer package ---
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
    Uses your custom lexer and transforms its output into the
    format required by the frontend, including whitespace.
    """
    # 1. Instantiate and run your lexer
    lexer = Lexer(code)
    tokens_from_lexer, error = lexer.tokenize_all()

    if error:
        return None, error

    # 2. Transform the output format
    # from: [(('val', 'type'), {'meta':...})]
    # to:   [{'type':..., 'value':..., 'start':..., 'end':...}]
    processed_tokens = []
    for token_pair, meta in tokens_from_lexer:
        value, token_type = token_pair
        processed_tokens.append({
            "type": token_type.upper(),  # Use uppercase for consistency
            "value": value,
            "start": meta['start'],
            "end": meta['end']
        })

    # 3. Gap-filling: Re-introduce WHITESPACE tokens for the frontend
    final_tokens = []
    last_end = 0
    for token in processed_tokens:
        # Check for a gap between the last token and this one
        if token["start"] > last_end:
            whitespace_value = code[last_end:token["start"]]
            final_tokens.append({
                "type": "WHITESPACE",
                "value": whitespace_value,
                "start": last_end,
                "end": token["start"]
            })
        
        final_tokens.append(token)
        last_end = token["end"]

    # Check for any trailing whitespace after the last token
    if last_end < len(code):
        final_tokens.append({
            "type": "WHITESPACE",
            "value": code[last_end:],
            "start": last_end,
            "end": len(code)
        })

    return final_tokens, None


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                # Standard case: client sends JSON with a 'code' key
                payload = json.loads(data)
                code = payload.get("code", "")
            except (json.JSONDecodeError, AttributeError):
                # Fallback: client sends plain text
                code = data

            # Run your custom lexer
            tokens, error = run_lexer(code)

            response_payload = {}
            if error:
                # Send a dedicated error object to the client
                response_payload["error"] = error
            else:
                response_payload["tokens"] = tokens

            # Send the result back to the client
            await websocket.send_text(json.dumps(response_payload))

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Closing connection")