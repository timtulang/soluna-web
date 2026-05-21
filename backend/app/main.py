from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import re
import io
import sys
import asyncio
import queue
import builtins
import time

from app.lexer.lexer import Lexer 
from app.parser.parser import EarleyParser
from app.parser.grammar import SOLUNA_GRAMMAR
from app.parser.adapter import adapter
from app.parser.tree_builder import ParseTreeBuilder
from app.semantics.analyzer import SemanticAnalyzer
from app.semantics.errors import SemanticError
from app.codegen.tacgen import TACGenerator
from app.codegen.tac_interpreter import TACInterpreter
from app.codegen.transpiler import PythonTranspiler
from app.codegen.python_runtime import SolunaList, soluna_index, soluna_set

# Switch between 'tac' and 'python'
ACTIVE_GENERATOR = "python"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://soluna-web-theta.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run_pipeline(code: str, progress_callback=None):
    """
    Compile Soluna code with real progress tracking.
    
    Stages:
    1. Lexing (0-20%)
    2. Parsing (20-50%)
    3. Semantic Analysis (50-80%)
    4. Code Generation (80-100%)
    """
    is_disconnected = False  # Track if the socket is dead
    
    async def send_progress(stage: str, percentage: int, message: str):
        nonlocal is_disconnected
        if is_disconnected:
            return  # Stop trying to send if we already know it's disconnected
            
        """Helper to send progress updates"""
        if progress_callback:
            try:
                await progress_callback(json.dumps({
                    "compilationProgress": {
                        "stage": stage,
                        "percentage": percentage,
                        "message": message,
                        "timestamp": int(time.time() * 1000)
                    }
                }))
            except Exception as e:
                is_disconnected = True  # Flag it as disconnected to stop further attempts
                # Only print the error if it's NOT a normal close/disconnect message
                if "close message" not in str(e).lower() and "disconnect" not in str(e).lower():
                    print(f"Error sending progress: {e}")
    
    # Get or create event loop for async operations
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # ===== STAGE 1: LEXING (0-20%) =====
    try:
        loop.run_until_complete(send_progress("lexing", 5, "Initializing lexer..."))
        
        lexer = Lexer(code)
        tokens_from_lexer, lexer_errors = lexer.tokenize_all()
        
        loop.run_until_complete(send_progress("lexing", 15, f"Tokenized {len(tokens_from_lexer)} tokens"))
    except Exception as e:
        loop.run_until_complete(send_progress("error", 0, f"Lexer error: {str(e)}"))
        return None, [{"type": "LEXER_ERROR", "message": str(e), "line": 0, "col": 0, "start": 0, "end": 0}], None, None, [], ""

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

    loop.run_until_complete(send_progress("lexing", 20, "Lexing complete"))

    parse_tree = None
    parser_error = None
    warnings = []
    tac_code = ""
    
    if len(lexer_errors) == 0 and len(tokens_from_lexer) > 0:
        # ===== STAGE 2: PARSING (20-50%) =====
        try:
            loop.run_until_complete(send_progress("parsing", 25, "Building token stream..."))
            clean_parser_tokens = adapter(tokens_from_lexer)

            loop.run_until_complete(send_progress("parsing", 35, f"Parsing {len(clean_parser_tokens)} tokens..."))
            parser = EarleyParser(SOLUNA_GRAMMAR, 'program')
            is_valid = parser.parse(clean_parser_tokens)
            
            if is_valid:
                loop.run_until_complete(send_progress("parsing", 45, "Building parse tree..."))
                builder = ParseTreeBuilder(parser, clean_parser_tokens)
                parse_tree = builder.build()

                if parse_tree:
                    # ===== STAGE 3: SEMANTIC ANALYSIS (50-80%) =====
                    loop.run_until_complete(send_progress("semantic", 55, "Analyzing symbols..."))
                    analyzer = SemanticAnalyzer()
                    try:
                        analyzer.analyze(parse_tree)
                        warnings = [{"type": "WARNING", "message": w} for w in analyzer.warnings]
                        loop.run_until_complete(send_progress("semantic", 70, f"Found {len(warnings)} warnings"))
                        
                        # ===== STAGE 4: CODE GENERATION (80-100%) =====
                        loop.run_until_complete(send_progress("codegen", 80, f"Generating {ACTIVE_GENERATOR.upper()} code..."))
                        
                        if ACTIVE_GENERATOR == "tac":
                            generator = TACGenerator()
                        else:
                            generator = PythonTranspiler()
                            
                        tac_code = generator.generate(parse_tree)  # 'tac_code' now holds either TAC or Python
                        
                        # Print generated TAC instructions to console
                        print("\n" + "="*60)
                        print(f"Generated {ACTIVE_GENERATOR.upper()} Instructions:")
                        print("="*60)
                        print(tac_code)
                        print("="*60 + "\n")
                        
                        loop.run_until_complete(send_progress("codegen", 100, "Code generation complete"))
                        
                    except SemanticError as se:
                        lexer_errors.append({
                            "type": "SEMANTIC_ERROR",
                            "message": se.message,
                            "line": se.line,
                            "col": se.col,
                            "start": 0, "end": 0 
                        })
                        loop.run_until_complete(send_progress("error", 0, f"Semantic error: {se.message}"))
                        parse_tree = None
            else:
                parser_error = "Syntax Error: The code does not match the Soluna grammar."
                loop.run_until_complete(send_progress("error", 0, parser_error))

        except Exception as e:
            parser_error = str(e).strip()
            loop.run_until_complete(send_progress("error", 0, f"Parser error: {parser_error}"))

    return final_tokens, lexer_errors, parse_tree, parser_error, warnings, tac_code

class ExecutionEnv:
    def __init__(self, ws: WebSocket, loop: asyncio.AbstractEventLoop, input_q: queue.Queue):
        self.ws = ws
        self.loop = loop
        self.input_q = input_q
        self.output_buffer = ""
    
    async def output(self, text: str):
        """Async callback for output (nova/lumen)"""
        self.output_buffer += text
        try:
            await self.ws.send_text(json.dumps({"output": self.output_buffer}))
        except Exception as e:
            if "close message" not in str(e).lower() and "closed" not in str(e).lower():
                print(f"Output error: {e}")
    
    async def input(self, expected_type: str = "let") -> str:
        """Async callback for input (lumina)"""
        # Send request for input
        try:
            await self.ws.send_text(json.dumps({
                "output": self.output_buffer,
                "isWaitingForInput": True,
                "inputMode": "line",
                "expectedType": expected_type
            }))
        except Exception as e:
            if "close message" not in str(e).lower() and "closed" not in str(e).lower():
                print(f"Input request error: {e}")
            raise Exception("Connection closed")
        
        # Wait for response (use thread to avoid blocking event loop)
        try:
            def get_from_queue():
                return self.input_q.get(timeout=300)  # 5 minute timeout
            
            val = await asyncio.to_thread(get_from_queue)
            if isinstance(val, Exception):
                raise val
            
            # Validate and cast based on type
            val_str = str(val).strip()
            
            if expected_type == "kai":
                # Integer type
                try:
                    if len(val_str.lstrip('-')) > 15:
                        raise ValueError("Integer too large")
                    result = int(val_str)
                except ValueError:
                    raise RuntimeError(f"Runtime Error: Invalid input '{val_str}' for type kai (integer)")
            elif expected_type == "flux":
                # Float type
                try:
                    parts = val_str.lstrip('-').split('.')
                    if len(parts[0]) > 15 or (len(parts) == 2 and len(parts[1]) > 8) or len(parts) > 2:
                        raise ValueError("Float too large")
                    result = float(val_str)
                except ValueError:
                    raise RuntimeError(f"Runtime Error: Invalid input '{val_str}' for type flux (float)")
            elif expected_type == "lani":
                # Boolean type
                if val_str.lower() not in ['iris', 'sage', 'true', 'false']:
                    raise RuntimeError(f"Runtime Error: Invalid input '{val_str}' for type lani (boolean)")
                result = val_str.lower() in ['iris', 'true']
            else:
                result = val_str
            
            # Echo to output buffer
            self.output_buffer += val_str + "\n"
            try:
                await self.ws.send_text(json.dumps({
                    "output": self.output_buffer,
                    "isWaitingForInput": False
                }))
            except Exception as e:
                if "close message" not in str(e).lower() and "closed" not in str(e).lower():
                    print(f"Echo error: {e}")
            
            return result
        except queue.Empty:
            raise RuntimeError("Runtime Error: Input timeout")
    
    async def getch(self) -> str:
        """Async callback for character input (spark)"""
        # Send request for char input
        try:
            await self.ws.send_text(json.dumps({
                "output": self.output_buffer,
                "isWaitingForInput": True,
                "inputMode": "char"
            }))
        except Exception as e:
            if "close message" not in str(e).lower() and "closed" not in str(e).lower():
                print(f"Char input request error: {e}")
            raise Exception("Connection closed")
        
        # Wait for response (use thread to avoid blocking event loop)
        try:
            def get_from_queue():
                return self.input_q.get(timeout=300)
            
            val = await asyncio.to_thread(get_from_queue)
            if isinstance(val, Exception):
                raise val
            
            val_str = str(val)[:1]  # Just first character
            
            # Echo to output buffer (no newline)
            self.output_buffer += val_str
            try:
                await self.ws.send_text(json.dumps({
                    "output": self.output_buffer,
                    "isWaitingForInput": False
                }))
            except Exception as e:
                if "close message" not in str(e).lower() and "closed" not in str(e).lower():
                    print(f"Echo error: {e}")
            
            return val_str
        except queue.Empty:
            raise RuntimeError("Runtime Error: Character input timeout")

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

            if "input" in payload:
                if active_input_q:
                    active_input_q.put(payload["input"])
                continue
                
            code = payload.get("code", "")
            
            if active_input_q:
                active_input_q.put(Exception("ABORT_EXECUTION"))
                active_input_q = None

            # Create progress callback for this compilation
            async def progress_callback(msg: str):
                await websocket.send_text(msg)

            tokens, errors, parse_tree, parser_err, warnings, tac_code = await asyncio.to_thread(
                run_pipeline, code, progress_callback
            )

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
                "transpiledCode": tac_code,  # Send TAC code instead of Python
                "output": "",
                "isWaitingForInput": False,
                "compilationProgress": {
                    "stage": "complete" if not errors else "error",
                    "percentage": 100,
                    "message": "Compilation complete" if not errors else "Compilation failed",
                    "timestamp": int(time.time() * 1000)
                }
            }
            
            # Safely send the final payload
            try:
                await websocket.send_text(json.dumps(response_payload))
            except Exception as e:
                if "close message" in str(e).lower() or "closed" in str(e).lower():
                    break # Safely exit the loop if the client already left
                raise e

            # Run Execution Phase using the TAC interpreter
            # Run Execution Phase using the TAC interpreter
            if not errors and tac_code:
                if ACTIVE_GENERATOR == "tac":
                    active_input_q = queue.Queue()
                    env = ExecutionEnv(websocket, loop, active_input_q)
                    
                    async def run_tac_code(tac: str, environment: ExecutionEnv, q: queue.Queue):
                        try:
                            interpreter = TACInterpreter(
                                tac,
                                input_callback=environment.input,
                                output_callback=environment.output,
                                getch_callback=environment.getch
                            )
                            await interpreter.run()
                            
                            # Send final output
                            await websocket.send_text(json.dumps({
                                "output": environment.output_buffer,
                                "isWaitingForInput": False
                            }))
                        except Exception as e:
                            # ... (keep existing exception handling)
                            err_msg = str(e)
                            if str(e) != "ABORT_EXECUTION":
                                if "Runtime Error" not in err_msg:
                                    err_msg = f"Runtime Error: {err_msg}"
                                
                                prefix = "" if environment.output_buffer.endswith("\n") else "\n"
                                environment.output_buffer += f"{prefix}{err_msg}"
                                
                                try:
                                    await websocket.send_text(json.dumps({
                                        "output": environment.output_buffer,
                                        "isWaitingForInput": False
                                    }))
                                except Exception as send_err:
                                    if "close message" not in str(send_err).lower() and "closed" not in str(send_err).lower():
                                        print(f"Error sending output: {send_err}")
                    
                    asyncio.create_task(run_tac_code(tac_code, env, active_input_q))
                else:
                    # Execute Python Transpiler output
                    active_input_q = queue.Queue()
                    env = ExecutionEnv(websocket, loop, active_input_q)
                    
                    async def run_python_code(python_code: str, environment: ExecutionEnv, q: queue.Queue):
                        try:
                            # 1. Custom thread-safe print function
                            def soluna_print_sync(*args, sep=' ', end='\n'):
                                text = sep.join(map(str, args)) + end
                                environment.output_buffer += text
                                # Safely push the WebSocket message to the main event loop
                                asyncio.run_coroutine_threadsafe(
                                    environment.ws.send_text(json.dumps({
                                        "output": environment.output_buffer
                                    })),
                                    loop
                                )

                            # 2. Custom thread-safe input function
                            def soluna_input_sync(expected_type="let"):
                                # Request input from the frontend
                                asyncio.run_coroutine_threadsafe(
                                    environment.ws.send_text(json.dumps({
                                        "output": environment.output_buffer,
                                        "isWaitingForInput": True,
                                        "inputMode": "line",
                                        "expectedType": expected_type
                                    })),
                                    loop
                                )
                                
                                # Block THIS thread (not the main loop) waiting for user input
                                try:
                                    val = q.get(timeout=300)
                                    if isinstance(val, Exception):
                                        raise val
                                        
                                    val_str = str(val).strip()
                                    
                                    # Basic type coercion based on Soluna's types
                                    if expected_type == "kai":
                                        result = int(val_str)
                                    elif expected_type == "flux":
                                        result = float(val_str)
                                    elif expected_type == "lani":
                                        result = val_str.lower() in ['iris', 'true', 'sage']
                                    else:
                                        result = val_str
                                        
                                    environment.output_buffer += val_str + "\n"
                                    
                                    # Tell frontend we are no longer waiting
                                    asyncio.run_coroutine_threadsafe(
                                        environment.ws.send_text(json.dumps({
                                            "output": environment.output_buffer,
                                            "isWaitingForInput": False
                                        })),
                                        loop
                                    )
                                    return result
                                    
                                except ValueError:
                                    raise RuntimeError(f"Runtime Error: Invalid input '{val_str}' for type {expected_type}")
                                except queue.Empty:
                                    raise RuntimeError("Runtime Error: Input timeout")

                            # 3. Create execution namespace with our injected functions
                            namespace = {
                                '__SolunaList': SolunaList,
                                '__soluna_input': soluna_input_sync,
                                '__soluna_index': soluna_index,
                                '__soluna_set': soluna_set,
                                'print': soluna_print_sync, # Overrides standard print!
                                '__builtins__': builtins,
                            }
                            
                            # 4. Run exec() in a background thread to prevent deadlocking FastAPI
                            def execute():
                                exec(python_code, namespace)
                                
                            await asyncio.to_thread(execute)
                            
                            # Send final execution state
                            await websocket.send_text(json.dumps({
                                "output": environment.output_buffer,
                                "isWaitingForInput": False
                            }))
                            
                        except Exception as e:
                            err_msg = str(e)
                            if err_msg != "ABORT_EXECUTION":
                                if "Runtime Error" not in err_msg:
                                    err_msg = f"Runtime Error: {err_msg}"
                                
                                prefix = "" if environment.output_buffer.endswith("\n") else "\n"
                                environment.output_buffer += f"{prefix}{err_msg}"
                                
                                try:
                                    await websocket.send_text(json.dumps({
                                        "output": environment.output_buffer,
                                        "isWaitingForInput": False
                                    }))
                                except Exception as send_err:
                                    if "close message" not in str(send_err).lower() and "closed" not in str(send_err).lower():
                                        print(f"Error sending output: {send_err}")
                    
                    asyncio.create_task(run_python_code(tac_code, env, active_input_q))

    except WebSocketDisconnect:
        if active_input_q:
            active_input_q.put(Exception("ABORT_EXECUTION"))
    except Exception as e:
        err_msg = str(e)
        # Suppress the server crash print if the user just closed the socket
        if "close message" not in err_msg.lower() and "closed" not in err_msg.lower():
            print(f"WS Handling Error: {err_msg}")