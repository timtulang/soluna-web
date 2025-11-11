import React, { useEffect, useRef, useState } from "react";

// Types
type Token = {
  type: string;
  value: string;
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
  error?: LexerError;
};

// Token colors with modern palette
const tokenColors: Record<string, string> = {
  COMMENT: "#7c9d8f",
  KAI_LIT: "#a5d6a7",
  FLUX_LIT: "#a5d6a7",
  ID: "#ffd54f",
  SELENE_LITERAL: "#ff8a65",
  CHAR_LITERAL: "#ff8a65",
  AND: "#ba68c8",
  ASTER: "#ba68c8",
  BLAZE: "#ba68c8",
  COS: "#ba68c8",
  FLUX: "#ba68c8",
  HUBBLE: "#ba68c8",
  IRIS: "#ba68c8",
  IXION: "#ba68c8",
  KAI: "#ba68c8",
  LANI: "#ba68c8",
  LEO: "#ba68c8",
  LET: "#ba68c8",
  LUMEN: "#ba68c8",
  LUMINA: "#ba68c8",
  LUNA: "#ba68c8",
  MOS: "#ba68c8",
  NOT: "#ba68c8",
  NOVA: "#ba68c8",
  OR: "#ba68c8",
  ORBIT: "#ba68c8",
  PHASE: "#ba68c8",
  SAGE: "#ba68c8",
  SELENE: "#ba68c8",
  SOL: "#ba68c8",
  SOLUNA: "#ba68c8",
  STAR: "#ba68c8",
  VOID: "#ba68c8",
  WANE: "#ba68c8",
  WARP: "#ba68c8",
  WAX: "#ba68c8",
  ZARA: "#ba68c8",
  ZERU: "#ba68c8",
  LEO_LABEL: "#4dd0e1",
  DEFAULT_SYMBOL: "#64b5f6",
  WHITESPACE: "#ffffff",
  UNKNOWN: "#ef5350",
};

const getColor = (type: string): string => {
  if (tokenColors[type]) return tokenColors[type];
  if (type.length <= 3 && !/^[A-Z0-9_]+$/.test(type))
    return tokenColors.DEFAULT_SYMBOL;
  return "#e0e0e0";
};

const App: React.FC = () => {
  const [wsStatus, setWsStatus] = useState<string>("DISCONNECTED");
  const [tokens, setTokens] = useState<Token[]>([]);
  const [raw, setRaw] = useState<string>("");
  const [error, setError] = useState<LexerError | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const sendTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

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
          if (data.error) {
            setError(data.error);
            setTokens([]);
          } else if (data.tokens) {
            setError(null);
            setTokens(data.tokens);
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
        wsRef.current?.send(JSON.stringify({ code }));
      } catch (e) {
        console.error("send failed", e);
      }
    }, 160);
  }

  function onEditorChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    const code = e.target.value;
    setRaw(code);
    sendCodeDebounced(code);
  }

  const getStatusColor = () => {
    switch (wsStatus) {
      case "CONNECTED": return "#10b981";
      case "CONNECTING": return "#f59e0b";
      default: return "#ef4444";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-zinc-950 to-black text-zinc-100">
      {/* Animated orbs - These are already yellow/amber and look great! */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-96 h-96 bg-yellow-600/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-amber-700/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto p-6">
        {/* Header */}
        <header className="mb-8">
          {/* Using darker, neutral colors */}
          <div className="bg-[#0c0d0d] backdrop-blur-xl border border-[#1a1a1a] rounded-2xl p-2 shadow-2xl">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-4">
                {/* --- ADDED LOGO --- */}
                <img 
                  src="src/assets/logo.png" 
                  alt="Soluna Logo" 
                  className="w-12 h-12"
                />
                <div>
                  {/* --- UPDATED to logo yellow --- */}
                  <h1 className="text-xl font-bold text-yellow-400">
                    Soluna
                  </h1>
                  {/* --- UPDATED to neutral zinc --- */}
                  <p className="text-zinc-400 text-sm mt-0.5">Real-time token visualization</p>
                </div>
              </div>
              
              <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-zinc-900/50 border border-zinc-700/50">
                <div 
                  className="w-2 h-2 rounded-full animate-pulse" 
                  style={{backgroundColor: getStatusColor()}}
                ></div>
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
            <div className="bg-zinc-900/40 backdrop-blur-xl border border-zinc-800/50 rounded-2xl shadow-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-zinc-800/50 flex items-center justify-between">
                <h2 className="font-semibold text-zinc-200">Code Editor</h2>
                {raw && <span className="text-xs text-zinc-400">{raw.length} chars</span>}
              </div>
              
              {/* Error: Kept as RED for usability */}
              {error && (
                <div className="mx-6 mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-start gap-3">
                  <svg className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" />
                  </svg>
                  <div className="flex-1">
                    <p className="text-red-300 font-medium text-sm">{error.message}</p>
                    <p className="text-red-400/70 text-xs mt-1">Line {error.line}, Column {error.col}</p>
                  </div>
                </div>
              )}

              <textarea
                value={raw}
                onChange={onEditorChange}
                placeholder="// Start typing your code here..."
                className="w-full h-64 p-6 bg-transparent text-zinc-100 font-mono text-sm resize-none focus:outline-none placeholder-zinc-600"
                spellCheck="false"
              />
            </div>

            {/* Preview */}
            <div className="bg-zinc-900/40 backdrop-blur-xl border border-zinc-800/50 rounded-2xl shadow-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-zinc-800/50">
                <h2 className="font-semibold text-zinc-200">Syntax Preview</h2>
              </div>
              {/* Using a pure black background for preview, like the 'S' in the logo */}
              <div className="p-6 font-mono text-sm min-h-[160px] bg-black/30">
                {tokens.length === 0 && !error ? (
                  <span className="text-zinc-600 italic">Your syntax-highlighted code will appear here...</span>
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
            </div>
          </div>

          {/* Right column */}
          <div className="space-y-6">
            {/* Raw Input */}
            <div className="bg-zinc-900/40 backdrop-blur-xl border border-zinc-800/50 rounded-2xl shadow-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-zinc-800/50">
                <h2 className="font-semibold text-zinc-200">Raw Input</h2>
              </div>
              <pre className="p-6 text-sm font-mono text-zinc-300 bg-black/30 overflow-x-auto min-h-[120px]">
                {raw || <span className="text-zinc-600 italic">No input yet...</span>}
              </pre>
            </div>

            {/* Tokens */}
            <div className="bg-zinc-900/40 backdrop-blur-xl border border-zinc-800/50 rounded-2xl shadow-2xl overflow-hidden flex flex-col" style={{maxHeight: '600px'}}>
              <div className="px-6 py-4 border-b border-zinc-800/50 flex items-center justify-between flex-shrink-0">
                <h2 className="font-semibold text-zinc-200">Tokens</h2>
                {tokens.length > 0 && (
                  /* --- UPDATED purple to yellow --- */
                  <span className="px-2.5 py-1 bg-yellow-400/20 text-yellow-300 text-xs font-semibold rounded-full">
                    {tokens.length}
                  </span>
                )}
              </div>
              
              <div className="flex-1 overflow-y-auto p-6">
                {tokens.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full min-h-[240px] text-zinc-500">
                    <svg className="w-16 h-16 mb-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                    <p className="text-sm font-medium">No tokens detected</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {tokens.map((t, i) => (
                      <div 
                        key={i} 
                        className="p-3 bg-zinc-950/40 rounded-lg border border-zinc-800/30 hover:border-zinc-700/50 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <span 
                            className="font-mono text-xs font-semibold px-2 py-1 rounded bg-zinc-800/50"
                            style={{color: getColor(t.type)}}
                          >
                            {t.type}
                          </span>
                          <span className="font-mono text-sm text-zinc-300 flex-1 text-right break-all">
                            {JSON.stringify(t.value)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-8 text-center">
          <div className="inline-flex items-center gap-3 px-6 py-3 bg-zinc-900/40 backdrop-blur-xl border border-zinc-800/50 rounded-full text-sm">
            <span className="text-zinc-400">WebSocket:</span>
            {/* --- UPDATED purple to yellow --- */}
            <code className="text-yellow-400 font-mono text-xs">ws://localhost:8000/ws</code>
            <span className="text-zinc-700">•</span>
            <span className="text-zinc-500">Real-time analysis</span>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default App;