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

type ParseNode = {
  type?: string;       
  data?: string;       
  rule?: string;       
  value?: string;
  children?: ParseNode[];
  [key: string]: unknown;
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

// --- Color Mapping (Yellow/Black Theme) ---

const tokenColors: Record<string, string> = {
  program: "#facc15", 
  globaldeclarations: "#a1a1aa", 
  functiondefinition: "#facc15", 
  variabledeclaration: "#2dd4bf", 
  block: "#a1a1aa",
  ifstatement: "#c084fc", 
  whileloop: "#c084fc",
  forloop: "#c084fc",
  returnstatement: "#c084fc",
  assignment: "#2dd4bf",
  expressionstatement: "#a1a1aa",

  identifier: "#60a5fa", 
  literal: "#4ade80",    
  
  if: "#c084fc", else: "#c084fc", while: "#c084fc", for: "#c084fc",
  return: "#c084fc", break: "#c084fc", continue: "#c084fc",
  
  var: "#2dd4bf", let: "#2dd4bf", const: "#2dd4bf",
  int: "#2dd4bf", float: "#2dd4bf", string: "#2dd4bf",
  char: "#2dd4bf", void: "#2dd4bf", bool: "#2dd4bf",
  
  lparen: "#facc15", rparen: "#facc15",
  lbrace: "#facc15", rbrace: "#facc15",
  
  unknown: "#f87171",
  default_symbol: "#a1a1aa", 
};

const getColor = (rawType: string): string => {
  if (!rawType) return "#a1a1aa";
  const type = String(rawType).toLowerCase(); 
  if (tokenColors[type]) return tokenColors[type];
  if (type.length <= 4 && !/^[a-z0-9_]+$/.test(type)) return "#a1a1aa";
  return "#a1a1aa";
};

// --- Icons ---

const IconFile = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
    <path d="M13.71 4.29l-3-3L10 1H4L3 2v12l1 1h9l1-1V5l-.29-.71zM13 14H4V2h5v4h4v8z"/>
  </svg>
);
const IconClose = () => (
  <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
    <path d="M7.116 8l-4.558 4.558.884.884L8 8.884l4.558 4.558.884-.884L8.884 8l4.558-4.558-.884-.884L8 7.116 3.442 2.558l-.884.884L7.116 8z"/>
  </svg>
);
const IconChevronRight = ({ rotated }: { rotated?: boolean }) => (
  <svg 
    width="16" height="16" viewBox="0 0 16 16" fill="currentColor" 
    style={{ transform: rotated ? 'rotate(90deg)' : 'none', transition: 'transform 0.1s' }}
  >
    <path d="M6 4l4 4-4 4V4z"/>
  </svg>
);
const IconError = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="#f87171">
    <path d="M8 1L1 14h14L8 1zm0 2.5L12.5 13H3.5L8 3.5zM7 11v1h2v-1H7zm0-5v4h2V6H7z"/>
  </svg>
);
const IconCheck = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4ade80" strokeWidth="2">
    <path d="M20 6L9 17l-5-5"/>
  </svg>
);

// --- Main App Component ---

const App: React.FC = () => {
  // --- State ---
  const [wsStatus, setWsStatus] = useState<string>("DISCONNECTED");
  const [files, setFiles] = useState<CodeFile[]>([{ id: '1', name: 'main.sl', content: '' }]);
  const [activeFileId, setActiveFileId] = useState<string>('1');
  
  // UI State
  const [showLeftSidebar, setShowLeftSidebar] = useState(true);
  const [showRightSidebar, setShowRightSidebar] = useState(true);
  const [activeRightTab, setActiveRightTab] = useState<'lexer' | 'parser'>('lexer');
  const [menuOpen, setMenuOpen] = useState<string | null>(null);
  
  // Data State
  const [tokens, setTokens] = useState<Token[]>([]);
  const [parseTree, setParseTree] = useState<ParseNode | null>(null);
  const [errors, setErrors] = useState<LexerError[]>([]);

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const sendTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const activeFile = files.find(f => f.id === activeFileId) || files[0];
  const lineCount = activeFile.content.split('\n').length;
  const lines = Array.from({ length: lineCount }, (_, i) => i + 1);

  // --- WebSocket ---

  useEffect(() => {
    let ws: WebSocket;
    function connect() {
      setWsStatus("CONNECTING");
      const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";
      ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.addEventListener("open", () => setWsStatus("CONNECTED"));
      ws.addEventListener("message", (ev) => {
        try {
          const data: WsMessage = JSON.parse(ev.data);
          if (data.tokens) setTokens(data.tokens);
          if (data.errors) setErrors(data.errors);
          if (data.parseTree) setParseTree(data.parseTree);
          else if (data.errors && data.errors.length > 0) setParseTree(null);
        } catch (e) { console.error(e); }
      });
      ws.addEventListener("close", () => { setWsStatus("DISCONNECTED"); setTimeout(connect, 1000); });
    }
    connect();
    return () => { wsRef.current?.close(); };
  }, []);

  function triggerAnalysis(code: string) {
    if (sendTimer.current) clearTimeout(sendTimer.current);
    sendTimer.current = setTimeout(() => {
      if (code.trim() === "") {
          setTokens([]); setErrors([]); setParseTree(null);
      }
      if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ code }));
      }
    }, 200);
  }

  // --- Actions ---

  function handleCodeChange(e: ChangeEvent<HTMLTextAreaElement>) {
    const newContent = e.target.value;
    setFiles(prev => prev.map(f => f.id === activeFileId ? { ...f, content: newContent } : f));
    triggerAnalysis(newContent);
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Tab') {
      e.preventDefault(); 
      const target = e.currentTarget;
      const start = target.selectionStart; const end = target.selectionEnd;
      const newContent = activeFile.content.substring(0, start) + "    " + activeFile.content.substring(end);
      setFiles(prev => prev.map(f => f.id === activeFileId ? { ...f, content: newContent } : f));
      triggerAnalysis(newContent);
      setTimeout(() => { if (textareaRef.current) textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start + 4; }, 0);
    }
  }

  function handleAddFile() {
    const newId = Date.now().toString();
    setFiles([...files, { id: newId, name: `script_${files.length}.sl`, content: '' }]);
    setActiveFileId(newId);
    triggerAnalysis('');
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
        setActiveFileId(newFiles[0].id);
        triggerAnalysis(newFiles[0].content);
    }
  }

  const saveFile = () => {
    const blob = new Blob([activeFile.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = activeFile.name; 
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setMenuOpen(null);
  };

  const saveFileAs = () => {
    const newName = prompt("Save As:", activeFile.name);
    if (newName) {
        setFiles(prev => prev.map(f => f.id === activeFileId ? { ...f, name: newName } : f));
        setTimeout(() => {
            const a = document.createElement('a');
            const blob = new Blob([activeFile.content], { type: 'text/plain' });
            a.href = URL.createObjectURL(blob);
            a.download = newName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }, 100);
    }
    setMenuOpen(null);
  };

  const openFile = () => {
    fileInputRef.current?.click();
    setMenuOpen(null);
  };

  const handleFileRead = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const content = ev.target?.result as string;
      const newId = Date.now().toString();
      setFiles([...files, { id: newId, name: file.name, content }]);
      setActiveFileId(newId);
      triggerAnalysis(content);
    };
    reader.readAsText(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleScroll = () => {
    if (textareaRef.current && lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  };

  // --- Derived ---
  const lexerErrors = errors.filter(e => e.type !== 'PARSER_ERROR');
  const parserErrors = errors.filter(e => e.type === 'PARSER_ERROR');
  const activeErrors = activeRightTab === 'lexer' ? lexerErrors : parserErrors;

  return (
    <div className="h-screen w-screen flex flex-col bg-black text-zinc-300 font-sans overflow-hidden select-none">
      
      {/* 1. TOP MENU BAR */}
      <div className="h-9 bg-zinc-950 flex items-center px-3 text-[13px] border-b border-zinc-900 z-50">
        <div className="flex items-center gap-2 mr-6 opacity-90">
             <img src="/src/assets/logo.png" alt="Logo" className="w-5 h-5" />
        </div>
        
        {/* File Menu */}
        <div className="relative">
          <button 
            className={`px-3 py-1 hover:bg-zinc-800 rounded-sm transition-colors ${menuOpen === 'file' ? 'bg-zinc-800 text-yellow-500' : ''}`}
            onClick={() => setMenuOpen(menuOpen === 'file' ? null : 'file')}
          >
            File
          </button>
          {menuOpen === 'file' && (
            <div className="absolute top-full left-0 mt-1 w-48 bg-zinc-900 border border-zinc-800 shadow-2xl py-1 z-50">
              <button className="w-full text-left px-4 py-2 hover:bg-yellow-500 hover:text-black transition-colors" onClick={handleAddFile}>New File</button>
              <div className="h-px bg-zinc-800 my-1"></div>
              <button className="w-full text-left px-4 py-2 hover:bg-yellow-500 hover:text-black transition-colors" onClick={openFile}>Open File...</button>
              <div className="h-px bg-zinc-800 my-1"></div>
              <button className="w-full text-left px-4 py-2 hover:bg-yellow-500 hover:text-black transition-colors" onClick={saveFile}>Save</button>
              <button className="w-full text-left px-4 py-2 hover:bg-yellow-500 hover:text-black transition-colors" onClick={saveFileAs}>Save As...</button>
              <div className="h-px bg-zinc-800 my-1"></div>
              <button className="w-full text-left px-4 py-2 hover:bg-yellow-500 hover:text-black transition-colors" onClick={() => window.location.reload()}>Exit</button>
            </div>
          )}
        </div>

        <button className="px-3 py-1 hover:bg-zinc-800 rounded-sm text-zinc-500 cursor-not-allowed">Edit</button>
        <button className="px-3 py-1 hover:bg-zinc-800 rounded-sm text-zinc-500 cursor-not-allowed">View</button>
        <input type="file" ref={fileInputRef} onChange={handleFileRead} className="hidden" />

        <div className="flex-1"></div>
        <div className="text-[11px] text-zinc-600 font-mono">SOLUNA DEV ENVIRONMENT</div>
      </div>

      {/* 2. MAIN WORKSPACE */}
      <div className="flex-1 flex overflow-hidden relative">
        
        {/* LEFT: File Explorer */}
        {showLeftSidebar && (
          <div className="w-60 bg-zinc-950 border-r border-zinc-900 flex flex-col">
            <div className="h-9 px-4 flex items-center text-[11px] font-bold tracking-widest text-zinc-500 bg-zinc-950">
              EXPLORER
            </div>
            <div className="flex-1 overflow-y-auto pt-2">
              <div className="px-3 py-1 flex items-center gap-1 font-bold text-[11px] text-zinc-400 mb-1">
                <IconChevronRight rotated />
                <span>WORKSPACE</span>
              </div>
              <div>
                {files.map(f => (
                  <div 
                    key={f.id} 
                    onClick={() => { setActiveFileId(f.id); triggerAnalysis(f.content); }}
                    className={`flex items-center gap-2 px-6 py-1.5 cursor-pointer text-[13px] border-l-2 ${activeFileId === f.id ? 'bg-zinc-900 text-yellow-500 border-yellow-500' : 'border-transparent text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'}`}
                  >
                    <IconFile />
                    <span className="truncate">{f.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* CENTER: Code Editor */}
        <div className="flex-1 flex flex-col min-w-0 bg-black">
            
            {/* Editor Tabs */}
            <div className="h-9 flex bg-zinc-950 overflow-x-auto scrollbar-hide border-b border-zinc-900">
              {files.map(file => (
                <div 
                  key={file.id}
                  onClick={() => { setActiveFileId(file.id); triggerAnalysis(file.content); }}
                  className={`
                    group flex items-center gap-2 px-4 min-w-[120px] max-w-[200px] cursor-pointer text-[13px] border-r border-zinc-900
                    ${activeFileId === file.id ? 'bg-black text-yellow-500 border-t-2 border-t-yellow-500' : 'bg-zinc-950 text-zinc-500 border-t-2 border-t-transparent hover:bg-zinc-900'}
                  `}
                >
                  <span className="truncate flex-1">{file.name}</span>
                  <span 
                    onClick={(e) => handleCloseFile(e, file.id)}
                    className={`w-4 h-4 flex items-center justify-center rounded-sm hover:bg-zinc-800 ${files.length > 1 ? 'opacity-0 group-hover:opacity-100' : 'hidden'}`}
                  >
                    <IconClose />
                  </span>
                </div>
              ))}
            </div>

            {/* Editor Area */}
            <div className="flex-1 relative flex">
              {/* Line Numbers */}
              <div ref={lineNumbersRef} className="w-12 bg-black text-zinc-700 text-right pr-3 pt-4 text-[13px] font-mono leading-6 select-none overflow-hidden">
                 {lines.map(l => <div key={l}>{l}</div>)}
              </div>
              {/* Text Area */}
              <textarea 
                ref={textareaRef}
                className="flex-1 bg-black text-zinc-300 p-0 pt-4 pl-2 font-mono text-[13px] leading-6 resize-none outline-none border-none whitespace-pre overflow-auto placeholder-zinc-800"
                spellCheck="false"
                placeholder="// Start coding in Soluna..."
                value={activeFile.content}
                onChange={handleCodeChange}
                onKeyDown={handleKeyDown}
                onScroll={handleScroll}
              />
            </div>
        </div>

        {/* RIGHT: Output Sidebar (Lexer/Parser) */}
        {showRightSidebar && (
          <div className="w-80 bg-zinc-950 border-l border-zinc-900 flex flex-col">
             {/* Tabs */}
             <div className="flex items-center h-9 border-b border-zinc-900">
                <button 
                  onClick={() => setActiveRightTab('lexer')}
                  className={`flex-1 h-full text-[11px] font-bold tracking-wider hover:bg-zinc-900 transition-colors ${activeRightTab === 'lexer' ? 'text-yellow-500 border-b-2 border-yellow-500 bg-zinc-900' : 'text-zinc-500 border-b-2 border-transparent'}`}
                >
                  LEXER
                </button>
                <button 
                  onClick={() => setActiveRightTab('parser')}
                  className={`flex-1 h-full text-[11px] font-bold tracking-wider hover:bg-zinc-900 transition-colors ${activeRightTab === 'parser' ? 'text-yellow-500 border-b-2 border-yellow-500 bg-zinc-900' : 'text-zinc-500 border-b-2 border-transparent'}`}
                >
                  PARSER
                </button>
             </div>

             {/* Content */}
             <div className="flex-1 overflow-auto bg-black p-0">
                
                {/* Error Banner */}
                {activeErrors.length > 0 && (
                  <div className="bg-red-900/20 border-b border-red-900/50 p-3">
                     <div className="flex items-center gap-2 text-red-500 font-bold text-xs mb-2">
                        <IconError />
                        {activeErrors.length} ERROR(S) DETECTED
                     </div>
                     {activeErrors.map((err, i) => (
                        <div key={i} className="text-[11px] text-red-400 font-mono mb-1 pl-5 border-l-2 border-red-900/50">
                           Line {err.line}: {err.message}
                        </div>
                     ))}
                  </div>
                )}

                {/* Lexer Output */}
                {activeRightTab === 'lexer' && (
                  tokens.length === 0 ? <div className="p-8 text-center text-zinc-700 text-xs">Waiting for input...</div> :
                  <table className="w-full text-left border-collapse">
                    <thead className="sticky top-0 bg-zinc-900">
                      <tr className="text-zinc-500 text-[10px] uppercase">
                         <th className="w-10 px-3 py-1 font-normal">Ln</th>
                         {/* Added Column Header */}
                         <th className="w-10 px-3 py-1 font-normal">Col</th>
                         <th className="px-3 py-1 font-normal">Type</th>
                         <th className="px-3 py-1 font-normal">Value</th>
                      </tr>
                    </thead>
                    <tbody className="font-mono text-[12px]">
                       {tokens.map((t, i) => (
                         <tr key={i} className="hover:bg-zinc-900/50 border-b border-zinc-900/30">
                           <td className="px-3 py-1 text-zinc-600">{t.line}</td>
                           {/* Added Column Data */}
                           <td className="px-3 py-1 text-zinc-600">{t.col}</td>
                           <td className="px-3 py-1 font-bold" style={{ color: getColor(t.type) }}>{t.type}</td>
                           <td className="px-3 py-1 text-zinc-400 break-all">{t.value}</td>
                         </tr>
                       ))}
                    </tbody>
                  </table>
                )}

                {/* Parser Output (Modified) */}
                {activeRightTab === 'parser' && (
                   <div className="h-full flex flex-col">
                      {lexerErrors.length > 0 ? (
                        /* BLOCKED STATE: LEXER ERRORS EXIST */
                        <div className="flex-1 flex flex-col items-center justify-center text-center p-6 opacity-80">
                            <div className="mb-3 transform scale-150"><IconError /></div>
                            <h3 className="text-red-400 font-bold text-xs uppercase tracking-wider mb-2">Lexer Errors Detected</h3>
                            <p className="text-zinc-500 text-[11px] max-w-[200px]">
                                The parser cannot build a tree while unrecognized tokens exist. <br/><br/>
                                <span className="text-zinc-400">Please fix lexical errors first.</span>
                            </p>
                        </div>
                      ) : parserErrors.length > 0 ? (
                         /* ERROR STATE: PARSER ERRORS EXIST */
                         <div className="flex-1 flex flex-col items-center justify-center text-center p-6 opacity-80">
                            <div className="mb-3 transform scale-150"><IconError /></div>
                            <h3 className="text-red-400 font-bold text-xs uppercase tracking-wider mb-2">Syntax Errors Found</h3>
                            <p className="text-zinc-500 text-[11px] max-w-[200px]">
                                Review the error list above to fix syntax issues.
                            </p>
                        </div>
                      ) : parseTree ? (
                        /* SUCCESS STATE: NO ERRORS */
                        <div className="flex-1 flex flex-col items-center justify-center text-center p-6 opacity-80 animate-in fade-in duration-500">
                           <div className="mb-4 transform scale-150"><IconCheck /></div>
                           <h3 className="text-green-400 font-bold text-xs uppercase tracking-wider mb-2">No Syntax Errors</h3>
                           <p className="text-zinc-500 text-[11px]">
                              The code is syntactically valid.
                           </p>
                        </div>
                      ) : (
                        /* EMPTY STATE */
                        <div className="flex-1 flex items-center justify-center text-zinc-800 text-xs">
                           Waiting for code...
                        </div>
                      )}
                   </div>
                )}
             </div>
          </div>
        )}

      </div>

      {/* 4. STATUS BAR */}
      <div className="h-6 bg-yellow-500 flex items-center px-3 text-black text-[11px] font-bold select-none justify-between">
         <div className="flex items-center gap-4">
            <div className="flex items-center gap-1">
               <span className={`w-2 h-2 rounded-full ${wsStatus === 'CONNECTED' ? 'bg-black animate-pulse' : 'bg-red-600'}`}></span>
               {wsStatus}
            </div>
            {errors.length > 0 && (
               <div className="flex items-center gap-1 px-2 py-0.5 bg-black/10 rounded">
                  <span>!</span> {errors.length} Error(s)
               </div>
            )}
         </div>
         
         <div className="flex items-center gap-4">
             {/* Layout Toggles */}
            <div className="flex gap-1 border-r border-black/10 pr-4 mr-1">
               <button onClick={() => setShowLeftSidebar(!showLeftSidebar)} className={`hover:bg-black/10 px-1 rounded ${!showLeftSidebar && 'opacity-50'}`}>[Sidebar]</button>
               <button onClick={() => setShowRightSidebar(!showRightSidebar)} className={`hover:bg-black/10 px-1 rounded ${!showRightSidebar && 'opacity-50'}`}>[Output]</button>
            </div>
            <span>Ln {tokens.length}</span>
            <span>Soluna 0.49</span>
         </div>
      </div>

    </div>
  );
};

export default App;