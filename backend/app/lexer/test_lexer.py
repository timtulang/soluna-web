import sys
import json

# ----------------------------------------------------------------------
# --- 1. regdef.py ---
# ----------------------------------------------------------------------
REGDEF = {
    'ascii': {chr(i) for i in range(128)},
    'ascii_no_newline': {chr(i) for i in range(128) if chr(i) not in ['\n', '\0']},
    'ascii_298_302': {chr(i) for i in range(128) if chr(i) not in ['\'', '"', '\n', '\\', '\0']},
    'ascii_309': {chr(i) for i in range(128) if chr(i) not in ['*', '\0']},
    'alphabet': {
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    },
    'digit': {
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
    },
    'alphanumeric': {
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
    },
    'arithmetic_operators': {'+', '-', '/', '*', '%', '^'},
    'relational_operators': {'<', '>'}, 
    'general_operators': {'+', '-', '/', '*', '%', '^', '=', '!', '&', '|'},
    'free_delim': {' ', '\\', '\n', '\0' },
    'io_delim': {'(', '\\'}
}

# ----------------------------------------------------------------------
# --- 2. delims.py ---
# ----------------------------------------------------------------------
DELIMS = {
    'separator_delim': {*REGDEF['free_delim'], '(' },
    'and_or_delim': {'(', '!', '"', '-', '\'', '_', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'arithmetic_delim': {'(', '!', '"', '-', '\'', '_', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'comma_equal_delim': {'"', '+', '-', '!', '(', '{', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'iris_sage_delim': {*REGDEF['free_delim'], *REGDEF['arithmetic_operators'], *REGDEF['relational_operators'], ')', ';', ',', '&', '|', '('},
    'label_delim': {*REGDEF['free_delim'], ';'},
    'most_symbol_delim': {'(', '!', '"', '-', '\'', '_', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'control_structure_delim': {*REGDEF['io_delim'], *REGDEF['free_delim']},
    'not_delim': {'"', '-', '!', '(', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'minus_delim': {'(', '!', '"', '\'', '_', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'semicolon_delim': {*REGDEF['alphabet'], *REGDEF['free_delim']},
    'string_concat_delim': {'(', '"', '\'', '_', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'string_length_delim': {'(', '"', '\'', '_', *REGDEF['alphabet']},
    'unary_delim': {'(', '+', '-', '*', '%', '/', *REGDEF['relational_operators'], ')', ';', '&', '|', '\'', '_', '=', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'identifier_delim': {*REGDEF['free_delim'], *REGDEF['arithmetic_operators'], *REGDEF['relational_operators'], '(', ')', '[', '}', '.', ';', ',', '&', '|', '='},
    'warp_delim': {';'},
    'open_bracket_delim': {'"', '\'', '-', '(', '[', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'close_bracket_delim': {';', ',', ')', '}', *REGDEF['free_delim']},
    'open_square_delim': { '“', "‘" , '-', '(', '{', '!' , '_' , *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'close_square_delim': {'[' , '=' , *REGDEF['free_delim']},
    'open_parenthesis_delim': {'"', '+', '-', '!', '(', *REGDEF['alphanumeric'], *REGDEF['free_delim']},
    'close_parenthesis_delim': {';', ',', *REGDEF['general_operators'], ')', ']', '}', *REGDEF['free_delim']},
    'most_data_type_delim': {*REGDEF['general_operators'], *REGDEF['relational_operators'], ')', ']', '}', ';', ',', '.', *REGDEF['free_delim']},
    'leo_delim': {';'},
    'zeru_delim': {*REGDEF['free_delim'], ';', ')', *REGDEF['arithmetic_operators'], *REGDEF['relational_operators']},
    'zara_delim': {*REGDEF['free_delim'], '(', ';'}
}

# ----------------------------------------------------------------------
# --- 3. td.py ---
# ----------------------------------------------------------------------
class State:
    def __init__(self, chars: list[str], branches: list[int] = [], end = False):
        self.chars = [chars] if type(chars) is str else chars
        self.branches = [branches] if type(branches) is int else branches
        self.isEnd = end

STATES = {
    # This is the FULLY CORRECTED states dictionary
    0: State('initial', [1, 10, 16, 20, 25, 32, 42, 46, 68, 72, 79, 86, 92, 114, 119, 129, 138, 144, 150, 154, 160, 162, 166, 170, 174, 179, 183, 186, 189, 192, 194, 196, 198, 200, 202, 204, 206, 208, 210, 257, 297, 303, 309, 317]),
    1: State('a', [2, 5]), 2: State('n', [3]),   3: State('d', [4]),   4: State(DELIMS['separator_delim'], end = True), #and
                           5: State('s', [6]),   6: State('t', [7]),   7: State('e', [8]), 8: State('r', [9]),  9: State(REGDEF['free_delim'], end = True), #aster
    10: State('b', [11]), 11: State('l', [12]), 12: State('a', [13]), 13: State('z', [14]), 14: State('e', [15]), 15: State(REGDEF['free_delim'], end = True),  #blaze
    16: State('c', [17]), 17: State('o', [18]), 18: State('s', [19]), 19: State(REGDEF['free_delim'], end = True),  #cos
    20: State('f', [21]), 21: State('l', [22]), 22: State('u', [23]), 23: State('x', [24]), 24: State(REGDEF['free_delim'], end = True), #flux
    25: State('h', [26]), 26: State('u', [27]), 27: State('b', [28]), 28: State('b', [29]), 29: State('l', [30]), 30: State('e', [31]), 31: State(REGDEF['free_delim'], end = True), #hubble
    32: State('i', [33, 37]), 33: State('r', [34]), 34: State('i', [35]), 35: State('s', [36]), 36: State(DELIMS['iris_sage_delim'], end = True), #iris
                              37: State('x', [38]), 38: State('i', [39]), 39: State('o', [40]), 40: State('n', [41]), 41: State(REGDEF['free_delim'], end = True), #ixion
    42: State('k', [43]),     43: State('a', [44]), 44: State('i', [45]), 45: State(REGDEF['free_delim'], end = True), #kai
    46: State('l', [47, 51, 56]), 47: State('a', [48]),     48: State('n', [49]), 49: State('i', [50]), 50: State(REGDEF['free_delim'], end = True), #lani
                                  51: State('e', [52, 54]), 52: State('o', [53]), 53: State(REGDEF['free_delim'], end = True), #leo
                                                            54: State('t', [55]), 55: State(REGDEF['free_delim'], end = True), #let
                                  56: State('u', [57, 65]), 57: State('m', [58, 61]), 58: State('e', [59]), 59: State('n', [60]), 60: State(REGDEF['io_delim'], end = True), #lumen
                                                                                      61: State('i', [62]), 62: State('n', [63]), 63: State('a', [64]), 64: State(REGDEF['io_delim'], end = True), #lumina
                                                            65: State('n', [66]), 66: State('a', [67]), 67: State(REGDEF['free_delim'], end = True), #luna
    68: State('m', [69]), 69: State('o', [70]),     70: State('s', [71]), 71: State(REGDEF['free_delim'], end = True), #mos
    72: State('n', [73]), 73: State('o', [74, 76]), 74: State('t', [75]), 75: State(DELIMS['separator_delim'], end = True), #not
                                                    76: State('v', [77]), 77: State('a', [78]), 78: State(REGDEF['io_delim'], end = True), #nova
    79: State('o', [80]), 80: State('r', [81, 82]), 81: State(DELIMS['separator_delim'], end = True), #or  
                                                    82: State('b', [83]), 83: State('i', [84]), 84: State('t', [85]), 85: State(REGDEF['free_delim'], end = True), #orbit            
    86: State('p', [87]), 87: State('h', [88]), 88: State('a', [89]), 89: State('s', [90]), 90: State('e', [91]), 91: State(REGDEF['free_delim'], end = True), #phase  
    92: State('s', [93, 97, 103, 110]),  93: State('a', [94]),   94: State('g', [95]), 95: State('e', [96]), 96: State(DELIMS['iris_sage_delim'], end = True), #sage 
                                         97: State('e', [98]),   98: State('l', [99]), 99: State('e', [100]), 100: State('n', [101]), 101: State('e', [102]), 102: State(REGDEF['free_delim'], end = True), #selene
                                        103: State('o', [104]), 104: State('l', [105, 106]), 105: State(DELIMS['separator_delim'], end = True), #sol
                                                                                             106: State('u', [107]), 107: State('n', [108]), 108: State('a', [109]), 109: State(DELIMS['separator_delim'], end = True), #soluna
                                        110: State('t', [111]), 111: State('a', [112]), 112: State('r', [113]), 113: State(REGDEF['free_delim'], end = True), #star
    114: State('v', [115]), 115: State('o', [116]), 116: State('i', [117]), 117: State('d', [118]), 118: State(REGDEF['free_delim'], end = True), #void  
    119: State('w', [120]), 120: State('a', [121, 124, 127]), 121: State('n', [122]), 122: State('e', [123]), 123: State(DELIMS['separator_delim'], end = True), #wane  
                                                              124: State('r', [125]), 125: State('p', [126]), 126: State(DELIMS['warp_delim'], end = True), #warp  
                                                              127: State('x', [128]), 128: State(REGDEF['free_delim'], end = True), #wax 
    129: State('z', [130, 134]), 130: State('a', [131]), 131: State('r', [132]), 132: State('a', [133]), 133: State(DELIMS['zara_delim'], end = True), #zara  
                                 134: State('e', [135]), 135: State('r', [136]), 136: State('u', [137]), 137: State(DELIMS['zeru_delim'], end = True), #zeru  
    # reserved symbols
    138: State('+', [139, 140, 142]), 139: State(DELIMS['arithmetic_delim'], end = True), #+  
                                      140: State('+', [141]), 141: State(DELIMS['unary_delim'], end = True), #++
                                      142: State('=', [143]), 143: State(DELIMS['most_symbol_delim'], end = True), #+=                  
    144: State('-', [145, 146, 148]), 145: State(DELIMS['minus_delim'], end = True), #-
                                      146: State('+', [147]), 147: State(DELIMS['unary_delim'], end = True), #--
                                      148: State('=', [149]), 149: State(DELIMS['most_symbol_delim'], end = True), #-=
    150: State('*', [151, 152]), 151: State(DELIMS['arithmetic_delim'], end = True), #*
                                 152: State('=', [153]), 153: State(DELIMS['most_symbol_delim'], end = True), #*= 
    154: State('/', [155, 156, 158]), 155: State(DELIMS['arithmetic_delim'], end = True), #/
                                      156: State('=', [157]), 157: State(DELIMS['most_symbol_delim'], end = True), #/=
                                      158: State('/', [159]), 159: State(DELIMS['arithmetic_delim'], end = True), #//
    160: State('^', [161]),      161: State(DELIMS['arithmetic_delim'], end = True), #^
    162: State('%', [163, 164]), 163: State(DELIMS['arithmetic_delim'], end = True), #%
                                 164: State('=', [165]), 165: State(DELIMS['most_symbol_delim'], end = True), #%=
    166: State('=', [167, 168]), 167: State(DELIMS['comma_equal_delim'], end = True), #=
                                 168: State('=', [169]), 169: State(DELIMS['most_symbol_delim'], end = True), #==
    170: State('!', [171, 172]), 171: State(DELIMS['not_delim'], end = True), #!
                                 172: State('=', [173]), 173: State(DELIMS['most_symbol_delim'], end = True), #!=
    174: State('<', [175, 177]), 175: State(DELIMS['most_symbol_delim'], end = True), #<
                                 177: State('=', [178]), 178: State(DELIMS['most_symbol_delim'], end = True), #<=
    179: State('>', [180, 181]), 180: State(DELIMS['most_symbol_delim'], end = True), #>
                                 181: State('=', [182]), 182: State(DELIMS['most_symbol_delim'], end = True), #>=
    183: State('&', [184]), 184: State('&', [185]), 185: State(DELIMS['and_or_delim'], end = True), #&&
    186: State('|', [187]), 187: State('|', [188]), 188: State(DELIMS['and_or_delim'], end = True), #||
    189: State('.', [190]), 190: State('.', [191]), 191: State(DELIMS['string_concat_delim'], end = True), #..
    192: State('#', [193]), 193: State(DELIMS['string_length_delim'], end = True), ##
    194: State('(', [195]), 195: State(DELIMS['open_parenthesis_delim'], end = True), #(
    196: State(')', [197]), 197: State(DELIMS['close_parenthesis_delim'], end = True), #)
    198: State('[', [199]), 199: State(DELIMS['open_square_delim'], end = True), #[
    200: State(']', [201]), 201: State(DELIMS['close_square_delim'], end = True), #]
    202: State('{', [203]), 203: State(DELIMS['open_bracket_delim'], end = True), #{
    204: State('}', [205]), 205: State(DELIMS['close_bracket_delim'], end = True), #}
    206: State(',', [207]), 207: State(DELIMS['comma_equal_delim'], end = True), #,
    208: State(';', [209]), 209: State(DELIMS['semicolon_delim'], end = True), #;
    
    # numerical values 
    210: State(REGDEF['digit'], [211, 212, 240]), 211: State(DELIMS['most_data_type_delim'], end = True), #numerical value
        212: State(REGDEF['digit'], [213, 214, 240]), 213: State(DELIMS['most_data_type_delim'], end = True), #numerical value
                214: State(REGDEF['digit'], [215, 216, 240]), 215: State(DELIMS['most_data_type_delim'], end = True), #numerical value
                    216: State(REGDEF['digit'], [217, 218, 240]), 217: State(DELIMS['most_data_type_delim'], end = True), #numerical value
                        218: State(REGDEF['digit'], [219, 220, 240]), 219: State(DELIMS['most_data_type_delim'], end = True), #numerical value
                            220: State(REGDEF['digit'], [221, 222, 240]), 221: State(DELIMS['most_data_type_delim'], end = True), #numerical value
                                222: State(REGDEF['digit'], [223, 224, 240]), 223: State(DELIMS['most_data_type_delim'], end = True), #numerical value
                                    224: State(REGDEF['digit'], [225, 226, 240]), 225: State(DELIMS['most_data_type_delim'], end = True), #numerical value
                                        226: State(REGDEF['digit'], [227, 228, 240]), 227: State(DELIMS['most_data_type_delim'], end = True), #numerical value
                                            228: State(REGDEF['digit'], [229, 230, 240]), 229: State(DELIMS['most_data_type_delim'], end = True), #numerical value
                                                230: State(REGDEF['digit'], [231, 232, 240]), 231: State(DELIMS['most_data_type_delim'], end = True), #numerical value
                                                    232: State(REGDEF['digit'], [233, 234, 240]), 233: State(DELIMS['most_data_type_delim'], end = True), #numerical value
                                                        234: State(REGDEF['digit'], [235, 236, 240]), 235: State(DELIMS['most_data_type_delim'], end = True), #numerical value
                                                            236: State(REGDEF['digit'], [237, 238, 240]), 237: State(DELIMS['most_data_type_delim'], end = True), #numerical value
                                                                238: State(REGDEF['digit'], [239]), 239: State(DELIMS['most_data_type_delim'], end = True), #numerical value
    # numerical values, decimals
    240: State('.', [241]),
        241: State(REGDEF['digit'], [242, 243]), 242: State(DELIMS['most_data_type_delim'], end = True),
            243: State(REGDEF['digit'], [244, 245]), 244: State(DELIMS['most_data_type_delim'], end = True),
                245: State(REGDEF['digit'], [246, 247]), 246: State(DELIMS['most_data_type_delim'], end = True),
                    247: State(REGDEF['digit'], [248, 249]), 248: State(DELIMS['most_data_type_delim'], end = True),
                        249: State(REGDEF['digit'], [250, 251]), 250: State(DELIMS['most_data_type_delim'], end = True),
                            251: State(REGDEF['digit'], [252, 253]), 252: State(DELIMS['most_data_type_delim'], end = True),
                                253: State(REGDEF['digit'], [254, 255]), 254: State(DELIMS['most_data_type_delim'], end = True),
                                    255: State(REGDEF['digit'], [256]), 256: State(DELIMS['most_data_type_delim'], end = True),
    # identifiers
    257: State([*REGDEF['alphabet'], '_'], [258, 259]), 258: State(DELIMS['identifier_delim'], end = True),
        259: State([*REGDEF['alphanumeric'], '_'], [260, 261]), 260: State(DELIMS['identifier_delim'], end = True),
            261: State(REGDEF['alphanumeric'], [262, 263]), 262: State(DELIMS['identifier_delim'], end = True),
                263: State(REGDEF['alphanumeric'], [264, 265]), 264: State(DELIMS['identifier_delim'], end = True),
                    265: State(REGDEF['alphanumeric'], [266, 267]), 266: State(DELIMS['identifier_delim'], end = True),
                        267: State(REGDEF['alphanumeric'], [268, 269]), 268: State(DELIMS['identifier_delim'], end = True),
                            269: State(REGDEF['alphanumeric'], [270, 271]), 270: State(DELIMS['identifier_delim'], end = True),
                                271: State(REGDEF['alphanumeric'], [272, 273]), 272: State(DELIMS['identifier_delim'], end = True),
                                    273: State(REGDEF['alphanumeric'], [274, 275]), 274: State(DELIMS['identifier_delim'], end = True),
                                        275: State(REGDEF['alphanumeric'], [276, 277]), 276: State(DELIMS['identifier_delim'], end = True),
                                            277: State(REGDEF['alphanumeric'], [278, 279]), 278: State(DELIMS['identifier_delim'], end = True),
                                                279: State(REGDEF['alphanumeric'], [280, 281]), 280: State(DELIMS['identifier_delim'], end = True),
                                                    281: State(REGDEF['alphanumeric'], [282, 283]), 282: State(DELIMS['identifier_delim'], end = True),
                                                        283: State(REGDEF['alphanumeric'], [284, 285]), 284: State(DELIMS['identifier_delim'], end = True),
                                                            285: State(REGDEF['alphanumeric'], [286, 287]), 286: State(DELIMS['identifier_delim'], end = True),
                                                                287: State(REGDEF['alphanumeric'], [288, 289]), 288: State(DELIMS['identifier_delim'], end = True),
                                                                    289: State(REGDEF['alphanumeric'], [290, 291]), 290: State(DELIMS['identifier_delim'], end = True),
                                                                        291: State(REGDEF['alphanumeric'], [292, 293]), 292: State(DELIMS['identifier_delim'], end = True),
                                                                            293: State(REGDEF['alphanumeric'], [294, 295]), 294: State(DELIMS['identifier_delim'], end = True),
                                                                                295: State(REGDEF['alphanumeric'], [296]), 296: State(DELIMS['identifier_delim'], end = True),
    # string, char, comments, leo
    # string, char, comments, leo
    297: State('\'', [298, 301]), 298: State(REGDEF['ascii_298_302'], [299]), 299: State('\'', [300]), 300: State(DELIMS['most_data_type_delim'], end = True),
                                  301: State('\\', [298]), 302: State(REGDEF['ascii_298_302'], [299]),
    303: State('"', [304, 307]), 304: State(REGDEF['ascii_298_302'], [304, 305, 307]), 305: State('"', [306]), 306: State(DELIMS['most_data_type_delim'], end = True),
                                                           307: State('\\', [308]), 308: State(REGDEF['ascii_298_302'], [304]),
    
    # --- THIS BLOCK IS NOW FIXED ---
    309: State('\\', [310, 313]), 310: State('\\', [311]), 
                                  311: State(REGDEF['ascii_no_newline'], [311, 312]), 
                                  312: State(['\n', '\0'], end = True), # Accepts newline or EOF
                
                # Multiline Comment Logic
                313: State('*', [314]), # On \*, goto 314
                314: State(REGDEF['ascii_309'], [314, 315]), # Consume any char except *
                315: State('*', [314, 316]), # On *, goto 314 (if not end) or 316
                316: State('\\', [317]), # On \, goto 317 (this is the end)
                317: State(REGDEF['free_delim'], end = True), # NOW it's an end state, delimited by space, \n, ;, etc.
    
    # --- All leo_label states are shifted by +1 ---
    318: State(':', [319]), 319: State(':', [320]), 320: State([*REGDEF['alphanumeric'], '_'], [321]), 321: State(REGDEF['alphanumeric'], [322]), 322: State(REGDEF['alphanumeric'], [323]), 323: State(REGDEF['alphanumeric'], [324]), 324: State(REGDEF['alphanumeric'], [325]), 325: State(':', [326]), 326: State(':', [327]), 327: State(DELIMS['leo_delim'], end = True)
}

# ----------------------------------------------------------------------
# --- 4. token.py ---
# ----------------------------------------------------------------------
RESERVED_WORDS = {
    'and', 'aster', 'blaze', 'cos', 'flux', 'hubble', 'iris', 'ixion', 
    'kai', 'lani', 'leo', 'let', 'lumen', 'lumina', 'luna', 'mos', 'not', 
    'nova', 'or', 'orbit', 'phase', 'sage', 'selene', 'sol', 'soluna', 
    'star', 'void', 'wane', 'warp', 'wax', 'zara', 'zeru'
}
RESERVED_SYMBOLS = {
    '+', '++', '+=', '-', '--', '-=', '*', '*=', '/', '/=', '//', '^', 
    '%', '%=', '=', '==', '!', '!=', '<', '<=', '>', '>=', '&&', '||', 
    '..', '#', '(', ')', '[', ']', '{', '}', ',', ';'
}
def is_leo_label(lexeme):
    if not (lexeme.startswith('::') and lexeme.endswith('::')):
        return False
    middle = lexeme[2:-2]
    if not (1 <= len(middle) <= 5):
        return False
    if not all(c.isalnum() or c == '_' for c in middle):
        return False
    return True

def tokenize(lexemes: list[str], metadata: list):
    token_stream = []
    
    for lexeme in lexemes:
        if isinstance(lexeme, tuple):
            token_stream.append(lexeme)
            continue
        if lexeme in RESERVED_WORDS:
            token_stream.append((lexeme, lexeme))
            continue
        if lexeme in RESERVED_SYMBOLS:
            token_stream.append((lexeme, lexeme))
            continue
        if lexeme.startswith('\\') and lexeme.endswith('\n'):
            token_stream.append((lexeme, 'comment'))
            continue
        if lexeme.startswith('\\*') and lexeme.endswith('*\\'):
            token_stream.append((lexeme, 'comment'))
            continue
        if is_leo_label(lexeme):
            token_stream.append((lexeme, 'leo_label'))
            continue
        if lexeme.startswith('"') and lexeme.endswith('"'):
            token_stream.append((lexeme, 'chika_literal'))
            continue
        if lexeme.startswith("'") and lexeme.endswith("'"):
            token_stream.append((lexeme, 'char_literal'))
            continue
        if lexeme.replace('.', '', 1).isdigit():
            if '.' in lexeme:
                integer_part, fractional_part = lexeme.split('.')
                integer_part = integer_part.lstrip('0') or '0'
                fractional_part = fractional_part.rstrip('0') or '0'
                normalized = integer_part + '.' + fractional_part
                token_stream.append((normalized, 'flux_lit')) 
            else:
                normalized = lexeme.lstrip('0') or '0'
                token_stream.append((normalized, 'kai_lit')) 
            continue
        
        token_stream.append((lexeme, 'id'))

    if metadata and len(metadata) == len(token_stream):
        return [(tok, meta) for tok, meta in zip(token_stream, metadata)]
    return token_stream

# ----------------------------------------------------------------------
# --- 5. lexer_errors.py ---
# ----------------------------------------------------------------------
UNFINISHED_FLUX_STATES = {240}
UNCLOSED_STRING_STATES = {304, 308}
UNCLOSED_CHAR_STATES = {298, 302}
UNCLOSED_COMMENT_STATES = {314, 315, 316}

def check_for_dead_end_error(last_good_active_states, current_lexeme, start_metadata):
    line, col, _, _ = start_metadata
    if not last_good_active_states.isdisjoint(UNFINISHED_FLUX_STATES):
        return ('UNFINISHED_FLUX', (line, col), current_lexeme)
    return None

def check_for_total_failure_error(
    last_good_active_states,
    char_that_killed_it,
    current_lexeme,
    start_metadata
):
    line, col, _, _ = start_metadata
    if char_that_killed_it != '\0' and last_good_active_states:
        all_were_end_states = all(
            state_id in STATES and STATES[state_id].isEnd
            for state_id in last_good_active_states
        )
        if all_were_end_states:
            return ('INVALID_DELIMITER', (line, col), (current_lexeme, char_that_killed_it))

    if char_that_killed_it == '\0':
        if not last_good_active_states.isdisjoint(UNCLOSED_STRING_STATES):
            return ('UNCLOSED_STRING', (line, col), current_lexeme)
        if not last_good_active_states.isdisjoint(UNCLOSED_CHAR_STATES):
            return ('UNCLOSED_CHAR', (line, col), current_lexeme)
        if not last_good_active_states.isdisjoint(UNCLOSED_COMMENT_STATES):
            return ('UNCLOSED_COMMENT', (line, col), current_lexeme)

    return ('UNRECOGNIZED_CHAR', (line, col), char_that_killed_it)

def format_error(error_tuple):
    error_type, (line, col), data = error_tuple
    error_info = {"type": error_type, "line": line, "col": col}
    
    if error_type == 'UNFINISHED_FLUX':
        error_info["message"] = f"Unfinished float literal '{data}'."
    elif error_type == 'INVALID_DELIMITER':
        lexeme, delim = data
        error_info["col"] = col + len(lexeme)
        error_info["message"] = f"Invalid delimiter '{delim}' after token '{lexeme}'."
    elif error_type in ['UNCLOSED_STRING', 'UNCLOSED_COMMENT']:
        error_info["message"] = f"Unclosed {error_type.split('_')[1].lower()}."
    elif error_type == 'UNCLOSED_CHAR':
        error_info["message"] = "Unclosed char literal."
    else: # UNRECOGNIZED_CHAR
        error_info["message"] = f"Unrecognized character '{data}'."
    return error_info

# ----------------------------------------------------------------------
# --- 6. lexer.py ---
# ----------------------------------------------------------------------
class Lexer:
    WHITESPACE = {' ', '\n', '\t', '\r'}
    
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.cursor = 0
        self.line = 1
        self.col = 1

    def _get_char_at(self, index: int) -> str:
        if index < len(self.source_code): return self.source_code[index]
        return '\0'
    
    def _check_char_in_state_chars(self, char: str, state_chars) -> bool:
        try: return char in state_chars
        except: return False
    
    def _skip_ignorable_whitespace(self):
        while self.cursor < len(self.source_code):
            char = self.source_code[self.cursor]
            if char in self.WHITESPACE:
                if char == '\n': self.line += 1; self.col = 1
                else: self.col += 1
                self.cursor += 1
            else: break
    
    def _get_next_token(self):
        active_states = {0}
        current_lexeme = ""
        search_index = self.cursor
        last_accepted_lexeme = None
        last_accepted_end_index = self.cursor
        last_good_active_states = {0}
        char_that_killed_it = '\0'
        while active_states:
            last_good_active_states = active_states
            lookahead_char = self._get_char_at(search_index)
            char_that_killed_it = lookahead_char
            next_active_states = set()
            for state_id in active_states:
                for next_state_id in STATES[state_id].branches:
                    next_state = STATES[next_state_id]
                    if next_state.isEnd and self._check_char_in_state_chars(lookahead_char, next_state.chars):
                        if len(current_lexeme) >= len(last_accepted_lexeme or ""):
                            last_accepted_lexeme = current_lexeme
                            last_accepted_end_index = search_index
            if lookahead_char == '\0': break
            for state_id in active_states:
                for next_state_id in STATES[state_id].branches:
                    next_state = STATES[next_state_id]
                    if not next_state.isEnd and self._check_char_in_state_chars(lookahead_char, next_state.chars):
                        next_active_states.add(next_state_id)
            if not next_active_states: break
            active_states = next_active_states
            current_lexeme += lookahead_char
            search_index += 1
        
        start_meta = (self.line, self.col, self.cursor, last_accepted_end_index)
        if last_accepted_lexeme is not None and len(current_lexeme) > len(last_accepted_lexeme):
            error = check_for_dead_end_error(last_good_active_states, current_lexeme, start_meta)
            if error: return None, error
        if last_accepted_lexeme is not None:
            lexeme = last_accepted_lexeme
            new_cursor_pos = last_accepted_end_index
            return lexeme, new_cursor_pos
        error = check_for_total_failure_error(last_good_active_states, char_that_killed_it, current_lexeme, start_meta)
        return None, error

    def tokenize_all(self):
        lexemes = []
        metadata = []
        
        while self.cursor < len(self.source_code):
            self._skip_ignorable_whitespace()
            if self.cursor >= len(self.source_code): break
                
            start_cursor = self.cursor
            start_line, start_col = self.line, self.col
            
            lexeme, result = self._get_next_token()
            
            if lexeme is None:
                error_tuple = result
                return [], format_error(error_tuple)
            
            end_cursor = result
            lexemes.append(lexeme)
            metadata.append({'line': start_line, 'col': start_col, 'start': start_cursor, 'end': end_cursor})
            
            self.cursor = end_cursor
            for char in lexeme:
                if char == '\n': self.line += 1; self.col = 1
                else: self.col += 1

        tokens = tokenize(lexemes, metadata)
        return tokens, None

# ----------------------------------------------------------------------
# --- 7. Test Runner ---
# ----------------------------------------------------------------------
if __name__ == '__main__':
    print("--- Isolated Lexer Test ---")
    
    # This is the exact string causing the error
    sample_code = r" sol \* comment2 *\ "
    
    print(f"Input code: {sample_code!r}\n")
    
    try:
        lexer = Lexer(sample_code)
        tokens, error = lexer.tokenize_all()
        
        if error:
            print("--- Lexer FAILED ---")
            print(json.dumps(error, indent=2))
        else:
            print("--- Lexer SUCCEEDED ---")
            print("\nFinal Tokens:")
            for token_pair, meta in tokens:
                lexeme, token_type = token_pair
                print(f"  Token: ({lexeme!r}, {token_type!r}) \t| Meta: {meta}")

    except Exception as e:
        print(f"\n--- A CRITICAL ERROR OCCURRED ---")
        print(f"Exception: {e}")