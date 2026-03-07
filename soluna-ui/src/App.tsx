import React, { useEffect, useRef, useState, useCallback } from "react";
import type { ChangeEvent } from "react";
import MonacoEditor, { type OnMount } from "@monaco-editor/react";
import type * as MonacoTypes from "monaco-editor";

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
  warnings?: { type: string, message: string }[]; 
  parseTree?: ParseNode;
  output?: string;         // <-- NEW: Terminal output from Python execution
  transpiledCode?: string; // <-- NEW: The generated Python code
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
const IconPlay = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
    <path d="M4 2v12l10-6z"/>
  </svg>
);

// --- Main App Component ---

const App: React.FC = () => {
  // --- Data State ---
  const [wsStatus, setWsStatus] = useState<string>("DISCONNECTED");
  const [files, setFiles] = useState<CodeFile[]>([{ id: '1', name: 'main.sl', content: '' }]);
  const [activeFileId, setActiveFileId] = useState<string>('1');
  const [tokens, setTokens] = useState<Token[]>([]);
  const [parseTree, setParseTree] = useState<ParseNode | null>(null);
  const [errors, setErrors] = useState<LexerError[]>([]);
  const [warnings, setWarnings] = useState<{ type: string, message: string }[]>([]);

  // --- UI State ---
  const [showLeftSidebar, setShowLeftSidebar] = useState(true);
  const [showRightSidebar, setShowRightSidebar] = useState(true);
  const [showTerminal, setShowTerminal] = useState(true);
  const [activeRightTab, setActiveRightTab] = useState<'lexer' | 'parser'>('lexer');
  const [activeTerminalTab, setActiveTerminalTab] = useState<'problems' | 'output' | 'terminal'>('problems');
  const [menuOpen, setMenuOpen] = useState<string | null>(null);
  
  // --- Compilation State ---
  const [autoCompile, setAutoCompile] = useState(true);

  // --- Resizing State ---
  const [leftWidth, setLeftWidth] = useState(240);
  const [rightWidth, setRightWidth] = useState(320);
  const [terminalHeight, setTerminalHeight] = useState(192);
  
  const [isResizingLeft, setIsResizingLeft] = useState(false);
  const [isResizingRight, setIsResizingRight] = useState(false);
  const [isResizingTerminal, setIsResizingTerminal] = useState(false);

  // --- Refs ---
  const wsRef = useRef<WebSocket | null>(null);
  const sendTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const editorRef = useRef<MonacoTypes.editor.IStandaloneCodeEditor | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

    // Add these near your other useState declarations
  const [consoleOutput, setConsoleOutput] = useState<string>("");
  const [transpiledCode, setTranspiledCode] = useState<string>("");

  // --- WebSocket Setup ---
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

          if (data.warnings) {
              setWarnings(data.warnings);
          } else {
              setWarnings([]);
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

  // --- Resizing Logic ---
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isResizingLeft) {
        const newWidth = Math.max(150, Math.min(e.clientX, 600)); 
        setLeftWidth(newWidth);
      }
      if (isResizingRight) {
        const newWidth = Math.max(200, Math.min(document.body.clientWidth - e.clientX, 800));
        setRightWidth(newWidth);
      }
      if (isResizingTerminal) {
        const newHeight = Math.max(100, Math.min(document.body.clientHeight - e.clientY - 24, 600)); 
        setTerminalHeight(newHeight);
      }
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

  // --- Helper Functions ---
  function triggerAnalysis(code: string, force: boolean = false) {
    if (!autoCompile && !force) return;

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

  // Trigger analysis automatically if the user flips the toggle back on
  useEffect(() => {
    if (autoCompile) {
      triggerAnalysis(files.find(f => f.id === activeFileId)?.content || '', true);
    }
  }, [autoCompile]);

  const activeFile = files.find(f => f.id === activeFileId) || files[0];

  function handleCodeChange(value: string | undefined) {
    const newContent = value ?? "";
    setFiles(prev => prev.map(f => f.id === activeFileId ? { ...f, content: newContent } : f));
    triggerAnalysis(newContent);
  }

  const handleEditorMount: OnMount = useCallback((editor, monaco) => {
    editorRef.current = editor;

    // ── Soluna keyword sets (derived from grammar.py) ──────────────────────
    // Data types
    const TYPES    = ['kai', 'flux', 'selene', 'blaze', 'lani', 'let'];
    // Control flow
    const CONTROL  = ['sol', 'soluna', 'luna', 'orbit', 'cos', 'phase', 'wax', 'wane', 'warp', 'mos'];
    // Declarations / modifiers
    const DECL     = ['zeta', 'void', 'local', 'hubble'];
    // Functions & I/O
    const FUNCS    = ['zara', 'lumina', 'nova', 'lumen'];
    // Booleans & logical operators
    const LITERALS = ['iris', 'sage'];
    const LOGICAL  = ['not', 'and', 'or'];
    // Misc
    const MISC     = ['leo', 'label'];

    const ALL_KEYWORDS = [...TYPES, ...CONTROL, ...DECL, ...FUNCS, ...LITERALS, ...LOGICAL, ...MISC];

    // Register Soluna language
    if (!monaco.languages.getLanguages().find((l: MonacoTypes.languages.ILanguageExtensionPoint) => l.id === 'soluna')) {
      monaco.languages.register({ id: 'soluna' });

      // ── Tokenizer ─────────────────────────────────────────────────────────
      const kwRegex = new RegExp(
        `\\b(${ALL_KEYWORDS.join('|')})\\b`
      );
      monaco.languages.setMonarchTokensProvider('soluna', {
        keywords: ALL_KEYWORDS,
        tokenizer: {
          root: [
            // Comments
            [/\/\/.*$/, 'comment'],
            [/\/\*/, 'comment', '@block_comment'],
            // Strings
            [/"([^"\\]|\\.)*$/, 'string.invalid'],
            [/"/, 'string', '@string_double'],
            // Chars
            [/'[^\\']'/, 'string.char'],
            // Keywords (must come before identifier rule)
            [kwRegex, 'keyword'],
            // String-length operator  #identifier
            [/#[a-zA-Z_]\w*/, 'operator.length'],
            // Identifiers
            [/[a-zA-Z_]\w*/, 'identifier'],
            // Numbers
            [/\d+\.\d*([eE][+-]?\d+)?/, 'number.float'],
            [/\d+/, 'number'],
            // Multi-char operators first
            [/\/\/|&&|\|\||!=|==|>=|<=|\+\+|--|[+\-]=|[*\/]=|%=|\.\.|[+\-*\/%^<>=!]/, 'operator'],
            // Brackets
            [/[{}()\[\]]/, 'delimiter.bracket'],
            // Delimiters
            [/[;,.]/, 'delimiter'],
          ],
          block_comment: [
            [/[^/*]+/, 'comment'],
            [/\*\//, 'comment', '@pop'],
            [/[/*]/, 'comment'],
          ],
          string_double: [
            [/[^\\"]+/, 'string'],
            [/\\./, 'string.escape'],
            [/"/, 'string', '@pop'],
          ],
        },
      });

      // ── Theme ─────────────────────────────────────────────────────────────
      monaco.editor.defineTheme('soluna-dark', {
        base: 'vs-dark',
        inherit: true,
        rules: [
          // Control flow keywords — purple
          { token: 'keyword',           foreground: 'c084fc', fontStyle: 'bold' },
          // Identifiers — blue
          { token: 'identifier',        foreground: '60a5fa' },
          // Numbers — green
          { token: 'number',            foreground: '4ade80' },
          { token: 'number.float',      foreground: '4ade80' },
          // Strings — green
          { token: 'string',            foreground: '4ade80' },
          { token: 'string.char',       foreground: '4ade80' },
          { token: 'string.escape',     foreground: 'facc15' },
          { token: 'string.invalid',    foreground: 'f87171' },
          // Comments — muted zinc
          { token: 'comment',           foreground: '52525b', fontStyle: 'italic' },
          // Brackets — yellow
          { token: 'delimiter.bracket', foreground: 'facc15' },
          // Operators — zinc
          { token: 'operator',          foreground: 'a1a1aa' },
          { token: 'operator.length',   foreground: 'facc15' },
          // Delimiters
          { token: 'delimiter',         foreground: 'a1a1aa' },
        ],
        colors: {
          'editor.background':                    '#000000',
          'editor.foreground':                    '#d4d4d8',
          'editorLineNumber.foreground':           '#3f3f46',
          'editorLineNumber.activeForeground':     '#facc15',
          'editor.lineHighlightBackground':        '#18181b',
          'editorCursor.foreground':               '#facc15',
          'editor.selectionBackground':            '#facc1540',
          'editorIndentGuide.background':          '#27272a',
          'editorWidget.background':               '#09090b',
          'editorSuggestWidget.background':        '#09090b',
          'editorSuggestWidget.border':            '#3f3f46',
          'editorSuggestWidget.selectedBackground':'#facc1520',
          'editorSuggestWidget.highlightForeground':'#facc15',
          'list.hoverBackground':                  '#18181b',
          'list.activeSelectionBackground':        '#facc1520',
          'list.activeSelectionForeground':        '#facc15',
        },
      });
      monaco.editor.setTheme('soluna-dark');

      // ── Completion Provider ───────────────────────────────────────────────
      monaco.languages.registerCompletionItemProvider('soluna', {
        provideCompletionItems: (model: MonacoTypes.editor.ITextModel, position: MonacoTypes.Position) => {
          const word = model.getWordUntilPosition(position);
          const range: MonacoTypes.IRange = {
            startLineNumber: position.lineNumber,
            endLineNumber:   position.lineNumber,
            startColumn:     word.startColumn,
            endColumn:       word.endColumn,
          };
          const KW  = monaco.languages.CompletionItemKind.Keyword;
          const SN  = monaco.languages.CompletionItemKind.Snippet;
          const ITR = monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet;

          const suggestions: MonacoTypes.languages.CompletionItem[] = [

            // ── Type declarations ──────────────────────────────────────────
            { label: 'kai',    kind: KW, insertText: 'kai ${1:name};',             insertTextRules: ITR, detail: 'int',    documentation: 'Integer variable declaration', range },
            { label: 'flux',   kind: KW, insertText: 'flux ${1:name};',            insertTextRules: ITR, detail: 'float',  documentation: 'Float variable declaration',   range },
            { label: 'selene', kind: KW, insertText: 'selene ${1:name};',          insertTextRules: ITR, detail: 'double', documentation: 'Double variable declaration',  range },
            { label: 'blaze',  kind: KW, insertText: 'blaze ${1:name};',           insertTextRules: ITR, detail: 'char',   documentation: 'Char variable declaration',    range },
            { label: 'lani',   kind: KW, insertText: 'lani ${1:name};',            insertTextRules: ITR, detail: 'bool',   documentation: 'Bool variable declaration',    range },
            { label: 'let',    kind: KW, insertText: 'let ${1:name};',             insertTextRules: ITR, detail: 'string', documentation: 'String variable declaration',  range },
            { label: 'void',   kind: KW, insertText: 'void',                       insertTextRules: ITR, detail: 'void return type', range },
            { label: 'zeta',   kind: KW, insertText: 'zeta',                       insertTextRules: ITR, detail: 'const modifier', documentation: 'Makes variable constant', range },
            { label: 'local',  kind: KW, insertText: 'local',                      insertTextRules: ITR, detail: 'local scope',    documentation: 'Local variable declaration', range },

            // ── Snippets: var declaration with init ────────────────────────
            { label: 'kai =',    kind: SN, insertText: 'kai ${1:name} = ${2:0};',       insertTextRules: ITR, detail: 'int with value',    range },
            { label: 'flux =',   kind: SN, insertText: 'flux ${1:name} = ${2:0.0};',    insertTextRules: ITR, detail: 'float with value',  range },
            { label: 'selene =', kind: SN, insertText: 'selene ${1:name} = ${2:0.0};',  insertTextRules: ITR, detail: 'double with value', range },
            { label: 'blaze =',  kind: SN, insertText: 'blaze ${1:name} = \'${2:a}\';', insertTextRules: ITR, detail: 'char with value',   range },
            { label: 'lani =',   kind: SN, insertText: 'lani ${1:name} = ${2:iris};',   insertTextRules: ITR, detail: 'bool with value',   range },
            { label: 'let =',    kind: SN, insertText: 'let ${1:name} = "${2:value}";', insertTextRules: ITR, detail: 'string with value', range },
            { label: 'zeta kai', kind: SN, insertText: 'zeta kai ${1:name} = ${2:0};',  insertTextRules: ITR, detail: 'const int',         range },

            // ── Hubble (tables/arrays) ─────────────────────────────────────
            { label: 'hubble', kind: KW, insertText: 'hubble',                           insertTextRules: ITR, detail: 'table/array keyword', range },
            { label: 'hubble []', kind: SN,
              insertText: 'hubble ${1:kai} ${2:name} = { ${3:elements} };',
              insertTextRules: ITR, detail: 'Table declaration', documentation: 'Declare a Hubble table', range },

            // ── Function definition ────────────────────────────────────────
            { label: 'func', kind: SN,
              insertText: '${1:void} ${2:name}(${3:params})\n\t${4}\nmos',
              insertTextRules: ITR, detail: 'Function definition', documentation: 'func_def: return_type name(params) ... mos', range },
            { label: 'kai func', kind: SN,
              insertText: 'kai ${1:name}(${2:params})\n\t${3}\n\tzara ${4:0};\nmos',
              insertTextRules: ITR, detail: 'int-returning function', range },
            { label: 'void func', kind: SN,
              insertText: 'void ${1:name}(${2:params})\n\t${3}\nmos',
              insertTextRules: ITR, detail: 'void function', range },
            { label: 'zara', kind: KW,
              insertText: 'zara ${1:value};',
              insertTextRules: ITR, detail: 'return statement', documentation: 'Return a value from a function', range },

            // ── Conditionals ───────────────────────────────────────────────
            { label: 'sol', kind: SN,
              insertText: 'sol ${1:condition}\n\t${2}\nmos',
              insertTextRules: ITR, detail: 'if statement', documentation: 'sol condition ... mos', range },
            { label: 'sol soluna luna', kind: SN,
              insertText: 'sol ${1:condition}\n\t${2}\nmos\nsoluna ${3:condition}\n\t${4}\nmos\nluna\n\t${5}\nmos',
              insertTextRules: ITR, detail: 'if / else if / else', range },
            { label: 'soluna', kind: SN,
              insertText: 'soluna ${1:condition}\n\t${2}\nmos',
              insertTextRules: ITR, detail: 'else-if branch', documentation: 'soluna condition ... mos', range },
            { label: 'luna', kind: SN,
              insertText: 'luna\n\t${1}\nmos',
              insertTextRules: ITR, detail: 'else branch', documentation: 'luna ... mos', range },

            // ── Loops ──────────────────────────────────────────────────────
            { label: 'orbit', kind: SN,
              insertText: 'orbit ${1:condition} cos\n\t${2}\nmos',
              insertTextRules: ITR, detail: 'while loop', documentation: 'orbit condition cos ... mos', range },
            { label: 'phase', kind: SN,
              insertText: 'phase kai ${1:i} = ${2:0}, ${3:limit}, ${4:1} cos\n\t${5}\nmos',
              insertTextRules: ITR, detail: 'for loop', documentation: 'phase start, limit, step cos ... mos', range },
            { label: 'wax wane', kind: SN,
              insertText: 'wax\n\t${1}\nwane ${2:condition}',
              insertTextRules: ITR, detail: 'repeat-until loop', documentation: 'wax ... wane condition', range },
            { label: 'warp', kind: KW,
              insertText: 'warp;',
              insertTextRules: ITR, detail: 'break statement', range },
            { label: 'mos', kind: KW,
              insertText: 'mos',
              insertTextRules: ITR, detail: 'end block', documentation: 'Closes a function, if, or loop block', range },
            { label: 'cos', kind: KW,
              insertText: 'cos',
              insertTextRules: ITR, detail: 'open loop body', documentation: 'Separates loop condition from body', range },

            // ── I/O ────────────────────────────────────────────────────────
            { label: 'nova', kind: SN,
              insertText: 'nova(${1:expression});',
              insertTextRules: ITR, detail: 'print (no newline)', documentation: 'nova(expr);', range },
            { label: 'lumen', kind: SN,
              insertText: 'lumen(${1:expression});',
              insertTextRules: ITR, detail: 'println (with newline)', documentation: 'lumen(expr);', range },
            { label: 'lumina', kind: SN,
              insertText: 'lumina()',
              insertTextRules: ITR, detail: 'input function', documentation: 'Reads user input', range },

            // ── Boolean literals ───────────────────────────────────────────
            { label: 'iris', kind: KW, insertText: 'iris', insertTextRules: ITR, detail: 'true',  range },
            { label: 'sage', kind: KW, insertText: 'sage', insertTextRules: ITR, detail: 'false', range },

            // ── Logical operators ──────────────────────────────────────────
            { label: 'and',  kind: KW, insertText: 'and',  insertTextRules: ITR, detail: 'logical AND', range },
            { label: 'or',   kind: KW, insertText: 'or',   insertTextRules: ITR, detail: 'logical OR',  range },
            { label: 'not',  kind: KW, insertText: 'not',  insertTextRules: ITR, detail: 'logical NOT', range },

            // ── Labels / Goto ──────────────────────────────────────────────
            { label: 'label', kind: KW, insertText: 'label ${1:name};', insertTextRules: ITR, detail: 'label declaration', range },
            { label: 'leo',   kind: SN, insertText: 'leo label ${1:name};', insertTextRules: ITR, detail: 'goto label', range },
          ];

          return { suggestions };
        },
      });
    } else {
      monaco.editor.setTheme('soluna-dark');
    }
  }, []);

  function handleAddFile() {
    const newId = Date.now().toString();
    setFiles([...files, { id: newId, name: `script_${files.length}.sl`, content: '' }]);
    setActiveFileId(newId);
    triggerAnalysis('', true);
  }

  function handleCloseFile(e: React.MouseEvent, id: string) {
    e.stopPropagation();
    if (files.length === 1) {
        setFiles([{...files[0], content: ''}]);
        triggerAnalysis('', true);
        return;
    }
    const newFiles = files.filter(f => f.id !== id);
    setFiles(newFiles);
    if (activeFileId === id) {
        setActiveFileId(newFiles[0].id);
        triggerAnalysis(newFiles[0].content, true);
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
      triggerAnalysis(content, true);
    };
    reader.readAsText(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };


  const parserErrors = errors.filter(e => e.type === 'PARSER_ERROR');
  const semanticErrors = errors.filter(e => e.type === 'SEMANTIC_ERROR');
  const lexerErrors = errors.filter(e => e.type !== 'PARSER_ERROR' && e.type !== 'SEMANTIC_ERROR');
  const sidebarErrors = activeRightTab === 'lexer' ? lexerErrors : parserErrors;

  return (
    <div className="h-screen w-screen flex flex-col bg-black text-zinc-300 font-sans overflow-hidden select-none">
      
      {/* 1. TOP MENU BAR */}
      <div className="h-9 bg-zinc-950 flex items-center px-3 text-[13px] border-b border-zinc-900 z-50 shrink-0">
        <div className="flex items-center gap-2 mr-6 opacity-90">
             <img src="/src/assets/logo.png" alt="Logo" className="w-5 h-5" />
        </div>
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
              <button className="w-full text-left px-4 py-2 hover:bg-yellow-500 hover:text-black transition-colors" onClick={() => window.location.reload()}>Exit</button>
            </div>
          )}
        </div>

        {/* --- Compilation Controls --- */}
        <div className="flex items-center gap-4 ml-6">
          <button 
            onClick={() => triggerAnalysis(activeFile.content, true)}
            className="flex items-center gap-1.5 px-3 py-1 bg-yellow-500 text-black hover:bg-yellow-400 font-bold rounded-sm text-[11px] uppercase tracking-wider transition-colors shadow-sm"
            title="Run Compiler Pipeline"
          >
            <IconPlay /> Run
          </button>
          
          <label className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-zinc-400 cursor-pointer hover:text-zinc-200 transition-colors">
            <input 
              type="checkbox" 
              checked={autoCompile} 
              onChange={(e) => setAutoCompile(e.target.checked)}
              className="accent-yellow-500 cursor-pointer"
            />
            Auto-Compile
          </label>
        </div>

        <input type="file" ref={fileInputRef} onChange={handleFileRead} className="hidden" />
        <div className="flex-1"></div>
        <div className="text-[11px] text-zinc-600 font-mono">SOLUNA DEV ENVIRONMENT</div>
      </div>

      {/* 2. MAIN WORKSPACE */}
      <div className="flex-1 flex overflow-hidden relative">
        
        {/* LEFT SIDEBAR */}
        {showLeftSidebar && (
          <div 
            className="bg-zinc-950 border-r border-zinc-900 flex flex-col shrink-0 relative"
            style={{ width: leftWidth }}
          >
            <div className="h-9 px-4 flex items-center text-[11px] font-bold tracking-widest text-zinc-500 bg-zinc-950 shrink-0">
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
                    onClick={() => { setActiveFileId(f.id); triggerAnalysis(f.content, true); }}
                    className={`flex items-center gap-2 px-6 py-1.5 cursor-pointer text-[13px] border-l-2 ${activeFileId === f.id ? 'bg-zinc-900 text-yellow-500 border-yellow-500' : 'border-transparent text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'}`}
                  >
                    <IconFile />
                    <span className="truncate">{f.name}</span>
                  </div>
                ))}
              </div>
            </div>
            <div 
                className="absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-yellow-500/50 z-10"
                onMouseDown={startResizingLeft}
            />
          </div>
        )}

        {/* CENTER: Code Editor & Terminal */}
        <div className="flex-1 flex flex-col min-w-0 bg-black relative">
            
            {/* Editor Tabs */}
            <div className="h-9 flex bg-zinc-950 overflow-x-auto scrollbar-hide border-b border-zinc-900 shrink-0">
              {files.map(file => (
                <div 
                    key={file.id}
                  onClick={() => { 
                    setActiveFileId(file.id); 
                    triggerAnalysis(file.content, true);
                  }}
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

            {/* Monaco Editor Area */}
            <div className="flex-1 relative flex overflow-hidden">
              <MonacoEditor
                height="100%"
                width="100%"
                language="soluna"
                value={activeFile.content}
                onChange={handleCodeChange}
                onMount={handleEditorMount}
                options={{
                  fontSize: 13,
                  fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
                  fontLigatures: true,
                  lineHeight: 24,
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  wordWrap: 'off',
                  tabSize: 4,
                  insertSpaces: true,
                  autoIndent: 'full',
                  formatOnType: true,
                  bracketPairColorization: { enabled: true },
                  matchBrackets: 'always',
                  autoClosingBrackets: 'always',
                  autoClosingQuotes: 'always',
                  suggest: {
                    showKeywords: true,
                    showSnippets: true,
                    showWords: true,
                  },
                  quickSuggestions: { other: true, comments: false, strings: false },
                  parameterHints: { enabled: true },
                  renderLineHighlight: 'line',
                  smoothScrolling: true,
                  cursorBlinking: 'smooth',
                  cursorSmoothCaretAnimation: 'on',
                  padding: { top: 16, bottom: 16 },
                  scrollbar: {
                    verticalScrollbarSize: 6,
                    horizontalScrollbarSize: 6,
                  },
                }}
              />
            </div>

            {/* BOTTOM TERMINAL PANEL */}
            {showTerminal && (
                <div 
                    className="bg-zinc-950 border-t border-zinc-800 flex flex-col shrink-0 relative"
                    style={{ height: terminalHeight }}
                >
                    <div 
                        className="absolute top-0 left-0 w-full h-1 cursor-row-resize hover:bg-yellow-500/50 z-10"
                        onMouseDown={startResizingTerminal}
                    />

                    {/* Terminal Header */}
                    <div className="flex items-center px-4 h-9 border-b border-zinc-800 gap-6 text-[11px] font-bold text-zinc-500 select-none bg-zinc-900/50 shrink-0">
                        <button 
                           onClick={() => setActiveTerminalTab('problems')}
                           className={`h-full border-b-2 flex items-center gap-2 transition-colors ${activeTerminalTab === 'problems' ? 'text-zinc-200 border-yellow-500' : 'border-transparent hover:text-zinc-300'}`}
                        >
                           PROBLEMS 
                           {(semanticErrors.length + (warnings?.length || 0)) > 0 && (
                               <span className={`rounded-full px-1.5 py-0.5 text-[10px] min-w-[1.5em] text-center ${semanticErrors.length > 0 ? 'bg-red-900/50 text-red-400' : 'bg-yellow-900/50 text-yellow-500'}`}>
                                   {semanticErrors.length + (warnings?.length || 0)}
                               </span>
                           )}
                        </button>
                        <button 
                           onClick={() => setActiveTerminalTab('output')}
                           className={`h-full border-b-2 transition-colors ${activeTerminalTab === 'output' ? 'text-zinc-200 border-yellow-500' : 'border-transparent hover:text-zinc-300'}`}
                        >
                           OUTPUT
                        </button>
                        <button 
                           onClick={() => setActiveTerminalTab('terminal')}
                           className={`h-full border-b-2 transition-colors ${activeTerminalTab === 'terminal' ? 'text-zinc-200 border-yellow-500' : 'border-transparent hover:text-zinc-300'}`}
                        >
                           TERMINAL
                        </button>
                        
                        <div className="flex-1" />
                        <button onClick={() => setShowTerminal(false)} className="hover:text-white"><IconClose /></button>
                    </div>

                    {/* Terminal Content */}
                    <div className="flex-1 overflow-y-auto p-0 bg-zinc-950 font-mono text-[12px]">
                        {activeTerminalTab === 'problems' && (
                            <div className="flex flex-col">
                                {semanticErrors.length === 0 && (!warnings || warnings.length === 0) ? (
                                    <div className="text-zinc-600 italic p-4 text-xs">No problems detected in workspace.</div>
                                ) : (
                                    <>
                                        {/* Render Errors */}
                                        {semanticErrors.map((err, i) => (
                                            <div key={`err-${i}`} className="group flex items-start gap-2 p-1 px-4 hover:bg-zinc-900 cursor-pointer border-l-2 border-transparent hover:border-red-500">
                                                <div className="mt-0.5"><IconError /></div>
                                                <div className="flex-1">
                                                    <div className="text-zinc-300">{err.message}</div>
                                                    <div className="text-zinc-600 text-[10px]">{activeFile.name}</div>
                                                </div>
                                                <div className="text-zinc-500 text-[11px] group-hover:text-zinc-300">[{err.line}, {err.col}]</div>
                                            </div>
                                        ))}

                                        {/* Render Warnings */}
                                        {warnings && warnings.map((warn, i) => (
                                            <div key={`warn-${i}`} className="group flex items-start gap-2 p-1 px-4 hover:bg-zinc-900 cursor-pointer border-l-2 border-transparent hover:border-yellow-500">
                                                <div className="mt-0.5 text-yellow-500 font-bold text-[14px] leading-none">⚠</div>
                                                <div className="flex-1">
                                                    <div className="text-zinc-300">{warn.message}</div>
                                                    <div className="text-zinc-600 text-[10px]">{activeFile.name}</div>
                                                </div>
                                            </div>
                                        ))}
                                    </>
                                )}
                            </div>
                        )}
                        {activeTerminalTab === 'output' && (
                             <div className="text-zinc-600 italic p-4 text-xs">Program output will appear here...</div>
                        )}
                         {activeTerminalTab === 'terminal' && (
                             <div className="text-zinc-600 italic p-4 text-xs">Soluna REPL ready...</div>
                        )}
                    </div>
                </div>
            )}
        </div>

        {/* RIGHT SIDEBAR (Lexer/Parser Output) */}
        {showRightSidebar && (
          <div 
            className="bg-zinc-950 border-l border-zinc-900 flex flex-col shrink-0 relative"
            style={{ width: rightWidth }}
          >
             <div 
                className="absolute top-0 left-0 w-1 h-full cursor-col-resize hover:bg-yellow-500/50 z-10"
                onMouseDown={startResizingRight}
            />

             {/* Tabs */}
             <div className="flex items-center h-9 border-b border-zinc-900 shrink-0">
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
                {sidebarErrors.length > 0 && (
                  <div className="bg-red-900/20 border-b border-red-900/50 p-3">
                     <div className="flex items-center gap-2 text-red-500 font-bold text-xs mb-2">
                        <IconError />
                        {sidebarErrors.length} {activeRightTab === 'lexer' ? 'LEXER' : 'SYNTAX'} ERROR(S)
                     </div>
                     {sidebarErrors.map((err, i) => (
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

                {/* Parser Output */}
                {activeRightTab === 'parser' && (
                   <div className="h-full flex flex-col">
                      {lexerErrors.length > 0 ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-center p-6 opacity-80">
                            <div className="mb-3 transform scale-150"><IconError /></div>
                            <h3 className="text-red-400 font-bold text-xs uppercase tracking-wider mb-2">Lexer Errors Detected</h3>
                            <p className="text-zinc-500 text-[11px] max-w-[200px]">
                                Fix tokens before parsing.
                            </p>
                        </div>
                      ) : parserErrors.length > 0 ? (
                         <div className="flex-1 flex flex-col items-center justify-center text-center p-6 opacity-80">
                            <div className="mb-3 transform scale-150"><IconError /></div>
                            <h3 className="text-red-400 font-bold text-xs uppercase tracking-wider mb-2">Syntax Errors</h3>
                            <p className="text-zinc-500 text-[11px] max-w-[200px]">
                                See error list above.
                            </p>
                        </div>
                      ) : parseTree ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-center p-6 opacity-80 animate-in fade-in duration-500">
                           <div className="mb-4 transform scale-150"><IconCheck /></div>
                           <h3 className="text-green-400 font-bold text-xs uppercase tracking-wider mb-2">No Syntax Errors</h3>
                           <p className="text-zinc-500 text-[11px]">
                              Valid Soluna syntax. <br/>
                              <span className="opacity-50">(Check Terminal for Logic Errors)</span>
                           </p>
                        </div>
                      ) : (
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
      <div className="h-6 bg-yellow-500 flex items-center px-3 text-black text-[11px] font-bold select-none justify-between shrink-0">
         <div className="flex items-center gap-4">
            <div className="flex items-center gap-1">
               <span className={`w-2 h-2 rounded-full ${wsStatus === 'CONNECTED' ? 'bg-black animate-pulse' : 'bg-red-600'}`}></span>
               {wsStatus}
            </div>
            {errors.length > 0 && (
               <div className="flex items-center gap-1 px-2 py-0.5 bg-black/10 rounded cursor-pointer hover:bg-black/20" onClick={() => {setShowTerminal(true); setActiveTerminalTab('problems');}}>
                  <span>!</span> {errors.length} Error(s)
               </div>
            )}
         </div>
         
         <div className="flex items-center gap-4">
            <div className="flex gap-1 border-r border-black/10 pr-4 mr-1">
               <button onClick={() => setShowLeftSidebar(!showLeftSidebar)} className={`hover:bg-black/10 px-1 rounded ${!showLeftSidebar && 'opacity-50'}`}>[Sidebar]</button>
               <button onClick={() => setShowTerminal(!showTerminal)} className={`hover:bg-black/10 px-1 rounded ${!showTerminal && 'opacity-50'}`}>[Terminal]</button>
               <button onClick={() => setShowRightSidebar(!showRightSidebar)} className={`hover:bg-black/10 px-1 rounded ${!showRightSidebar && 'opacity-50'}`}>[Output]</button>
            </div>
            <span>Ln {tokens.length}</span>
            <span>Soluna 0.50</span>
         </div>
      </div>

    </div>
  );
};

export default App;