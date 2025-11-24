#
# td.py (Transition Diagram)
#
# This file *is* the brain of the lexer. It defines the entire
# Finite Automaton (FA) as a dictionary of states.
#
# I import my character sets (REGDEF) and delimiter sets (DELIMS)
# to build the state transitions.
#

from .regdef import REGDEF
from .delims import DELIMS

class State:
    """
    I created this class to represent a single state in my FA.
    
    Attributes:
        chars (list[str]): The set of characters that this state accepts
                           to transition *from* a previous state.
        branches (list[int]): A list of state IDs that this state can
                              transition *to*.
        isEnd (bool): If True, this state represents the end of a
                      valid token. The 'chars' in this case are not
                      for transition, but are the set of *valid delimiters*
                      (from delims.py) that can follow the token.
    """
    def __init__(self, chars: list[str], branches: list[int] = [], end = False):
        # I ensure 'chars' and 'branches' are always lists for consistency.
        self.chars = [chars] if type(chars) is str else chars
        self.branches = [branches] if type(branches) is int else branches
        self.isEnd = end

# This is the complete transition table for my FA.
# Each key is a state ID, and each value is a State object.
STATES = {
    # State 0: The initial state. All possible token paths branch from here.
    0: State('initial', [1, 10, 16, 20, 25, 32, 42, 46, 68, 72, 79, 86, 92, 114, 119, 129, 138, 144, 150, 154, 160, 162, 166, 170, 174, 179, 183, 186, 189, 192, 194, 196, 198, 200, 202, 204, 206, 208, 210, 257, 297, 303, 309, 318]),
    
    # --- Keyword: 'and' and 'aster' ---
    # Path: 0 -> 1 ('a')
    1: State('a', [2, 5]), 
    # Path: 0 -> 1 ('a') -> 2 ('n')
    2: State('n', [3]),
    # Path: 0 -> 1 ('a') -> 2 ('n') -> 3 ('d')
    3: State('d', [4]),
    # Path: 0 -> ... -> 3 ('d') -> 4 (End State for 'and')
    4: State(DELIMS['separator_delim'], end = True), # 'and'
    # Path: 0 -> 1 ('a') -> 5 ('s') ...
                           5: State('s', [6]),   6: State('t', [7]),   7: State('e', [8]), 8: State('r', [9]),  9: State(REGDEF['free_delim'], end = True), # 'aster'
    
    # --- Keywords (blaze, cos, flux, hubble) ---
    10: State('b', [11]), 11: State('l', [12]), 12: State('a', [13]), 13: State('z', [14]), 14: State('e', [15]), 15: State(REGDEF['free_delim'], end = True),  # 'blaze'
    16: State('c', [17]), 17: State('o', [18]), 18: State('s', [19]), 19: State(REGDEF['free_delim'], end = True),  # 'cos'
    20: State('f', [21]), 21: State('l', [22]), 22: State('u', [23]), 23: State('x', [24]), 24: State(REGDEF['free_delim'], end = True), # 'flux'
    25: State('h', [26]), 26: State('u', [27]), 27: State('b', [28]), 28: State('b', [29]), 29: State('l', [30]), 30: State('e', [31]), 31: State(REGDEF['free_delim'], end = True), # 'hubble'

    # --- Keywords: 'iris' and 'ixion' ---
    # This path (starting with 'i') branches.
    32: State('i', [33, 37]), 
    # Path for 'iris'
    33: State('r', [34]), 34: State('i', [35]), 35: State('s', [36]), 36: State(DELIMS['iris_sage_delim'], end = True), # 'iris'
    # Path for 'ixion'
    37: State('x', [38]), 38: State('i', [39]), 39: State('o', [40]), 40: State('n', [41]), 41: State(REGDEF['free_delim'], end = True), # 'ixion'
    
    # --- Keyword: 'kai' ---
    42: State('k', [43]),     43: State('a', [44]), 44: State('i', [45]), 45: State(REGDEF['free_delim'], end = True), # 'kai'

    # --- Keywords: 'lani', 'leo', 'let', 'lumen', 'lumina', 'luna' ---
    # This is my most complex keyword branch, starting with 'l'.
    46: State('l', [47, 51, 56]), 
    # Path for 'lani'
    47: State('a', [48]),     48: State('n', [49]), 49: State('i', [50]), 50: State(REGDEF['free_delim'], end = True), # 'lani'
    # Path for 'leo' and 'let'
    51: State('e', [52, 54]), 
    52: State('o', [53]), 53: State(REGDEF['free_delim'], end = True), # 'leo'
    54: State('t', [55]), 55: State(REGDEF['free_delim'], end = True), # 'let'
    # Path for 'lumen', 'lumina', 'luna'
    56: State('u', [57, 65]), 
    57: State('m', [58, 61]), 
    # Path for 'lumen'
    58: State('e', [59]), 59: State('n', [60]), 60: State(REGDEF['io_delim'], end = True), # 'lumen'
    # Path for 'lumina'
    61: State('i', [62]), 62: State('n', [63]), 63: State('a', [64]), 64: State(REGDEF['io_delim'], end = True), # 'lumina'
    # Path for 'luna'
    65: State('n', [66]), 66: State('a', [67]), 67: State(REGDEF['free_delim'], end = True), # 'luna'

    # --- Keywords (mos, not, nova, or, orbit, phase) ---
    68: State('m', [69]), 69: State('o', [70]),     70: State('s', [71]), 71: State(REGDEF['free_delim'], end = True), # 'mos'
    72: State('n', [73]), 73: State('o', [74, 76]), 74: State('t', [75]), 75: State(DELIMS['separator_delim'], end = True), # 'not'
                                                    76: State('v', [77]), 77: State('a', [78]), 78: State(REGDEF['io_delim'], end = True), # 'nova'
    79: State('o', [80]), 80: State('r', [81, 82]), 81: State(DELIMS['separator_delim'], end = True), # 'or'  
                                                    82: State('b', [83]), 83: State('i', [84]), 84: State('t', [85]), 85: State(REGDEF['free_delim'], end = True), # 'orbit'            
    86: State('p', [87]), 87: State('h', [88]), 88: State('a', [89]), 89: State('s', [90]), 90: State('e', [91]), 91: State(REGDEF['free_delim'], end = True), # 'phase'  
    
    # --- Keywords (sage, selene, sol, soluna, star) ---
    92: State('s', [93, 97, 103, 110]),  
    93: State('a', [94]),   94: State('g', [95]), 95: State('e', [96]), 96: State(DELIMS['iris_sage_delim'], end = True), # 'sage' 
    97: State('e', [98]),   98: State('l', [99]), 99: State('e', [100]), 100: State('n', [101]), 101: State('e', [102]), 102: State(REGDEF['free_delim'], end = True), # 'selene'
    103: State('o', [104]), 104: State('l', [105, 106]), 105: State(DELIMS['separator_delim'], end = True), # 'sol'
                                                         106: State('u', [107]), 107: State('n', [108]), 108: State('a', [109]), 109: State(DELIMS['separator_delim'], end = True), # 'soluna'
    110: State('t', [111]), 111: State('a', [112]), 112: State('r', [113]), 113: State(REGDEF['free_delim'], end = True), # 'star'
    
    # --- Keywords (void, wane, warp, wax, zara, zeru, zeta) ---
    114: State('v', [115]), 115: State('o', [116]), 116: State('i', [117]), 117: State('d', [118]), 118: State(REGDEF['free_delim'], end = True), # 'void'  
    119: State('w', [120]), 120: State('a', [121, 124, 127]), 121: State('n', [122]), 122: State('e', [123]), 123: State(DELIMS['separator_delim'], end = True), # 'wane'  
                                                              124: State('r', [125]), 125: State('p', [126]), 126: State(DELIMS['warp_delim'], end = True), # 'warp'  
                                                              127: State('x', [128]), 128: State(REGDEF['free_delim'], end = True), # 'wax' 
    # 'z' branch: 'zara', 'zeru', 'zeta'
    # 129 ('z') -> 130 ('a') for zara
    # 129 ('z') -> 134 ('e') for zeru/zeta
    129: State('z', [130, 134]), 
        # Path for 'zara'
        130: State('a', [131]), 131: State('r', [132]), 132: State('a', [133]), 133: State(DELIMS['zara_delim'], end = True), # 'zara'  
        # Path for 'zeru' and 'zeta'
        # 134 ('e') branches to 135 ('r') or 328 ('t')
        134: State('e', [135, 328]), 
            # zeru
            135: State('r', [136]), 136: State('u', [137]), 137: State(DELIMS['zeru_delim'], end = True), # 'zeru'
            # zeta (NEW)
            328: State('t', [329]), 329: State('a', [330]), 330: State(REGDEF['free_delim'], end = True), # 'zeta'
    
    # --- Reserved Symbols ---
    
    # +, ++, +=
    138: State('+', [139, 140, 142]), 
    139: State(DELIMS['arithmetic_delim'], end = True), # +  (End state)
    140: State('+', [141]), 
    141: State(DELIMS['unary_delim'], end = True), # ++ (End state)
    142: State('=', [143]), 
    143: State(DELIMS['most_symbol_delim'], end = True), # += (End state)
    
    # -, --, -=, AND NEGATIVE NUMBERS
    # Modified 144: Accepts '-' and branches to:
    # 145 (- delimiter), 146 (--), 148 (-=)
    # AND 210 (Start of number chain for negative literals)
    144: State('-', [145, 146, 148, 210]), 
    145: State(DELIMS['minus_delim'], end = True), # -
    146: State('-', [147]), 
    147: State(DELIMS['unary_delim'], end = True), # --
    148: State('=', [149]), 
    149: State(DELIMS['most_symbol_delim'], end = True), # -=
    
    # *, *=
    150: State('*', [151, 152]), 
    151: State(DELIMS['arithmetic_delim'], end = True), # *
    152: State('=', [153]), 
    153: State(DELIMS['most_symbol_delim'], end = True), # *= 
    
    # /, /=, //
    154: State('/', [155, 156, 158]), 
    155: State(DELIMS['arithmetic_delim'], end = True), # /
    156: State('=', [157]), 
    157: State(DELIMS['most_symbol_delim'], end = True), # /=
    158: State('/', [159]), 
    159: State(DELIMS['arithmetic_delim'], end = True), # //
    
    # ^
    160: State('^', [161]),      
    161: State(DELIMS['arithmetic_delim'], end = True), # ^
    
    # %, %=
    162: State('%', [163, 164]), 
    163: State(DELIMS['arithmetic_delim'], end = True), # %
    164: State('=', [165]), 
    165: State(DELIMS['most_symbol_delim'], end = True), # %=
    
    # =, ==
    166: State('=', [167, 168]), 
    167: State(DELIMS['comma_equal_delim'], end = True), # =
    168: State('=', [169]), 
    169: State(DELIMS['most_symbol_delim'], end = True), # ==
    
    # !, !=
    170: State('!', [171, 172]), 
    171: State(DELIMS['not_delim'], end = True), # !
    172: State('=', [173]), 
    173: State(DELIMS['most_symbol_delim'], end = True), # !=
    
    # <, <=
    174: State('<', [175, 177]), 
    175: State(DELIMS['most_symbol_delim'], end = True), # <
    177: State('=', [178]), 
    178: State(DELIMS['most_symbol_delim'], end = True), # <=
    
    # >. >=
    179: State('>', [180, 181]), 
    180: State(DELIMS['most_symbol_delim'], end = True), # >
    181: State('=', [182]), 
    182: State(DELIMS['most_symbol_delim'], end = True), # >=
    
    # &&
    183: State('&', [184]), 
    184: State('&', [185]), 
    185: State(DELIMS['and_or_delim'], end = True), # &&
    
    # ||
    186: State('|', [187]), 
    187: State('|', [188]), 
    188: State(DELIMS['and_or_delim'], end = True), # ||
    
    # ..
    189: State('.', [190]), 
    190: State('.', [191]), 
    191: State(DELIMS['string_concat_delim'], end = True), # ..
    
    # #
    192: State('#', [193]), 
    193: State(DELIMS['string_length_delim'], end = True), # #
    
    # Grouping Symbols: (, ), [, ], {, }
    194: State('(', [195]), 195: State(DELIMS['open_parenthesis_delim'], end = True), #(
    196: State(')', [197]), 197: State(DELIMS['close_parenthesis_delim'], end = True), #)
    198: State('[', [199]), 199: State(DELIMS['open_square_delim'], end = True), #[
    200: State(']', [201]), 201: State(DELIMS['close_square_delim'], end = True), #]
    202: State('{', [203]), 203: State(DELIMS['open_bracket_delim'], end = True), #{
    204: State('}', [205]), 205: State(DELIMS['close_bracket_delim'], end = True), #}
    
    # ,
    206: State(',', [207]), 207: State(DELIMS['comma_equal_delim'], end = True), #,
    
    # ;
    208: State(';', [209]), 209: State(DELIMS['semicolon_delim'], end = True), #;
    
    # --- Numerical Values (Integers) ---
    # This is a "chain" of states to accept digits.
    # Each state in the chain (211, 213, 215...) is an end state,
    # allowing for numbers of different lengths.
    # Each state also branches to state 240 ('.') to start a float.
    210: State(REGDEF['digit'], [211, 212, 240]), 211: State(DELIMS['float_delim'], end = True), # 1-digit int
        212: State(REGDEF['digit'], [213, 214, 240]), 213: State(DELIMS['float_delim'], end = True), # 2-digit int
                214: State(REGDEF['digit'], [215, 216, 240]), 215: State(DELIMS['float_delim'], end = True), # 3-digit int
                    216: State(REGDEF['digit'], [217, 218, 240]), 217: State(DELIMS['float_delim'], end = True), # 4-digit int
                        218: State(REGDEF['digit'], [219, 220, 240]), 219: State(DELIMS['float_delim'], end = True), # 5-digit int
                            220: State(REGDEF['digit'], [221, 222, 240]), 221: State(DELIMS['float_delim'], end = True), # 6-digit int
                                222: State(REGDEF['digit'], [223, 224, 240]), 223: State(DELIMS['float_delim'], end = True), # 7-digit int
                                    224: State(REGDEF['digit'], [225, 226, 240]), 225: State(DELIMS['float_delim'], end = True), # 8-digit int
                                        226: State(REGDEF['digit'], [227, 228, 240]), 227: State(DELIMS['float_delim'], end = True), # 9-digit int
                                            228: State(REGDEF['digit'], [229, 230, 240]), 229: State(DELIMS['float_delim'], end = True), # 10-digit int
                                                230: State(REGDEF['digit'], [231, 232, 240]), 231: State(DELIMS['float_delim'], end = True), # 11-digit int
                                                    232: State(REGDEF['digit'], [233, 234, 240]), 233: State(DELIMS['float_delim'], end = True), # 12-digit int
                                                        234: State(REGDEF['digit'], [235, 236, 240]), 235: State(DELIMS['float_delim'], end = True), # 13-digit int
                                                            236: State(REGDEF['digit'], [237, 238, 240]), 237: State(DELIMS['float_delim'], end = True), # 14-digit int
                                                                238: State(REGDEF['digit'], [239]), 239: State(DELIMS['float_delim'], end = True), # 15-digit int
    
    # --- Numerical Values (Floats) ---
    # State 240 is the "start of fractional part" state.
    # It *must* be followed by at least one digit (state 241).
    240: State('.', [241]),
        # State 241 is the first digit *after* the decimal.
        241: State(REGDEF['digit'], [242, 243]), 242: State(DELIMS['float_delim'], end = True), # x.1 (Length 1) -> FLUX
            # This chain (243, 245, etc.) accepts more fractional digits.
            243: State(REGDEF['digit'], [244, 245]), 244: State(DELIMS['float_delim'], end = True), # x.12 (Length 2) -> FLUX
                245: State(REGDEF['digit'], [246, 247]), 246: State(DELIMS['float_delim'], end = True), # x.123 (Length 3) -> FLUX
                    247: State(REGDEF['digit'], [248, 249]), 248: State(DELIMS['float_delim'], end = True), # x.1234 (Length 4) -> FLUX
                        249: State(REGDEF['digit'], [250, 251]), 250: State(DELIMS['float_delim'], end = True), # x.12345 (Length 5) -> ASTER
                            251: State(REGDEF['digit'], [252, 253]), 252: State(DELIMS['float_delim'], end = True), # x.123456 (Length 6) -> ASTER
                                253: State(REGDEF['digit'], [254, 255]), 254: State(DELIMS['float_delim'], end = True), # x.1234567 (Length 7) -> ASTER
                                    255: State(REGDEF['digit'], [256]), 256: State(DELIMS['float_delim'], end = True), # x.12345678 (Length 8) -> ASTER
    
    # --- Identifiers ---
    # State 257: Must start with a letter or underscore.
    257: State([*REGDEF['alphabet'], '_'], [258, 259]), 
    258: State(DELIMS['identifier_delim'], end = True),
        259: State([*REGDEF['alphanumeric'], '_'], [260, 261]), 
        260: State(DELIMS['identifier_delim'], end = True),
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
    
    # --- Character Literals (e.g., 'a', '\n') ---
    297: State('\'', [298, 301]), 
    298: State(REGDEF['ascii_298_302'], [299]), 
    299: State('\'', [300]), 
    300: State(DELIMS['most_data_type_delim'], end = True),
    301: State('\\', [302]), 
    302: State(REGDEF['ascii_298_302'], [299]), 
    303: State('"', [304, 305, 307]), 
    304: State(REGDEF['ascii_298_302'], [304, 305, 307]), 
    305: State('"', [306]), 
    306: State(DELIMS['most_data_type_delim'], end = True),
    307: State('\\', [308]), 
    308: State(REGDEF['ascii_298_302'], [304]),
    
    # --- Comments (Single and Multi-line) ---
    309: State('\\', [310, 313]), 
    310: State('\\', [311]), 
    311: State(REGDEF['ascii_no_newline'], [311, 312]), 
    312: State('\n', end = True),
    
    # Path for multi-line comment: \* ... *\
    313: State('*', [314]), 
    # State 314: "Main Body" state.
    314: State(REGDEF['ascii_309'], [314, 315]),
    # State 315: "Saw a *" state.
    315: State('*', [3150, 315, 316]), 
    # State 3150: "Safe Return".
    3150: State(REGDEF['ascii_safe_comment_body'], [314, 315]),
    # State 316: Seen the closing *\
    316: State('\\', [317]),
    # State 317: End state for the multi-line comment.
    317: State(REGDEF['free_delim'], end = True), 
    
    # --- Leo Labels ---
    318: State(':', [319]), 
    319: State(':', [320]), 
    320: State([*REGDEF['alphanumeric'], '_'], [321, 325]), 
    321: State([*REGDEF['alphanumeric'], '_'], [322, 325]), 
    322: State([*REGDEF['alphanumeric'], '_'], [323, 325]), 
    323: State([*REGDEF['alphanumeric'], '_'], [324, 325]), 
    324: State([*REGDEF['alphanumeric'], '_'], [325]),      
    325: State(':', [326]), 
    326: State(':', [327]), 
    327: State(DELIMS['leo_delim'], end = True)
}

# NEW: Define Identifier End States for logic checking
ID_END_STATES = {
    258, 260, 262, 264, 266, 268, 270, 272, 274, 276, 
    278, 280, 282, 284, 286, 288, 290, 292, 294, 296
}