import React, { useEffect, useRef, useState } from "react";
import type { ChangeEvent, KeyboardEvent } from "react";

// --- Types ---

type Token = {
  type: string;
  value: string;
  alias?: string; 
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
  start: number;
  end: number;
};

// FIX: Changed [key: string]: any to [key: string]: unknown to satisfy TypeScript strict mode
type ParseNode = {
  type?: string;       
  data?: string;       
  rule?: string;       
  value?: string;
  children?: ParseNode[];
  [key: string]: unknown;  // Type-safe catch-all
};

type WsMessage = {
  tokens?: Token[];
  errors?: LexerError[];
  parseTree?: ParseNode;
};

type CodeFile = {
  id: string;
  name: string;
  content: string;
};

// --- Color Mapping ---

const tokenColors: Record<string, string> = {
  // --- Syntax Rules (Backend Rules) ---
  program: "#facc15", 
  globaldeclarations: "#e4e4e7", 
  functiondefinition: "#c586c0", 
  variabledeclaration: "#4ec9b0", 
  block: "#e4e4e7",
  ifstatement: "#c586c0",
  whileloop: "#c586c0",
  forloop: "#c586c0",
  returnstatement: "#c586c0",
  assignment: "#4ec9b0",
  expressionstatement: "#e4e4e7",

  // --- Literals & Identifiers ---
  identifier: "#9cdcfe", // Light Blue
  literal: "#b5cea8",    // Light Green 
  
  // --- Reserved Words (Keywords) ---
  if: "#c586c0",
  else: "#c586c0",
  while: "#c586c0",
  for: "#c586c0",
  return: "#c586c0",
  break: "#c586c0",
  continue: "#c586c0",
  
  // Declarations & Types
  var: "#569cd6",
  let: "#569cd6",
  const: "#569cd6",
  int: "#569cd6",
  float: "#569cd6",
  string: "#569cd6",
  char: "#569cd6",
  void: "#569cd6",
  bool: "#569cd6",
  
  // --- Custom/Other Tokens ---
  kai_lit: "#b5cea8", 
  flux_lit: "#b5cea8",
  aster_lit: "#b5cea8", 
  selene_literal: "#ce9178", 
  blaze_literal: "#ce9178", 
  leo_label: "#4ec9b0", 
  
  // --- Operators & Punctuation ---
  lparen: "#ffd700",
  rparen: "#ffd700",
  lbrace: "#ffd700",
  rbrace: "#ffd700",
  semi: "#d4d4d4",
  comma: "#d4d4d4",
  
  // --- Whitespace ---
  whitespace: "#ffffff",
  newline: "#ffffff",
  tab: "#ffffff",
  
  // --- Fallbacks ---
  unknown: "#f44747",
  default_symbol: "#569cd6", 
};

// Safe Color Lookup
const getColor = (rawType: string): string => {
  if (!rawType) return "#d4d4d4";
  const type = String(rawType).toLowerCase(); 
  
  if (tokenColors[type]) { return tokenColors[type]; }
  
  // Heuristic: Short uppercase codes (EQ, NEQ, GT) are likely operators/tokens
  if (type.length <= 4 && !/^[a-z0-9_]+$/.test(type)) { return tokenColors.default_symbol; }
  
  return "#d4d4d4";
};

// --- Recursive Tree Component ---

const TreeNode: React.FC<{ node: ParseNode; depth?: number }> = ({ node, depth = 0 }) => {
  const [expanded, setExpanded] = useState(true);
  
  if (!node) return null;

  // Robust Children Check
  const children = Array.isArray(node.children) ? node.children : [];
  const hasChildren = children.length > 0;
  
  // Prioritize 'type' (Backend), then 'data' (Lark default), then 'rule'
  const rawType = node.type || node.data || node.rule || "Unknown";
  // Ensure rawType is treated as a string before manipulation
  const typeStr = String(rawType);
  const typeKey = typeStr.toLowerCase();

  const nodeColor = tokenColors[typeKey] 
      ? tokenColors[typeKey]
      : hasChildren 
        ? "#e4e4e7" 
        : getColor(typeStr);

  // Debug handler
  const handleNodeClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    console.log("Clicked Node Data:", node); 
    setExpanded(!expanded);
  };

  return (
    <div className="font-mono text-sm leading-relaxed select-none">
      <div 
        className={`flex items-center gap-2 py-0.5 hover:bg-white/5 rounded px-2 cursor-pointer transition-colors`}
        style={{ paddingLeft: `${depth * 20 + 8}px` }}
        onClick={handleNodeClick}
      >
        <span className={`w-4 h-4 flex items-center justify-center text-zinc-500 text-[10px] transform transition-transform ${expanded ? 'rotate-90' : ''}`}>
          {hasChildren ? '▶' : '•'}
        </span>
        <span 
          className="font-semibold" 
          style={{ color: nodeColor }}
          title={`Type: ${typeStr}`} 
        >
          {typeStr}
        </span>
        {node.value && (
          <span className="text-zinc-500 text-xs">
             = <span className="text-[#ce9178]">"{node.value}"</span>
          </span>
        )}
      </div>
      {expanded && hasChildren && (
        <div className="border-l border-zinc-800 ml-[15px] relative">
          {children.map((child, i) => (
             child ? <TreeNode key={i} node={child} depth={depth + 1} /> : null
          ))}
        </div>
      )}
    </div>
  );
};

// --- Main App Component ---

const App: React.FC = () => {
  const [wsStatus, setWsStatus] = useState<string>("DISCONNECTED");
  
  const [files, setFiles] = useState<CodeFile[]>([
    { id: '1', name: 'main.sl', content: '' }
  ]);
  const [activeFileId, setActiveFileId] = useState<string>('1');
  const [renamingId, setRenamingId] = useState<string | null>(null);

  const [tokens, setTokens] = useState<Token[]>([]);
  const [parseTree, setParseTree] = useState<ParseNode | null>(null);
  const [errors, setErrors] = useState<LexerError[]>([]);
  
  const [activeTab, setActiveTab] = useState<'symbol' | 'tree'>('symbol');
  const [showErrors, setShowErrors] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);
  const sendTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const activeFile = files.find(f => f.id === activeFileId) || files[0];
  const lineCount = activeFile.content.split('\n').length;
  const lines = Array.from({ length: lineCount }, (_, i) => i + 1);

  useEffect(() => {
    let ws: WebSocket;

    function connect() {
      setWsStatus("CONNECTING");
      // Use environment variable for URL if available (for Vercel deployment)
      const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";
      ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.addEventListener("open", () => setWsStatus("CONNECTED"));

      ws.addEventListener("message", (ev) => {
        try {
          const data: WsMessage = JSON.parse(ev.data);
          if (data.tokens) setTokens(data.tokens);
          if (data.errors) setErrors(data.errors);
          
          if (data.parseTree) {
             setParseTree(data.parseTree);
          } else if (data.errors && data.errors.length > 0) {
             setParseTree(null);
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

  function triggerAnalysis(code: string) {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    if (sendTimer.current) clearTimeout(sendTimer.current);
    
    sendTimer.current = setTimeout(() => {
      try {
        if (code.trim() === "") {
            setTokens([]);
            setErrors([]);
            setParseTree(null);
        }
        wsRef.current?.send(JSON.stringify({ code }));
      } catch (e) {
        console.error("send failed", e);
      }
    }, 160);
  }

  const handleScroll = () => {
    if (textareaRef.current && lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  };

  function handleCodeChange(e: ChangeEvent<HTMLTextAreaElement>) {
    const newContent = e.target.value;
    setFiles(prev => prev.map(f => 
      f.id === activeFileId ? { ...f, content: newContent } : f
    ));
    triggerAnalysis(newContent);
  }

  function handleAddFile() {
    const newId = Date.now().toString();
    const newFile: CodeFile = {
      id: newId,
      name: `script_${files.length}.sl`,
      content: ''
    };
    setFiles([...files, newFile]);
    setActiveFileId(newId);
    triggerAnalysis('');
    
    setTimeout(() => {
        if(textareaRef.current) textareaRef.current.focus();
    }, 0);
  }

  function handleDownload() {
    const blob = new Blob([activeFile.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = activeFile.name; 
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function triggerFileUpload() {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  }

  function handleFileRead(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (ev) => {
      const content = ev.target?.result as string;
      const newId = Date.now().toString();
      const newFile: CodeFile = { id: newId, name: file.name, content: content };
      setFiles(prev => [...prev, newFile]);
      setActiveFileId(newId);
      triggerAnalysis(content);
      if (fileInputRef.current) fileInputRef.current.value = '';
    };
    reader.readAsText(file);
  }

  function handleCloseFile(e: React.MouseEvent, id: string) {
    e.stopPropagation();
    if (files.length === 1) {
       setFiles([{...files[0], content: ''}]);
       triggerAnalysis('');
       return;
    }
    const newFiles = files.filter(f => f.id !== id);
    setFiles(newFiles);
    if (activeFileId === id) {
        const next = newFiles[0];
        setActiveFileId(next.id);
        triggerAnalysis(next.content);
    }
  }

  function handleTabClick(id: string) {
    setActiveFileId(id);
    const file = files.find(f => f.id === id);
    if(file) triggerAnalysis(file.content);
  }
  
  function handleRename(id: string, newName: string) {
    setFiles(prev => prev.map(f => f.id === id ? { ...f, name: newName } : f));
    setRenamingId(null);
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault(); 
      const target = e.currentTarget;
      const start = target.selectionStart;
      const end = target.selectionEnd;
      const indent = "    "; 
      
      const newContent = activeFile.content.substring(0, start) + indent + activeFile.content.substring(end);
      setFiles(prev => prev.map(f => f.id === activeFileId ? { ...f, content: newContent } : f));
      triggerAnalysis(newContent);
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start + indent.length;
        }
      }, 0);
    }
  };

  const lexerErrors = errors.filter(e => e.type !== 'PARSER_ERROR');
  const parserErrors = errors.filter(e => e.type === 'PARSER_ERROR');
  const activeErrors = activeTab === 'symbol' ? lexerErrors : parserErrors;
  const hasErrors = activeErrors.length > 0;
  const isErrorButtonDisabled = !hasErrors && !showErrors;

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-zinc-950 to-black text-zinc-100 font-sans">
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-96 h-96 bg-yellow-600/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-amber-700/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}}></div>
      </div>
      <div className="relative z-10 max-w-[90rem] mx-auto p-6">
        <header className="mb-5">
          <div className="bg-[#0c0d0d] backdrop-blur-xl border border-[#1a1a1a] rounded-2xl p-2 shadow-2xl">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-4">
                <img src="src/assets/logo.png" alt="Soluna Logo" className="w-12 h-12"/>
                <div className="ml-4">
                  <h1 className="text-xl font-bold text-yellow-400">Soluna</h1>
                  <p className="text-zinc-400 text-sm mt-0.5">Lexical Analysis & Parsing</p>
                </div>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-zinc-900/50 border border-zinc-700/50">
                <div className="w-2 h-2 rounded-full animate-pulse" style={{backgroundColor: wsStatus === 'CONNECTED' ? '#22c55e' : '#ef4444'}}></div>
                <span className="text-xs font-semibold tracking-wide">{wsStatus}</span>
              </div>
            </div>
          </div>
        </header>

        <div className="grid lg:grid-cols-12 gap-6">
          <div className="lg:col-span-7 space-y-6 min-w-0">
            <div className="bg-zinc-900/40 backdrop-blur-xl border border-zinc-800/50 rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[600px]">
              <div className="flex items-center justify-between bg-zinc-950/50 border-b border-zinc-800/50">
                <div className="flex-1 flex overflow-x-auto scrollbar-hide">
                   {files.map(file => (
                     <div 
                       key={file.id}
                       onClick={() => handleTabClick(file.id)}
                       onDoubleClick={() => setRenamingId(file.id)}
                       className={`
                         group flex items-center gap-2 px-4 py-3 text-xs font-medium cursor-pointer border-r border-zinc-800/50 min-w-[120px] max-w-[200px] select-none flex-shrink-0
                         ${activeFileId === file.id ? 'bg-zinc-900/60 text-yellow-400 border-b-2 border-b-yellow-400' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900/30'}
                       `}
                     >
                       <span className="opacity-70">📄</span>
                       {renamingId === file.id ? (
                          <input 
                            autoFocus
                            className="bg-transparent text-white outline-none w-full"
                            defaultValue={file.name}
                            onBlur={(e) => handleRename(file.id, e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleRename(file.id, e.currentTarget.value)}
                          />
                       ) : (
                          <span className="truncate flex-1">{file.name}</span>
                       )}
                       <button 
                         onClick={(e) => handleCloseFile(e, file.id)}
                         className={`
                           w-5 h-5 rounded hover:bg-zinc-700/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity
                           ${files.length === 1 ? 'hidden' : ''}
                         `}
                       >
                         ×
                       </button>
                     </div>
                   ))}
                </div>

                <div className="flex items-center px-1 bg-zinc-950/50 h-full border-l border-zinc-800/50 z-10 shadow-[-10px_0_15px_-5px_rgba(0,0,0,0.5)]">
                   <input 
                     type="file" 
                     ref={fileInputRef} 
                     onChange={handleFileRead} 
                     className="hidden" 
                     accept=".sl,.txt,.js,.ts"
                   />
                   <button onClick={handleAddFile} className="w-9 h-9 flex items-center justify-center text-zinc-500 hover:text-yellow-400 hover:bg-zinc-900/50 rounded transition-colors" title="New File">
                     <span className="text-lg leading-none">+</span>
                   </button>
                   <div className="w-px h-5 bg-zinc-800 mx-1"></div>
                   <button onClick={triggerFileUpload} className="w-9 h-9 flex items-center justify-center text-zinc-500 hover:text-blue-400 hover:bg-zinc-900/50 rounded transition-colors" title="Open File">
                     <span className="text-lg leading-none">📂</span>
                   </button>
                   <button onClick={handleDownload} className="w-9 h-9 flex items-center justify-center text-zinc-500 hover:text-green-400 hover:bg-zinc-900/50 rounded transition-colors" title="Save File">
                     <span className="text-lg leading-none">💾</span>
                   </button>
                </div>
              </div>
              
              <div className="flex flex-1 relative overflow-hidden">
                <div ref={lineNumbersRef} className="w-12 flex-shrink-0 pt-6 pr-2 text-right font-mono text-sm leading-relaxed text-zinc-600 select-none bg-zinc-900/20 border-r border-zinc-800/50 overflow-hidden">
                    {lines.map((line) => (
                        <div key={line}>{line}</div>
                    ))}
                </div>
                <textarea
                  ref={textareaRef}
                  value={activeFile.content}
                  onChange={handleCodeChange}
                  onKeyDown={handleKeyDown}
                  onScroll={handleScroll}
                  placeholder={`// Start coding in ${activeFile.name}...`}
                  className="flex-1 w-full h-full pt-6 pl-4 pr-6 pb-6 bg-transparent text-zinc-100 font-mono text-sm resize-none focus:outline-none placeholder-zinc-600 leading-relaxed outline-none border-none whitespace-pre overflow-x-auto"
                  spellCheck="false"
                />
              </div>
            </div>
          </div>

          <div className="lg:col-span-5 bg-zinc-900/40 backdrop-blur-xl border border-zinc-800/50 rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[600px] min-w-0">
            <div className="px-2 py-2 border-b border-zinc-800/50 flex items-center justify-between flex-shrink-0 bg-zinc-900/60">
              <div className="flex space-x-1 bg-zinc-950/50 p-1 rounded-lg">
                 <button onClick={() => { setActiveTab('symbol'); setShowErrors(false); }} className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${activeTab === 'symbol' ? 'bg-zinc-800 text-yellow-400 shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}>Lexer</button>
                 <button onClick={() => { setActiveTab('tree'); setShowErrors(false); }} className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${activeTab === 'tree' ? 'bg-zinc-800 text-yellow-400 shadow-sm' : 'text-zinc-500 hover:text-zinc-300'}`}>Parser</button>
              </div>

              <div className="flex items-center gap-3">
                 <button 
                   onClick={() => setShowErrors(!showErrors)}
                   className={`
                      relative px-3 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full border transition-all
                      ${showErrors ? 'bg-red-500/20 text-red-400 border-red-500/30 hover:bg-red-500/30' : hasErrors ? 'bg-zinc-800 text-zinc-400 border-zinc-700 hover:text-red-400' : 'bg-zinc-800/50 text-zinc-600 border-zinc-800/50 cursor-not-allowed'}
                   `}
                   disabled={isErrorButtonDisabled}
                 >
                    {showErrors ? "Hide Errors" : hasErrors ? `Show Errors (${activeErrors.length})` : "No Errors"}
                 </button>

                 {tokens.length > 0 && (
                   <span className="mr-2 px-2.5 py-1 bg-yellow-400/10 text-yellow-500/80 text-[10px] font-semibold rounded-full border border-yellow-400/10">
                     {activeTab === 'symbol' ? `${tokens.length} TOKENS` : parseTree ? 'TREE BUILT' : 'NO TREE'}
                   </span>
                 )}
              </div>
            </div>
            
            <div className="flex-1 overflow-auto p-0">
              {showErrors ? (
                <div className="p-4 space-y-2">
                   {activeErrors.length === 0 ? (
                      <div className="text-center text-zinc-500 mt-10 text-sm">
                        <p>No errors in this phase.</p>
                        <p className="text-xs mt-2 opacity-50">You can hide this view now.</p>
                      </div>
                   ) : (
                      activeErrors.map((err, i) => (
                        <div key={i} className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3">
                          <span className="text-red-400 mt-0.5">⚠</span>
                          <div>
                            <p className="text-red-300 font-medium text-xs font-mono">{err.message}</p>
                            {err.line > 0 && <p className="text-red-400/50 text-[10px] mt-1">Line {err.line}, Col {err.col}</p>}
                          </div>
                        </div>
                      ))
                   )}
                </div>
              ) : (
                <>
                  {activeTab === 'symbol' && (
                     tokens.length === 0 ? (
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
                              <td className="px-4 py-1 text-zinc-300 break-all">
                                {t.value}
                                {t.alias && <span className="ml-2 text-zinc-500 text-[10px] tracking-wide">→ {t.alias}</span>}
                              </td>
                              <td className="px-4 py-1 font-semibold" style={{color: getColor(t.type)}}>{t.type}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )
                  )}

                  {activeTab === 'tree' && (
                    <div className="p-4 space-y-2">
                       {lexerErrors.length > 0 ? (
                         <div className="flex flex-col items-center justify-center h-full text-red-400 mt-10">
                            <span className="text-3xl mb-2">⚠</span>
                            <p className="font-medium">Parser did not run</p>
                            <p className="text-sm opacity-80 mt-1">Please fix lexical errors.</p>
                         </div>
                       ) : parserErrors.length === 0 ? (
                          <div className="text-center text-zinc-500 mt-10 text-sm">
                            <p>No parser errors.</p>
                          </div>
                       ) : (
                          parserErrors.map((err, i) => (
                            <div key={i} className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3">
                              <span className="text-red-400 mt-0.5">⚠</span>
                              <div>
                                <p className="text-red-300 font-medium text-xs font-mono">{err.message}</p>
                                {err.line > 0 && <p className="text-red-400/50 text-[10px] mt-1">Line {err.line}, Col {err.col}</p>}
                              </div>
                            </div>
                          ))
                       )}
                    </div>
                  )}
                </>
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