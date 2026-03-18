export type Token = {
  type: string;
  value: string;
  alias?: string;
  line: number;
  col: number;
  start: number;
  end: number;
};

export type LexerError = {
  type: string;
  message: string;
  line: number;
  col: number;
  start: number;
  end: number;
};

export type ParseNode = {
  type?: string;
  data?: string;
  rule?: string;
  value?: string;
  children?: ParseNode[];
  [key: string]: unknown;
};

export type WsMessage = {
  tokens?: Token[];
  errors?: LexerError[];
  warnings?: { type: string, message: string }[];
  parseTree?: ParseNode;
  output?: string;
  transpiledCode?: string;
  isWaitingForInput?: boolean;
  compilationProgress?: CompilationProgress;
};

export type CompilationProgress = {
  stage: 'idle' | 'lexing' | 'parsing' | 'semantic' | 'codegen' | 'complete' | 'error';
  percentage: number;
  message: string;
  timestamp: number;
};

export type CodeFile = {
  id: string;
  name: string;
  content: string;
};

export const tokenColors: Record<string, string> = {
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

export const getColor = (rawType: string): string => {
  if (!rawType) return "#a1a1aa";
  const type = String(rawType).toLowerCase();
  if (tokenColors[type]) return tokenColors[type];
  if (type.length <= 4 && !/^[a-z0-9_]+$/.test(type)) return "#a1a1aa";
  return "#a1a1aa";
};