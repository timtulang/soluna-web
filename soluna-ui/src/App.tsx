import React, { useEffect, useRef, useState, useCallback } from "react";
import type { ChangeEvent } from "react";
import MonacoEditor, { type OnMount } from "@monaco-editor/react";
import type * as MonacoTypes from "monaco-editor";
import { type Token, type LexerError, type ParseNode, type WsMessage, type CodeFile, getColor } from "./types";
import { setupMonaco } from "./monacoConfig";
import { TopMenuBar, StatusBar } from "./UIComponents";
import { IconFile, IconClose, IconChevronRight, IconError, IconCheck } from "./Icons";

const App: React.FC = () => {
  const [wsStatus, setWsStatus] = useState<string>("DISCONNECTED");
  const [files, setFiles] = useState<CodeFile[]>([{ id: '1', name: 'main.sl', content: '' }]);
  const [activeFileId, setActiveFileId] = useState<string>('1');
  const [tokens, setTokens] = useState<Token[]>([]);
  const [parseTree, setParseTree] = useState<ParseNode | null>(null);
  const [errors, setErrors] = useState<LexerError[]>([]);
  const [warnings, setWarnings] = useState<{ type: string, message: string }[]>([]);
  
  const [output, setOutput] = useState<string>("");
  const [isWaitingForInput, setIsWaitingForInput] = useState<boolean>(false);
  const [inputValue, setInputValue] = useState<string>("");

  const [editingFileId, setEditingFileId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState<string>("");

  const [showLeftSidebar, setShowLeftSidebar] = useState(true);
  const [showRightSidebar, setShowRightSidebar] = useState(true);
  const [showTerminal, setShowTerminal] = useState(true);
  const [activeRightTab, setActiveRightTab] = useState<'lexer' | 'parser'>('lexer');
  const [activeTerminalTab, setActiveTerminalTab] = useState<'problems' | 'output' | 'terminal'>('problems');
  const [menuOpen, setMenuOpen] = useState<string | null>(null);

  const [leftWidth, setLeftWidth] = useState(240);
  const [rightWidth, setRightWidth] = useState(320);
  const [terminalHeight, setTerminalHeight] = useState(192);
  
  const [isResizingLeft, setIsResizingLeft] = useState(false);
  const [isResizingRight, setIsResizingRight] = useState(false);
  const [isResizingTerminal, setIsResizingTerminal] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const editorRef = useRef<MonacoTypes.editor.IStandaloneCodeEditor | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
          if (data.warnings) setWarnings(data.warnings);
          else setWarnings([]);
          
          if (data.output !== undefined) {
             setOutput(data.output);
          }
          if (data.isWaitingForInput !== undefined) {
             setIsWaitingForInput(data.isWaitingForInput);
          }
          
          if (data.parseTree) {
             setParseTree(data.parseTree);
          } else if (data.errors && data.errors.length > 0) {
             setParseTree(null);
          }
        } catch (e) { console.error(e); }
      });
      ws.addEventListener("close", () => { setWsStatus("DISCONNECTED"); setTimeout(connect, 1000); });
    }
    connect();
    return () => { wsRef.current?.close(); };
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isResizingLeft) setLeftWidth(Math.max(150, Math.min(e.clientX, 600)));
      if (isResizingRight) setRightWidth(Math.max(200, Math.min(document.body.clientWidth - e.clientX, 800)));
      if (isResizingTerminal) setTerminalHeight(Math.max(100, Math.min(document.body.clientHeight - e.clientY - 24, 600)));
    };

    const handleMouseUp = () => {
      setIsResizingLeft(false);
      setIsResizingRight(false);
      setIsResizingTerminal(false);
      document.body.style.cursor = 'default';
    };

    if (isResizingLeft || isResizingRight || isResizingTerminal) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizingLeft, isResizingRight, isResizingTerminal]);

  const startResizingLeft = () => { setIsResizingLeft(true); document.body.style.cursor = 'col-resize'; };
  const startResizingRight = () => { setIsResizingRight(true); document.body.style.cursor = 'col-resize'; };
  const startResizingTerminal = () => { setIsResizingTerminal(true); document.body.style.cursor = 'row-resize'; };

  function triggerAnalysis(code: string) {
    if (code.trim() === "") {
        setTokens([]); setErrors([]); setParseTree(null); setOutput("");
        return;
    }
    
    setOutput("");
    setActiveTerminalTab('output');
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ code }));
    }
  }

  const handleInputSubmit = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ input: inputValue }));
        setInputValue("");
        setIsWaitingForInput(false);
      }
    }
  };

  const activeFile = files.find(f => f.id === activeFileId) || files[0];

  function handleCodeChange(value: string | undefined) {
    const newContent = value ?? "";
    setFiles(prev => prev.map(f => f.id === activeFileId ? { ...f, content: newContent } : f));
  }

  const handleEditorMount: OnMount = useCallback((editor, monaco) => {
    editorRef.current = editor;
    setupMonaco(monaco);
  }, []);

  function handleAddFile() {
    const newId = Date.now().toString();
    setFiles([...files, { id: newId, name: `script_${files.length}.sl`, content: '' }]);
    setActiveFileId(newId);
  }

  function handleCloseFile(e: React.MouseEvent, id: string) {
    e.stopPropagation();
    if (files.length === 1) {
        setFiles([{...files[0], content: ''}]);
        return;
    }
    const newFiles = files.filter(f => f.id !== id);
    setFiles(newFiles);
    if (activeFileId === id) {
        setActiveFileId(newFiles[0].id);
    }
  }

  const openFile = () => { fileInputRef.current?.click(); setMenuOpen(null); };
  
  const handleFileRead = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const content = ev.target?.result as string;
      const newId = Date.now().toString();
      setFiles([...files, { id: newId, name: file.name, content }]);
      setActiveFileId(newId);
    };
    reader.readAsText(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSaveFile = () => {
    if (!activeFile) return;
    const blob = new Blob([activeFile.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = activeFile.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setMenuOpen(null);
  };

  const handleFileClick = (e: React.MouseEvent, file: CodeFile) => {
    e.stopPropagation();
    if (activeFileId === file.id) {
      setEditingFileId(file.id);
      setEditingName(file.name);
    } else {
      setActiveFileId(file.id);
      setEditingFileId(null);
    }
  };

  const commitRename = (id: string) => {
    if (editingName.trim()) {
      setFiles(prev => prev.map(f => f.id === id ? { ...f, name: editingName.trim() } : f));
    }
    setEditingFileId(null);
  };

  const handleRenameKeyDown = (e: React.KeyboardEvent, id: string) => {
    if (e.key === 'Enter') commitRename(id);
    if (e.key === 'Escape') setEditingFileId(null);
  };

  const parserErrors = errors.filter(e => e.type === 'PARSER_ERROR');
  const semanticErrors = errors.filter(e => e.type === 'SEMANTIC_ERROR');
  const lexerErrors = errors.filter(e => e.type !== 'PARSER_ERROR' && e.type !== 'SEMANTIC_ERROR');

  return (
    <div className="h-screen w-screen flex flex-col bg-black text-zinc-300 font-sans overflow-hidden select-none">
      <TopMenuBar 
        menuOpen={menuOpen} setMenuOpen={setMenuOpen} handleAddFile={handleAddFile}
        openFile={openFile} fileInputRef={fileInputRef} handleFileRead={handleFileRead}
        triggerAnalysis={triggerAnalysis} activeFileContent={activeFile.content}
        handleSaveFile={handleSaveFile}
      />

      <div className="flex-1 flex overflow-hidden relative">
        {showLeftSidebar && (
          <div className="bg-zinc-950 border-r border-zinc-900 flex flex-col shrink-0 relative rounded-none" style={{ width: leftWidth }}>
            <div className="h-9 px-4 flex items-center text-[11px] font-bold tracking-widest text-zinc-500 bg-zinc-950 shrink-0 rounded-none">EXPLORER</div>
            <div className="flex-1 overflow-y-auto pt-2">
              <div className="px-3 py-1 flex items-center gap-1 font-bold text-[11px] text-zinc-400 mb-1">
                <IconChevronRight rotated /><span>WORKSPACE</span>
              </div>
              <div>
                {files.map(f => (
                  <div key={f.id} 
                    onClick={(e) => handleFileClick(e, f)}
                    className={`flex items-center gap-2 px-6 py-1.5 cursor-pointer text-[13px] border-l-2 rounded-none ${activeFileId === f.id ? 'bg-zinc-900 text-yellow-500 border-yellow-500' : 'border-transparent text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'}`}>
                    <IconFile />
                    {editingFileId === f.id ? (
                      <input
                        autoFocus
                        value={editingName}
                        onChange={(e) => setEditingName(e.target.value)}
                        onKeyDown={(e) => handleRenameKeyDown(e, f.id)}
                        onClick={(e) => e.stopPropagation()}
                        className="flex-1 bg-zinc-800 text-zinc-200 outline-none border border-yellow-500 px-1 py-0.5 text-[12px] w-full min-w-0"
                      />
                    ) : (
                      <span className="truncate">{f.name}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
            <div className="absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-yellow-500/50 z-10" onMouseDown={startResizingLeft} />
          </div>
        )}

        <div className="flex-1 flex flex-col min-w-0 bg-black relative rounded-none">
            <div className="h-9 flex bg-zinc-950 overflow-x-auto scrollbar-hide border-b border-zinc-900 shrink-0 rounded-none">
              {files.map(file => (
                <div key={file.id} 
                  onClick={(e) => handleFileClick(e, file)}
                  className={`group flex items-center gap-2 px-4 min-w-[120px] max-w-[200px] cursor-pointer text-[13px] border-r border-zinc-900 rounded-none ${activeFileId === file.id ? 'bg-black text-yellow-500 border-t-2 border-t-yellow-500' : 'bg-zinc-950 text-zinc-500 border-t-2 border-t-transparent hover:bg-zinc-900'}`}>
                  
                  {editingFileId === file.id ? (
                    <input
                      autoFocus
                      value={editingName}
                      onChange={(e) => setEditingName(e.target.value)}
                      onKeyDown={(e) => handleRenameKeyDown(e, file.id)}
                      onClick={(e) => e.stopPropagation()}
                      className="flex-1 bg-zinc-900 text-zinc-200 outline-none border border-yellow-500 px-1 py-0.5 text-[12px] w-full min-w-0"
                    />
                  ) : (
                    <span className="truncate flex-1">{file.name}</span>
                  )}

                  <span onClick={(e) => handleCloseFile(e, file.id)} className={`w-4 h-4 flex items-center justify-center rounded-none hover:bg-zinc-800 ${files.length > 1 ? 'opacity-0 group-hover:opacity-100' : 'hidden'}`}>
                    <IconClose />
                  </span>
                </div>
              ))}
            </div>

            <div className="flex-1 relative flex overflow-hidden rounded-none">
              <MonacoEditor
                height="100%" width="100%" language="soluna"
                value={activeFile.content} onChange={handleCodeChange} onMount={handleEditorMount}
                options={{
                  fontSize: 13, fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
                  fontLigatures: true, lineHeight: 24, minimap: { enabled: false },
                  scrollBeyondLastLine: false, wordWrap: 'off', tabSize: 4,
                  insertSpaces: true, autoIndent: 'full', formatOnType: true,
                  bracketPairColorization: { enabled: true }, matchBrackets: 'always',
                  autoClosingBrackets: 'always', autoClosingQuotes: 'always',
                  suggest: { showKeywords: true, showSnippets: true, showWords: true },
                  quickSuggestions: { other: true, comments: false, strings: false },
                  parameterHints: { enabled: true }, renderLineHighlight: 'line',
                  smoothScrolling: true, cursorBlinking: 'smooth', cursorSmoothCaretAnimation: 'on',
                  padding: { top: 16, bottom: 16 }, scrollbar: { verticalScrollbarSize: 6, horizontalScrollbarSize: 6 },
                }}
              />
            </div>

            {showTerminal && (
                <div className="bg-zinc-950 border-t border-zinc-800 flex flex-col shrink-0 relative rounded-none" style={{ height: terminalHeight }}>
                    <div className="absolute top-0 left-0 w-full h-1 cursor-row-resize hover:bg-yellow-500/50 z-10" onMouseDown={startResizingTerminal} />
                    <div className="flex items-center px-4 h-9 border-b border-zinc-800 gap-6 text-[11px] font-bold text-zinc-500 select-none bg-zinc-900/50 shrink-0 rounded-none">
                        <button onClick={() => setActiveTerminalTab('problems')} className={`h-full border-b-2 flex items-center gap-2 transition-colors rounded-none ${activeTerminalTab === 'problems' ? 'text-zinc-200 border-yellow-500' : 'border-transparent hover:text-zinc-300'}`}>
                           PROBLEMS {(errors.length + (warnings?.length || 0)) > 0 && (
                               <span className={`rounded-none px-1.5 py-0.5 text-[10px] min-w-[1.5em] text-center ${errors.length > 0 ? 'bg-red-900/50 text-red-400' : 'bg-yellow-900/50 text-yellow-500'}`}>
                                   {errors.length + (warnings?.length || 0)}
                               </span>
                           )}
                        </button>
                        <button onClick={() => setActiveTerminalTab('output')} className={`h-full border-b-2 transition-colors rounded-none ${activeTerminalTab === 'output' ? 'text-zinc-200 border-yellow-500' : 'border-transparent hover:text-zinc-300'}`}>OUTPUT</button>
                        <button onClick={() => setActiveTerminalTab('terminal')} className={`h-full border-b-2 transition-colors rounded-none ${activeTerminalTab === 'terminal' ? 'text-zinc-200 border-yellow-500' : 'border-transparent hover:text-zinc-300'}`}>TERMINAL</button>
                        <div className="flex-1" />
                        <button onClick={() => setShowTerminal(false)} className="hover:text-white rounded-none"><IconClose /></button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-0 bg-zinc-950 font-mono text-[12px] rounded-none">
                        {activeTerminalTab === 'problems' && (
                            <div className="flex flex-col rounded-none py-2">
                                {errors.length === 0 && (!warnings || warnings.length === 0) ? (
                                    <div className="text-zinc-600 italic p-4 text-xs">No problems detected in workspace.</div>
                                ) : (
                                    <>
                                        {errors.map((err, i) => {
                                            let typeLabel = "LEXICAL";
                                            if (err.type === 'PARSER_ERROR') typeLabel = "SYNTAX";
                                            else if (err.type === 'SEMANTIC_ERROR') typeLabel = "SEMANTIC";

                                            return (
                                            <div key={`err-${i}`} className="group flex items-start gap-3 py-2 px-4 hover:bg-zinc-900 cursor-pointer border-l-2 border-transparent hover:border-red-500 rounded-none">
                                                <div className="mt-1 shrink-0"><IconError /></div>
                                                <div className="flex-1 min-w-0 flex flex-col gap-1">
                                                    <div className="flex items-start gap-2">
                                                        <span className="shrink-0 mt-0.5 bg-red-950/80 text-red-400 border border-red-900/50 px-1 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded-sm leading-none">
                                                            {typeLabel}
                                                        </span>
                                                        <span className="text-zinc-300 break-words leading-relaxed">{err.message}</span>
                                                    </div>
                                                    <div className="text-zinc-600 text-[10px]">{activeFile.name}</div>
                                                </div>
                                                <div className="text-zinc-500 text-[11px] shrink-0 group-hover:text-zinc-300 ml-4 mt-0.5">[{err.line}, {err.col}]</div>
                                            </div>
                                        )})}
                                        {warnings && warnings.map((warn, i) => (
                                            <div key={`warn-${i}`} className="group flex items-start gap-3 py-2 px-4 hover:bg-zinc-900 cursor-pointer border-l-2 border-transparent hover:border-yellow-500 rounded-none">
                                                <div className="mt-1 shrink-0 text-yellow-500 font-bold text-[14px] leading-none">⚠</div>
                                                <div className="flex-1 min-w-0 flex flex-col gap-1">
                                                    <div className="flex items-start gap-2">
                                                        <span className="shrink-0 mt-0.5 bg-yellow-950/80 text-yellow-500 border border-yellow-900/50 px-1 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded-sm leading-none">
                                                            WARNING
                                                        </span>
                                                        <span className="text-zinc-300 break-words leading-relaxed">{warn.message}</span>
                                                    </div>
                                                    <div className="text-zinc-600 text-[10px]">{activeFile.name}</div>
                                                </div>
                                            </div>
                                        ))}
                                    </>
                                )}
                            </div>
                        )}
                        {activeTerminalTab === 'output' && (
                            <div className="p-4 flex flex-col h-full font-mono text-xs">
                                <div className="text-zinc-300 whitespace-pre-wrap">
                                    {output ? output : <span className="text-zinc-600 italic">Program output will appear here...</span>}
                                </div>
                                {isWaitingForInput && (
                                    <div className="flex items-center mt-1">
                                        <span className="text-yellow-500 mr-2 font-bold">{">"}</span>
                                        <input
                                            autoFocus
                                            type="text"
                                            value={inputValue}
                                            onChange={(e) => setInputValue(e.target.value)}
                                            onKeyDown={handleInputSubmit}
                                            className="flex-1 bg-transparent border-none outline-none text-zinc-300 p-0 m-0 focus:ring-0"
                                            placeholder="Type input and press Enter..."
                                        />
                                    </div>
                                )}
                            </div>
                        )}
                        {activeTerminalTab === 'terminal' && <div className="text-zinc-600 italic p-4 text-xs">Soluna REPL ready...</div>}
                    </div>
                </div>
            )}
        </div>

        {showRightSidebar && (
          <div className="bg-zinc-950 border-l border-zinc-900 flex flex-col shrink-0 relative rounded-none" style={{ width: rightWidth }}>
             <div className="absolute top-0 left-0 w-1 h-full cursor-col-resize hover:bg-yellow-500/50 z-10" onMouseDown={startResizingRight} />
             <div className="flex items-center h-9 border-b border-zinc-900 shrink-0 rounded-none">
                <button onClick={() => setActiveRightTab('lexer')} className={`flex-1 h-full text-[11px] font-bold tracking-wider hover:bg-zinc-900 transition-colors rounded-none ${activeRightTab === 'lexer' ? 'text-yellow-500 border-b-2 border-yellow-500 bg-zinc-900' : 'text-zinc-500 border-b-2 border-transparent'}`}>LEXER</button>
                <button onClick={() => setActiveRightTab('parser')} className={`flex-1 h-full text-[11px] font-bold tracking-wider hover:bg-zinc-900 transition-colors rounded-none ${activeRightTab === 'parser' ? 'text-yellow-500 border-b-2 border-yellow-500 bg-zinc-900' : 'text-zinc-500 border-b-2 border-transparent'}`}>PARSER</button>
             </div>
             <div className="flex-1 overflow-auto bg-black p-0 rounded-none">
                {activeRightTab === 'lexer' && (
                  tokens.length === 0 ? <div className="p-8 text-center text-zinc-700 text-xs">Waiting for input...</div> :
                  <table className="w-full text-left border-collapse">
                    <thead className="sticky top-0 bg-zinc-900">
                      <tr className="text-zinc-500 text-[10px] uppercase">
                         <th className="w-10 px-3 py-1 font-normal">Ln</th>
                         <th className="w-10 px-3 py-1 font-normal">Col</th>
                         <th className="px-3 py-1 font-normal">Type</th>
                         <th className="px-3 py-1 font-normal">Value</th>
                      </tr>
                    </thead>
                    <tbody className="font-mono text-[12px]">
                       {tokens.map((t, i) => (
                         <tr key={i} className="hover:bg-zinc-900/50 border-b border-zinc-900/30">
                           <td className="px-3 py-1 text-zinc-600">{t.line}</td>
                           <td className="px-3 py-1 text-zinc-600">{t.col}</td>
                           <td className="px-3 py-1 font-bold" style={{ color: getColor(t.type) }}>{t.type}</td>
                           <td className="px-3 py-1 text-zinc-400 break-all">{t.value}</td>
                         </tr>
                       ))}
                    </tbody>
                  </table>
                )}
                {activeRightTab === 'parser' && (
                   <div className="h-full flex flex-col rounded-none">
                      {lexerErrors.length > 0 ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-center p-6 opacity-80">
                            <div className="mb-3 transform scale-150"><IconError /></div>
                            <h3 className="text-red-400 font-bold text-xs uppercase tracking-wider mb-2">Lexer Errors Detected</h3>
                            <p className="text-zinc-500 text-[11px] max-w-[200px]">Check Problems tab to fix lexer errors before parsing.</p>
                        </div>
                      ) : parserErrors.length > 0 ? (
                         <div className="flex-1 flex flex-col items-center justify-center text-center p-6 opacity-80">
                            <div className="mb-3 transform scale-150"><IconError /></div>
                            <h3 className="text-red-400 font-bold text-xs uppercase tracking-wider mb-2">Syntax Errors Detected</h3>
                            <p className="text-zinc-500 text-[11px] max-w-[200px]">Check Problems tab to view syntax errors.</p>
                        </div>
                      ) : parseTree ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-center p-6 opacity-80 animate-in fade-in duration-500">
                           <div className="mb-4 transform scale-150"><IconCheck /></div>
                           <h3 className="text-green-400 font-bold text-xs uppercase tracking-wider mb-2">No Syntax Errors</h3>
                           <p className="text-zinc-500 text-[11px]">Valid Soluna syntax. <br/><span className="opacity-50">(Check Terminal for Logic Errors)</span></p>
                        </div>
                      ) : (
                        <div className="flex-1 flex items-center justify-center text-zinc-800 text-xs">Waiting for code...</div>
                      )}
                   </div>
                )}
             </div>
          </div>
        )}
      </div>

      <StatusBar 
         wsStatus={wsStatus} errorsLength={errors.length}
         showLeftSidebar={showLeftSidebar} setShowLeftSidebar={setShowLeftSidebar}
         showTerminal={showTerminal} setShowTerminal={setShowTerminal}
         showRightSidebar={showRightSidebar} setShowRightSidebar={setShowRightSidebar}
         tokensLength={tokens.length}
      />
    </div>
  );
};

export default App;