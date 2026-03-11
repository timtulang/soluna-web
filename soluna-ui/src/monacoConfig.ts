import type * as MonacoTypes from "monaco-editor";

export const setupMonaco = (monaco: typeof MonacoTypes) => {
  const TYPES = ['kai', 'flux', 'selene', 'blaze', 'lani', 'let'];
  const CONTROL = ['sol', 'soluna', 'luna', 'orbit', 'cos', 'phase', 'wax', 'wane', 'warp', 'mos'];
  const DECL = ['zeta', 'void', 'local', 'hubble'];
  const FUNCS = ['zara', 'lumina', 'nova', 'lumen'];
  const LITERALS = ['iris', 'sage'];
  const LOGICAL = ['not', 'and', 'or'];
  const MISC = ['leo', 'label'];

  const ALL_KEYWORDS = [...TYPES, ...CONTROL, ...DECL, ...FUNCS, ...LITERALS, ...LOGICAL, ...MISC];

  if (!monaco.languages.getLanguages().find((l) => l.id === 'soluna')) {
    monaco.languages.register({ id: 'soluna' });

    const kwRegex = new RegExp(`\\b(${ALL_KEYWORDS.join('|')})\\b`);
    
    monaco.languages.setMonarchTokensProvider('soluna', {
      keywords: ALL_KEYWORDS,
      tokenizer: {
        root: [
          [/\\\\.*$/, 'comment'],
          [/\/\*/, 'comment', '@block_comment'],
          [/"([^"\\]|\\.)*$/, 'string.invalid'],
          [/"/, 'string', '@string_double'],
          [/'[^\\']'/, 'string.char'],
          [kwRegex, 'keyword'],
          [/#[a-zA-Z_]\w*/, 'operator.length'],
          [/[a-zA-Z_]\w*/, 'identifier'],
          [/\d+\.\d*([eE][+-]?\d+)?/, 'number.float'],
          [/\d+/, 'number'],
          [/&&|\|\||!=|==|>=|<=|\+\+|--|[+\-]=|[*\/]=|%=|\.\.|[+\-*\/%^<>=!]/, 'operator'],
          [/[{}()\[\]]/, 'delimiter.bracket'],
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

    monaco.editor.defineTheme('soluna-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'keyword', foreground: 'c084fc', fontStyle: 'bold' },
        { token: 'identifier', foreground: '60a5fa' },
        { token: 'number', foreground: '4ade80' },
        { token: 'number.float', foreground: '4ade80' },
        { token: 'string', foreground: '4ade80' },
        { token: 'string.char', foreground: '4ade80' },
        { token: 'string.escape', foreground: 'facc15' },
        { token: 'string.invalid', foreground: 'f87171' },
        { token: 'comment', foreground: '52525b', fontStyle: 'italic' },
        { token: 'delimiter.bracket', foreground: 'facc15' },
        { token: 'operator', foreground: 'a1a1aa' },
        { token: 'operator.length', foreground: 'facc15' },
        { token: 'delimiter', foreground: 'a1a1aa' },
      ],
      colors: {
        'editor.background': '#000000',
        'editor.foreground': '#d4d4d8',
        'editorLineNumber.foreground': '#3f3f46',
        'editorLineNumber.activeForeground': '#facc15',
        'editor.lineHighlightBackground': '#18181b',
        'editorCursor.foreground': '#facc15',
        'editor.selectionBackground': '#facc1540',
        'editorIndentGuide.background': '#27272a',
        'editorWidget.background': '#09090b',
        'editorSuggestWidget.background': '#09090b',
        'editorSuggestWidget.border': '#3f3f46',
        'editorSuggestWidget.selectedBackground': '#facc1520',
        'editorSuggestWidget.highlightForeground': '#facc15',
        'list.hoverBackground': '#18181b',
        'list.activeSelectionBackground': '#facc1520',
        'list.activeSelectionForeground': '#facc15',
      },
    });
    monaco.editor.setTheme('soluna-dark');

    monaco.languages.registerCompletionItemProvider('soluna', {
      provideCompletionItems: (model, position) => {
        const word = model.getWordUntilPosition(position);
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn,
        };
        const KW = monaco.languages.CompletionItemKind.Keyword;
        const SN = monaco.languages.CompletionItemKind.Snippet;
        const ITR = monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet;

        return {
          suggestions: [
            { label: 'kai', kind: KW, insertText: 'kai ${1:name};', insertTextRules: ITR, detail: 'int', range },
            { label: 'flux', kind: KW, insertText: 'flux ${1:name};', insertTextRules: ITR, detail: 'float', range },
            { label: 'selene', kind: KW, insertText: 'selene ${1:name};', insertTextRules: ITR, detail: 'double', range },
            { label: 'blaze', kind: KW, insertText: 'blaze ${1:name};', insertTextRules: ITR, detail: 'char', range },
            { label: 'lani', kind: KW, insertText: 'lani ${1:name};', insertTextRules: ITR, detail: 'bool', range },
            { label: 'let', kind: KW, insertText: 'let ${1:name};', insertTextRules: ITR, detail: 'string', range },
            { label: 'void', kind: KW, insertText: 'void', insertTextRules: ITR, detail: 'void return type', range },
            { label: 'zeta', kind: KW, insertText: 'zeta', insertTextRules: ITR, detail: 'const modifier', range },
            { label: 'local', kind: KW, insertText: 'local', insertTextRules: ITR, detail: 'local scope', range },
            { label: 'kai =', kind: SN, insertText: 'kai ${1:name} = ${2:0};', insertTextRules: ITR, detail: 'int with value', range },
            { label: 'flux =', kind: SN, insertText: 'flux ${1:name} = ${2:0.0};', insertTextRules: ITR, detail: 'float with value', range },
            { label: 'selene =', kind: SN, insertText: 'selene ${1:name} = ${2:0.0};', insertTextRules: ITR, detail: 'double with value', range },
            { label: 'blaze =', kind: SN, insertText: 'blaze ${1:name} = \'${2:a}\';', insertTextRules: ITR, detail: 'char with value', range },
            { label: 'lani =', kind: SN, insertText: 'lani ${1:name} = ${2:iris};', insertTextRules: ITR, detail: 'bool with value', range },
            { label: 'let =', kind: SN, insertText: 'let ${1:name} = "${2:value}";', insertTextRules: ITR, detail: 'string with value', range },
            { label: 'zeta kai', kind: SN, insertText: 'zeta kai ${1:name} = ${2:0};', insertTextRules: ITR, detail: 'const int', range },
            { label: 'hubble', kind: KW, insertText: 'hubble', insertTextRules: ITR, detail: 'table/array keyword', range },
            { label: 'hubble []', kind: SN, insertText: 'hubble ${1:kai} ${2:name} = { ${3:elements} };', insertTextRules: ITR, detail: 'Table declaration', range },
            { label: 'func', kind: SN, insertText: '${1:void} ${2:name}(${3:params})\n\t${4}\nmos', insertTextRules: ITR, detail: 'Function definition', range },
            { label: 'kai func', kind: SN, insertText: 'kai ${1:name}(${2:params})\n\t${3}\n\tzara ${4:0};\nmos', insertTextRules: ITR, detail: 'int-returning function', range },
            { label: 'void func', kind: SN, insertText: 'void ${1:name}(${2:params})\n\t${3}\nmos', insertTextRules: ITR, detail: 'void function', range },
            { label: 'zara', kind: KW, insertText: 'zara ${1:value};', insertTextRules: ITR, detail: 'return statement', range },
            { label: 'sol', kind: SN, insertText: 'sol ${1:condition}\n\t${2}\nmos', insertTextRules: ITR, detail: 'if statement', range },
            { label: 'sol soluna luna', kind: SN, insertText: 'sol ${1:condition}\n\t${2}\nmos\nsoluna ${3:condition}\n\t${4}\nmos\nluna\n\t${5}\nmos', insertTextRules: ITR, detail: 'if / else if / else', range },
            { label: 'soluna', kind: SN, insertText: 'soluna ${1:condition}\n\t${2}\nmos', insertTextRules: ITR, detail: 'else-if branch', range },
            { label: 'luna', kind: SN, insertText: 'luna\n\t${1}\nmos', insertTextRules: ITR, detail: 'else branch', range },
            { label: 'orbit', kind: SN, insertText: 'orbit ${1:condition} cos\n\t${2}\nmos', insertTextRules: ITR, detail: 'while loop', range },
            { label: 'phase', kind: SN, insertText: 'phase kai ${1:i} = ${2:0}, ${3:limit}, ${4:1} cos\n\t${5}\nmos', insertTextRules: ITR, detail: 'for loop', range },
            { label: 'wax wane', kind: SN, insertText: 'wax\n\t${1}\nwane ${2:condition}', insertTextRules: ITR, detail: 'repeat-until loop', range },
            { label: 'warp', kind: KW, insertText: 'warp;', insertTextRules: ITR, detail: 'break statement', range },
            { label: 'mos', kind: KW, insertText: 'mos', insertTextRules: ITR, detail: 'end block', range },
            { label: 'cos', kind: KW, insertText: 'cos', insertTextRules: ITR, detail: 'open loop body', range },
            { label: 'nova', kind: SN, insertText: 'nova(${1:expression});', insertTextRules: ITR, detail: 'print (no newline)', range },
            { label: 'lumen', kind: SN, insertText: 'lumen(${1:expression});', insertTextRules: ITR, detail: 'println (with newline)', range },
            { label: 'lumina', kind: SN, insertText: 'lumina()', insertTextRules: ITR, detail: 'input function', range },
            { label: 'iris', kind: KW, insertText: 'iris', insertTextRules: ITR, detail: 'true', range },
            { label: 'sage', kind: KW, insertText: 'sage', insertTextRules: ITR, detail: 'false', range },
            { label: 'and', kind: KW, insertText: 'and', insertTextRules: ITR, detail: 'logical AND', range },
            { label: 'or', kind: KW, insertText: 'or', insertTextRules: ITR, detail: 'logical OR', range },
            { label: 'not', kind: KW, insertText: 'not', insertTextRules: ITR, detail: 'logical NOT', range },
            { label: 'label', kind: KW, insertText: 'label ${1:name};', insertTextRules: ITR, detail: 'label declaration', range },
            { label: 'leo', kind: SN, insertText: 'leo label ${1:name};', insertTextRules: ITR, detail: 'goto label', range },
          ]
        };
      },
    });
  } else {
    monaco.editor.setTheme('soluna-dark');
  }
};