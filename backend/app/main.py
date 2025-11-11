from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
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
    Uses your custom lexer and transforms its output.
    Returns (tokens, errors)
    """
    lexer = Lexer(code)
    tokens_from_lexer, errors = lexer.tokenize_all()

    processed_tokens = []
    for token_pair, meta in tokens_from_lexer:
        value, token_type = token_pair
        processed_tokens.append({
            "type": token_type.upper(),
            "value": value,
            "start": meta['start'],
            "end": meta['end']
        })

    final_tokens = []
    last_end = 0
    for token in processed_tokens:
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
    if last_end < len(code):
        final_tokens.append({
            "type": "WHITESPACE",
            "value": code[last_end:],
            "start": last_end,
            "end": len(code)
        })

    # --- UPDATED: Return both ---
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