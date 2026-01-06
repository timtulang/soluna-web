import React, { useEffect, useRef, useState } from "react";
import type { ChangeEvent, KeyboardEvent } from "react";

// ... [Keep your type definitions and tokenColors map exactly as they are] ...

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
  // Literals & Identifiers
  comment: "#6a9955", 
  kai_lit: "#b5cea8", 
  flux_lit: "#b5cea8",
  aster_lit: "#b5cea8", 
  id: "#dcdcaa", 
  selene_literal: "#ce9178", 
  blaze_literal: "#ce9178", 
  leo_label: "#4ec9b0", 
  
  // Whitespace
  whitespace: "#ffffff",
  newline: "#ffffff",
  tab: "#ffffff",
  
  // Keywords
  and: "#c586c0", aster: "#c586c0", blaze: "#c586c0", cos: "#c586c0", flux: "#c586c0", 
  hubble: "#c586c0", iris: "#c586c0", ixion: "#c586c0", kai: "#c586c0", lani: "#c586c0", 
  leo: "#c586c0", let: "#c586c0", lumen: "#c586c0", lumina: "#c586c0", luna: "#c586c0", 
  mos: "#c586c0", not: "#c586c0", nova: "#c586c0", or: "#c586c0", orbit: "#c586c0", 
  phase: "#c586c0", sage: "#c586c0", selene: "#c586c0", sol: "#c586c0", soluna: "#c586c0", 
  star: "#c586c0", void: "#c586c0", wane: "#c586c0", warp: "#c586c0", wax: "#c586c0", 
  zara: "#c586c0", zeru: "#c586c0", zeta: "#c586c0",
  
  // Fallbacks
  unknown: "#f44747",
  default_symbol: "#569cd6", 
};

const getColor = (type: string): string => {
  if (tokenColors[type]) { return tokenColors[type]; }
  if (type.length <= 3 && !/^[a-z0-9_]+$/.test(type)) { return tokenColors.default_symbol; }
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
  
  // We use this ref to manually set cursor position after a state update
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    let ws: WebSocket;

    function connect() {
      setWsStatus("CONNECTING");
      ws = new WebSocket("ws://localhost:8000/ws");
      wsRef.current = ws;

      ws.addEventListener("open", () => setWsStatus("CONNECTED"));

      ws.addEventListener("message", (ev) => {
        try {
          const data: WsMessage = JSON.parse(ev.data);
          if (data.tokens) setTokens(data.tokens);
          if (data.errors) setErrors(data.errors);
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

  // --- NEW: Handle Tab Key ---
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault(); // Stop focus from moving
      
      const target = e.currentTarget;
      const start = target.selectionStart;
      const end = target.selectionEnd;
      const indent = "    "; 
      
      const newValue = raw.substring(0, start) + indent + raw.substring(end);
      
      setRaw(newValue);
      sendCodeDebounced(newValue);

      // Move the cursor to after the inserted spaces
      // We need to use setTimeout or useLayoutEffect to ensure this runs after render,
      // but in simple handlers, updating the ref immediately after often works 
      // if React schedules the re-render efficiently. 
      // However, the most reliable way in raw React without a layout effect 
      // is usually scheduling it for the next tick.
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start + indent.length;
        }
      }, 0);
    }
  };

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
                ref={textareaRef} // Attach Ref here
                value={raw}
                onChange={onEditorChange}
                onKeyDown={handleKeyDown} // Attach Key Handler here
                placeholder="// Start typing your code here..."
                className="w-full flex-1 p-6 bg-transparent text-zinc-100 font-mono text-sm resize-none focus:outline-none placeholder-zinc-600 leading-relaxed"
                spellCheck="false"
              />
            </div>

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
                        <td className="px-4 py-1 text-zinc-500 tabular-nums">{t.line}</td>
                        <td className="px-4 py-1 text-zinc-500 tabular-nums">{t.col}</td>
                        <td className="px-4 py-1 text-zinc-300 break-all">{t.value}</td>
                        <td className="px-4 py-1 font-semibold" style={{color: getColor(t.type)}}>{t.type}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>

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