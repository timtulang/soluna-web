from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import re
import io
import sys
import asyncio
import queue
import builtins

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

    return final_tokens, lexer_errors, parse_tree, parser_error, warnings, transpiled_code

class ExecutionEnv:
    def __init__(self, ws: WebSocket, loop: asyncio.AbstractEventLoop, input_q: queue.Queue):
        self.ws = ws
        self.loop = loop
        self.input_q = input_q
        self.output_buffer = ""
        
    def c_print(self, *args, end='\n', sep=' '):
        text = sep.join(str(a) for a in args) + end
        self.output_buffer += text
        asyncio.run_coroutine_threadsafe(
            self.ws.send_text(json.dumps({"output": self.output_buffer})),
            self.loop
        )
        
    def c_input(self):
        # 1. Ask frontend for input
        asyncio.run_coroutine_threadsafe(
            self.ws.send_text(json.dumps({
                "output": self.output_buffer,
                "isWaitingForInput": True
            })),
            self.loop
        )
        # 2. Block this thread until WebSocket receives {"input": "..."}
        val = self.input_q.get()
        if isinstance(val, Exception):
            raise val # Aborts execution if user hits Run again
            
        # 3. Echo the input to the terminal and hide the input box
        self.output_buffer += str(val) + "\n"
        asyncio.run_coroutine_threadsafe(
            self.ws.send_text(json.dumps({
                "output": self.output_buffer,
                "isWaitingForInput": False
            })),
            self.loop
        )
        return val

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_running_loop()
    active_input_q = None
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                continue

            # Route incoming data to the active thread if it's an input response
            if "input" in payload:
                if active_input_q:
                    active_input_q.put(payload["input"])
                continue
                
            code = payload.get("code", "")
            
            # Abort any currently running execution thread if the user presses Run again
            if active_input_q:
                active_input_q.put(Exception("ABORT_EXECUTION"))
                active_input_q = None

            tokens, errors, parse_tree, parser_err, warnings, transpiled_code = run_pipeline(code)

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
                "transpiledCode": transpiled_code,
                "output": "",
                "isWaitingForInput": False
            }
            await websocket.send_text(json.dumps(response_payload))

            # Run Execution Phase
            if not errors and transpiled_code:
                active_input_q = queue.Queue()
                env = ExecutionEnv(websocket, loop, active_input_q)
                
                def run_code(q, environment, t_code):
                    try:
                        custom_globals = builtins.__dict__.copy()
                        custom_globals["print"] = environment.c_print
                        custom_globals["input"] = environment.c_input
                        
                        # Executes securely using our overridden globals
                        exec(t_code, custom_globals)
                        
                    except Exception as e:
                        if str(e) != "ABORT_EXECUTION":
                            err_msg = str(e)
                            if "Runtime Error" not in err_msg:
                                err_msg = f"Runtime Error: {err_msg}"
                                
                            prefix = "" if environment.output_buffer.endswith("\n") else "\n"
                            environment.output_buffer += f"{prefix}{err_msg}"
                            
                            # Bubble error to UI and kill input box
                            asyncio.run_coroutine_threadsafe(
                                websocket.send_text(json.dumps({
                                    "output": environment.output_buffer,
                                    "isWaitingForInput": False
                                })),
                                loop
                            )
                        
                # Launch the executor in a non-blocking background thread
                asyncio.create_task(asyncio.to_thread(run_code, active_input_q, env, transpiled_code))

    except WebSocketDisconnect:
        if active_input_q:
            active_input_q.put(Exception("ABORT_EXECUTION"))
    except Exception as e:
        print(f"WS Handling Error: {e}")