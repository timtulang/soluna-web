import React, { useEffect, useRef, useState } from "react";
import type { ChangeEvent } from "react";

type Token = {
  type: string;
  value: string;
  line: number;
  col: number;
  start: number;
  end: number;
};

type LexerError = {
  type: string;
  message: string;
  line: number;
  col: number;
};

type WsMessage = {
  tokens?: Token[];
  errors?: LexerError[];
};

const tokenColors: Record<string, string> = {
  COMMENT: "#6a9955", 
  KAI_LIT: "#b5cea8", 
  FLUX_LIT: "#b5cea8", 
  ID: "#dcdcaa", 
  SELENE_LITERAL: "#ce9178", 
  BLAZE_LITERAL: "#ce9178", 
  AND: "#c586c0", 
  ASTER: "#c586c0", 
  BLAZE: "#c586c0", 
  COS: "#c586c0", 
  FLUX: "#c586c0", 
  HUBBLE: "#c586c0", 
  IRIS: "#c586c0", 
  IXION: "#c586c0", 
  KAI: "#c586c0", 
  LANI: "#c586c0", 
  LEO: "#c586c0", 
  LET: "#c586c0", 
  LUMEN: "#c586c0", 
  LUMINA: "#c586c0", 
  LUNA: "#c586c0", 
  MOS: "#c586c0", 
  NOT: "#c586c0", 
  NOVA: "#c586c0", 
  OR: "#c586c0", 
  ORBIT: "#c586c0", 
  PHASE: "#c586c0", 
  SAGE: "#c586c0", 
  SELENE: "#c586c0", 
  SOL: "#c586c0", 
  SOLUNA: "#c586c0", 
  STAR: "#c586c0", 
  VOID: "#c586c0", 
  WANE: "#c586c0", 
  WARP: "#c586c0", 
  WAX: "#c586c0", 
  ZARA: "#c586c0", 
  ZERU: "#c586c0", 
  LEO_LABEL: "#4ec9b0", 
  DEFAULT_SYMBOL: "#569cd6", 
  WHITESPACE: "#ffffff", 
  UNKNOWN: "#f44747",
};
const getColor = (type: string): string => {
  if (tokenColors[type]) { return tokenColors[type]; }
  if (type.length <= 3 && !/^[A-Z0-9_]+$/.test(type)) { return tokenColors.DEFAULT_SYMBOL; }
  return "#d4d4d4";
};


// --- Component ---
const App: React.FC = () => {
  const [wsStatus, setWsStatus] = useState<string>("DISCONNECTED");
  const [tokens, setTokens] = useState<Token[]>([]);
  const [raw, setRaw] = useState<string>("");
  const [errors, setErrors] = useState<LexerError[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const sendTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Connect to websocket
  useEffect(() => {
    let ws: WebSocket;

    function connect() {
      setWsStatus("CONNECTING");
      // Ensure this port matches your Python server
      ws = new WebSocket("ws://localhost:8000/ws");
      wsRef.current = ws;

      ws.addEventListener("open", () => setWsStatus("CONNECTED"));

      ws.addEventListener("message", (ev) => {
        try {
          const data: WsMessage = JSON.parse(ev.data);
          
          if (data.tokens) {
            setTokens(data.tokens);
          }
          if (data.errors) {
            setErrors(data.errors);
          }

        } catch (e) {
          console.error("Invalid message from server", e);
        }
      });

      ws.addEventListener("close", () => {
        setWsStatus("DISCONNECTED");
        setTimeout(connect, 800);
      });

      ws.addEventListener("error", (e) => {
        console.error("WebSocket error", e);
        ws.close();
      });
    }

    connect();
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  function sendCodeDebounced(code: string) {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    if (sendTimer.current) clearTimeout(sendTimer.current);
    sendTimer.current = setTimeout(() => {
      try {
        // Send empty tokens array to clear table if code is empty
        if (code.trim() === "") {
            setTokens([]);
            setErrors([]);
        }
        wsRef.current?.send(JSON.stringify({ code }));
      } catch (e) {
        console.error("send failed", e);
      }
    }, 160);
  }
  
  function onEditorChange(e: ChangeEvent<HTMLTextAreaElement>) {
    const code = e.target.value;
    setRaw(code);
    sendCodeDebounced(code);
  }


  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-zinc-950 to-black text-zinc-100 font-sans">
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-96 h-96 bg-yellow-600/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-amber-700/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
      </div>
      <div className="relative z-10 max-w-7xl mx-auto p-6">
        <header className="mb-5">
          <div className="bg-[#0c0d0d] backdrop-blur-xl border border-[#1a1a1a] rounded-2xl p-2 shadow-2xl">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-4">
                <img src="src/assets/logo.png" alt="Soluna Logo" className="w-12 h-12"/>
                <div className="ml-4">
                  <h1 className="text-xl font-bold text-yellow-400">Soluna</h1>
                  <p className="text-zinc-400 text-sm mt-0.5">Lexical Analysis Table</p>
                </div>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-zinc-900/50 border border-zinc-700/50">
                <div className="w-2 h-2 rounded-full animate-pulse" style={{backgroundColor: wsStatus === 'CONNECTED' ? '#22c55e' : '#ef4444'}}></div>
                <span className="text-xs font-semibold tracking-wide">{wsStatus}</span>
              </div>
            </div>
          </div>
        </header>

        {/* Main content */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Left column */}
          <div className="space-y-6">
            {/* Editor */}
            <div className="bg-zinc-900/40 backdrop-blur-xl border border-zinc-800/50 rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[400px]">
              <div className="px-6 py-4 border-b border-zinc-800/50 flex items-center justify-between">
                <h2 className="font-semibold text-zinc-200">Source Code</h2>
                {raw && <span className="text-xs text-zinc-400">{raw.length} chars</span>}
              </div>
              
              <textarea
                value={raw}
                onChange={onEditorChange}
                placeholder="// Start typing your code here..."
                className="w-full flex-1 p-6 bg-transparent text-zinc-100 font-mono text-sm resize-none focus:outline-none placeholder-zinc-600 leading-relaxed"
                spellCheck="false"
              />
            </div>

            {/* Syntax Preview
             <div className="bg-zinc-900/40 backdrop-blur-xl border border-zinc-800/50 rounded-2xl shadow-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-zinc-800/50">
                <h2 className="font-semibold text-zinc-200">Syntax Highlight Preview</h2>
              </div>
              <div className="p-6 font-mono text-sm min-h-[100px] max-h-[200px] overflow-y-auto bg-black/30">
                {tokens.length === 0 && errors.length === 0 ? (
                  <span className="text-zinc-600 italic">Preview will appear here...</span>
                ) : (
                  <div className="whitespace-pre-wrap break-words">
                    {tokens.map((t, i) => (
                      <span key={i} style={{color: getColor(t.type)}}>
                        {t.value}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div> */}

            {errors.length > 0 && (
                <div className="space-y-2">
                  {errors.map((err, i) => (
                    <div key={i} className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-start gap-3">
                      <div className="flex-1">
                        <p className="text-red-300 font-medium text-sm">{err.message}</p>
                        <p className="text-red-400/70 text-xs mt-1">Line {err.line}, Column {err.col}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
          </div>

          {/* Right column: Token Table */}
          <div className="bg-zinc-900/40 backdrop-blur-xl border border-zinc-800/50 rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[800px]">
            <div className="px-6 py-4 border-b border-zinc-800/50 flex items-center justify-between flex-shrink-0 bg-zinc-900/60">
              <h2 className="font-semibold text-zinc-200">Symbol Table</h2>
              {tokens.length > 0 && (
                <span className="px-2.5 py-1 bg-yellow-400/20 text-yellow-300 text-xs font-semibold rounded-full">
                  {tokens.length} Entries
                </span>
              )}
            </div>
            
            <div className="flex-1 overflow-auto">
              {tokens.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-zinc-500">
                  <p className="text-sm font-medium">Waiting for input...</p>
                </div>
              ) : (
                <table className="w-full text-left border-collapse font-mono text-xs sm:text-sm">
                  <thead className="bg-zinc-950/80 sticky top-0 z-10 text-zinc-400 uppercase tracking-wider text-xs">
                    <tr>
                      <th className="px-4 py-3 font-medium border-b border-zinc-800 w-16">Row</th>
                      <th className="px-4 py-3 font-medium border-b border-zinc-800 w-16">Col</th>
                      <th className="px-4 py-3 font-medium border-b border-zinc-800">Lexeme</th>
                      <th className="px-4 py-3 font-medium border-b border-zinc-800">Token</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/50">
                    {tokens.map((t, i) => (
                      <tr key={i} className="hover:bg-zinc-800/30 transition-colors group">
                        {/* Row Number */}
                        <td className="px-4 py-1 text-zinc-500 tabular-nums">
                          {t.line}
                        </td>
                        {/* Column Number */}
                        <td className="px-4 py-1 text-zinc-500 tabular-nums">
                          {t.col}
                        </td>
                        {/* Lexeme Value */}
                        <td className="px-4 py-1 text-zinc-300 break-all">
                           {t.value}
                        </td>
                        {/* Token Type */}
                        <td className="px-4 py-1 font-semibold" style={{color: getColor(t.type)}}>
                          {t.type}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-8 text-center">
          <div className="inline-flex items-center gap-3 px-6 py-3 bg-zinc-900/40 backdrop-blur-xl border border-zinc-800/50 rounded-full text-sm">
            <span className="text-zinc-400">Server:</span>
            <code className="text-yellow-400 font-mono text-xs">ws://localhost:8000/ws</code>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default App;