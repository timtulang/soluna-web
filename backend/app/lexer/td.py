#
# td.py (Transition Diagram)
#
# This file *is* the brain of the lexer. It defines the entire
# Finite Automaton (FA) as a dictionary of states.
#

from .regdef import REGDEF
from .delims import DELIMS

class State:
    """
    I created this class to represent a single state in my FA.
    """
    def __init__(self, chars: list[str], branches: list[int] = [], end = False):
        self.chars = [chars] if type(chars) is str else chars
        self.branches = [branches] if type(branches) is int else branches
        self.isEnd = end

# This is the complete transition table for my FA.
STATES = {
    # --- State 0: Initial State ---
    0: State('initial', [
        1, 10, 16, 20, 25, 32, 42, 46, 73, 77, 84, 91, 97, 119, 124, 134, 
        143, 149, 155, 159, 165, 167, 171, 175, 179, 184, 188, 191, 194, 
        197, 199, 201, 203, 205, 207, 209, 211, 213, 215, 262, 302, 308, 
        314, 323
    ]),
    
    # --- Keyword: 'and' ---
    1: State('a', [2]),
    2: State('n', [3]),
    3: State('d', [4]),
    4: State(DELIMS['separator_delim'], end=True), # 'and'
    
    # --- Keyword: 'blaze' ---
    10: State('b', [11]), 
    11: State('l', [12]), 
    12: State('a', [13]), 
    13: State('z', [14]), 
    14: State('e', [15]), 
    15: State(REGDEF['free_delim'], end=True), 

    # --- Keyword: 'cos' ---
    16: State('c', [17]), 
    17: State('o', [18]), 
    18: State('s', [19]), 
    19: State(REGDEF['free_delim'], end=True), 

    # --- Keyword: 'flux' ---
    20: State('f', [21]), 
    21: State('l', [22]), 
    22: State('u', [23]), 
    23: State('x', [24]), 
    24: State(REGDEF['free_delim'], end=True), 

    # --- Keyword: 'hubble' ---
    25: State('h', [26]), 
    26: State('u', [27]), 
    27: State('b', [28]), 
    28: State('b', [29]), 
    29: State('l', [30]), 
    30: State('e', [31]), 
    31: State(REGDEF['free_delim'], end=True), 

    # --- Keywords: 'iris' and 'ixion' ---
    32: State('i', [33, 37]), 
    
    # 'iris'
    33: State('r', [34]), 
    34: State('i', [35]), 
    35: State('s', [36]), 
    36: State(DELIMS['iris_sage_delim'], end=True), 
    
    # 'ixion'
    37: State('x', [38]), 
    38: State('i', [39]), 
    39: State('o', [40]), 
    40: State('n', [41]), 
    41: State(REGDEF['free_delim'], end=True), 
    
    # --- Keyword: 'kai' ---
    42: State('k', [43]), 
    43: State('a', [44]), 
    44: State('i', [45]), 
    45: State(REGDEF['free_delim'], end=True), 

    # --- Keywords: 'lani', 'leo', 'let', 'local', 'lumen', 'lumina', 'luna' ---
    46: State('l', [47, 51, 56, 61]), 
    
    # 'lani'
    47: State('a', [48]), 
    48: State('n', [49]), 
    49: State('i', [50]), 
    50: State(REGDEF['free_delim'], end=True), 
    
    # 'leo' & 'let'
    51: State('e', [52, 54]), 
    52: State('o', [53]), 
    53: State(REGDEF['free_delim'], end=True), # 'leo'
    54: State('t', [55]), 
    55: State(REGDEF['free_delim'], end=True), # 'let'

    # 'local'
    56: State('o', [57]), 
    57: State('c', [58]), 
    58: State('a', [59]), 
    59: State('l', [60]), 
    60: State(REGDEF['free_delim'], end=True), 

    # 'lumen', 'lumina', 'luna'
    61: State('u', [62, 70]), 
    62: State('m', [63, 66]), 
    
    # 'lumen'
    63: State('e', [64]), 
    64: State('n', [65]), 
    65: State(REGDEF['io_delim'], end=True), 
    
    # 'lumina'
    66: State('i', [67]), 
    67: State('n', [68]), 
    68: State('a', [69]), 
    69: State(REGDEF['io_delim'], end=True), 
    
    # 'luna'
    70: State('n', [71]), 
    71: State('a', [72]), 
    72: State(REGDEF['free_delim'], end=True), 

    # --- Keyword: 'mos' ---
    # UPDATED: Allows '}' and ';' as delimiters (based on previous fix)
    73: State('m', [74]), 
    74: State('o', [75]), 
    75: State('s', [76]), 
    76: State({*REGDEF['free_delim'], '}', ';', ')'}, end=True), 
    
    # --- Keywords: 'not', 'nova' ---
    77: State('n', [78]), 
    78: State('o', [79, 81]), 
    
    # 'not'
    79: State('t', [80]), 
    80: State(DELIMS['separator_delim'], end=True), 
    
    # 'nova'
    81: State('v', [82]), 
    82: State('a', [83]), 
    83: State(REGDEF['io_delim'], end=True), 
    
    # --- Keywords: 'or', 'orbit' ---
    84: State('o', [85]), 
    85: State('r', [86, 87]), 
    86: State(DELIMS['separator_delim'], end=True), # 'or'  
    
    # 'orbit'
    87: State('b', [88]), 
    88: State('i', [89]), 
    89: State('t', [90]), 
    90: State(REGDEF['free_delim'], end=True),            
    
    # --- Keyword: 'phase' ---
    91: State('p', [92]), 
    92: State('h', [93]), 
    93: State('a', [94]), 
    94: State('s', [95]), 
    95: State('e', [96]), 
    96: State(REGDEF['free_delim'], end=True),  
    
    # --- Keywords: 'sage', 'selene', 'sol', 'soluna', 'star' ---
    97: State('s', [98, 102, 108, 115]),  
    
    # 'sage'
    98: State('a', [99]), 
    99: State('g', [100]), 
    100: State('e', [101]), 
    101: State(DELIMS['iris_sage_delim'], end=True), 
    
    # 'selene'
    102: State('e', [103]), 
    103: State('l', [104]), 
    104: State('e', [105]), 
    105: State('n', [106]), 
    106: State('e', [107]), 
    107: State(REGDEF['free_delim'], end=True), 
    
    # 'sol' & 'soluna'
    108: State('o', [109]), 
    109: State('l', [110, 111]), 
    110: State(DELIMS['separator_delim'], end=True), # 'sol'
    
    # 'soluna'
    111: State('u', [112]), 
    112: State('n', [113]), 
    113: State('a', [114]), 
    114: State(DELIMS['separator_delim'], end=True), 
    
    # 'star'
    115: State('t', [116]), 
    116: State('a', [117]), 
    117: State('r', [118]), 
    118: State(REGDEF['free_delim'], end=True), 
    
    # --- Keyword: 'void' ---
    119: State('v', [120]), 
    120: State('o', [121]), 
    121: State('i', [122]), 
    122: State('d', [123]), 
    123: State(REGDEF['free_delim'], end=True),  
    
    # --- Keywords: 'wane', 'warp', 'wax' ---
    124: State('w', [125]), 
    125: State('a', [126, 129, 132]), 
    
    # 'wane'
    # UPDATED: Allows '}' and ';' as delimiters
    126: State('n', [127]), 
    127: State('e', [128]), 
    128: State({*DELIMS['separator_delim'], '}', ';'}, end=True),  
    
    # 'warp'
    129: State('r', [130]), 
    130: State('p', [131]), 
    131: State(DELIMS['warp_delim'], end=True),  
    
    # 'wax'
    132: State('x', [133]), 
    133: State(REGDEF['free_delim'], end=True), 
    
    # --- Keywords: 'zara', 'zeru', 'zeta' ---
    134: State('z', [135, 139]), 
    
    # 'zara'
    135: State('a', [136]), 
    136: State('r', [137]), 
    137: State('a', [138]), 
    138: State(DELIMS['zara_delim'], end=True),  
    
    # 'zeru', 'zeta'
    139: State('e', [140, 333]), 
    
    # 'zeru'
    140: State('r', [141]), 
    141: State('u', [142]), 
    142: State(DELIMS['zeru_delim'], end=True),
            
    # --- Operators & Symbols ---
    
    # +, ++, +=
    143: State('+', [144, 145, 147]), 
    144: State(DELIMS['arithmetic_delim'], end=True), # +
    145: State('+', [146]), 
    146: State(DELIMS['unary_delim'], end=True), # ++
    147: State('=', [148]), 
    148: State(DELIMS['most_symbol_delim'], end=True), # +=
    
    # -, --, -=, Negative Numbers
    149: State('-', [150, 151, 153, 215]), 
    150: State(DELIMS['minus_delim'], end=True), # -
    151: State('-', [152]), 
    152: State(DELIMS['unary_delim'], end=True), # --
    153: State('=', [154]), 
    154: State(DELIMS['most_symbol_delim'], end=True), # -=
    
    # *, *=
    155: State('*', [156, 157]), 
    156: State(DELIMS['arithmetic_delim'], end=True), # *
    157: State('=', [158]), 
    158: State(DELIMS['most_symbol_delim'], end=True), # *= 
    
    # /, /=, //
    159: State('/', [160, 161, 163]), 
    160: State(DELIMS['arithmetic_delim'], end=True), # /
    161: State('=', [162]), 
    162: State(DELIMS['most_symbol_delim'], end=True), # /=
    163: State('/', [164]), 
    164: State(DELIMS['arithmetic_delim'], end=True), # //
    
    # ^
    165: State('^', [166]),      
    166: State(DELIMS['arithmetic_delim'], end=True), 
    
    # %, %=
    167: State('%', [168, 169]), 
    168: State(DELIMS['arithmetic_delim'], end=True), # %
    169: State('=', [170]), 
    170: State(DELIMS['most_symbol_delim'], end=True), # %=
    
    # =, ==
    171: State('=', [172, 173]), 
    172: State(DELIMS['comma_equal_delim'], end=True), # =
    173: State('=', [174]), 
    174: State(DELIMS['most_symbol_delim'], end=True), # ==
    
    # !, !=
    175: State('!', [176, 177]), 
    176: State(DELIMS['not_delim'], end=True), # !
    177: State('=', [178]), 
    178: State(DELIMS['most_symbol_delim'], end=True), # !=
    
    # <, <=
    179: State('<', [180, 182]), 
    180: State(DELIMS['most_symbol_delim'], end=True), # <
    182: State('=', [183]), 
    183: State(DELIMS['most_symbol_delim'], end=True), # <=
    
    # >, >=
    184: State('>', [185, 186]), 
    185: State(DELIMS['most_symbol_delim'], end=True), # >
    186: State('=', [187]), 
    187: State(DELIMS['most_symbol_delim'], end=True), # >=
    
    # &&
    188: State('&', [189]), 
    189: State('&', [190]), 
    190: State(DELIMS['and_or_delim'], end=True), 
    
    # ||
    191: State('|', [192]), 
    192: State('|', [193]), 
    193: State(DELIMS['and_or_delim'], end=True), 
    
    # ..
    194: State('.', [195]), 
    195: State('.', [196]), 
    196: State(DELIMS['string_concat_delim'], end=True), 
    
    # #
    197: State('#', [198]), 
    198: State(DELIMS['string_length_delim'], end=True), 
    
    # Grouping Symbols: (, ), [, ], {, }
    199: State('(', [200]), 200: State(DELIMS['open_parenthesis_delim'], end=True),
    201: State(')', [202]), 202: State(DELIMS['close_parenthesis_delim'], end=True),
    203: State('[', [204]), 204: State(DELIMS['open_square_delim'], end=True),
    205: State(']', [206]), 206: State(DELIMS['close_square_delim'], end=True),
    207: State('{', [208]), 208: State(DELIMS['open_bracket_delim'], end=True),
    209: State('}', [210]), 210: State(DELIMS['close_bracket_delim'], end=True),
    
    # ,
    211: State(',', [212]), 212: State(DELIMS['comma_equal_delim'], end=True),
    
    # ;
    213: State(';', [214]), 214: State(DELIMS['semicolon_delim'], end=True),
    
    # --- Numerical Values (Integers) ---
    215: State(REGDEF['digit'], [216, 217, 245]), 
    216: State(DELIMS['float_delim'], end=True), 
    217: State(REGDEF['digit'], [218, 219, 245]), 
    218: State(DELIMS['float_delim'], end=True), 
    219: State(REGDEF['digit'], [220, 221, 245]), 
    220: State(DELIMS['float_delim'], end=True), 
    221: State(REGDEF['digit'], [222, 223, 245]), 
    222: State(DELIMS['float_delim'], end=True), 
    223: State(REGDEF['digit'], [224, 225, 245]), 
    224: State(DELIMS['float_delim'], end=True), 
    225: State(REGDEF['digit'], [226, 227, 245]), 
    226: State(DELIMS['float_delim'], end=True), 
    227: State(REGDEF['digit'], [228, 229, 245]), 
    228: State(DELIMS['float_delim'], end=True), 
    229: State(REGDEF['digit'], [230, 231, 245]), 
    230: State(DELIMS['float_delim'], end=True), 
    231: State(REGDEF['digit'], [232, 233, 245]), 
    232: State(DELIMS['float_delim'], end=True), 
    233: State(REGDEF['digit'], [234, 235, 245]), 
    234: State(DELIMS['float_delim'], end=True), 
    235: State(REGDEF['digit'], [236, 237, 245]), 
    236: State(DELIMS['float_delim'], end=True), 
    237: State(REGDEF['digit'], [238, 239, 245]), 
    238: State(DELIMS['float_delim'], end=True), 
    239: State(REGDEF['digit'], [240, 241, 245]), 
    240: State(DELIMS['float_delim'], end=True), 
    241: State(REGDEF['digit'], [242, 243, 245]), 
    242: State(DELIMS['float_delim'], end=True), 
    243: State(REGDEF['digit'], [244]), 
    244: State(DELIMS['float_delim'], end=True), 
    
    # --- Numerical Values (Floats) ---
    245: State('.', [246]),
    246: State(REGDEF['digit'], [247, 248]), 247: State(DELIMS['float_delim'], end=True), 
    248: State(REGDEF['digit'], [249, 250]), 249: State(DELIMS['float_delim'], end=True), 
    250: State(REGDEF['digit'], [251, 252]), 251: State(DELIMS['float_delim'], end=True), 
    252: State(REGDEF['digit'], [253, 254]), 253: State(DELIMS['float_delim'], end=True), 
    254: State(REGDEF['digit'], [255, 256]), 255: State(DELIMS['float_delim'], end=True), 
    256: State(REGDEF['digit'], [257, 258]), 257: State(DELIMS['float_delim'], end=True), 
    258: State(REGDEF['digit'], [259, 260]), 259: State(DELIMS['float_delim'], end=True), 
    260: State(REGDEF['digit'], [261]), 261: State(DELIMS['float_delim'], end=True), 
    
    # --- Identifiers ---
    262: State([*REGDEF['alphabet'], '_'], [263, 264]), 
    263: State(DELIMS['identifier_delim'], end=True),
    
    264: State(REGDEF['alphanumeric'], [265, 266]), 
    265: State(DELIMS['identifier_delim'], end=True),
    
    266: State(REGDEF['alphanumeric'], [267, 268]), 
    267: State(DELIMS['identifier_delim'], end=True),
    
    268: State(REGDEF['alphanumeric'], [269, 270]), 
    269: State(DELIMS['identifier_delim'], end=True),
    
    270: State(REGDEF['alphanumeric'], [271, 272]), 
    271: State(DELIMS['identifier_delim'], end=True),
    
    272: State(REGDEF['alphanumeric'], [273, 274]), 
    273: State(DELIMS['identifier_delim'], end=True),
    
    274: State(REGDEF['alphanumeric'], [275, 276]), 
    275: State(DELIMS['identifier_delim'], end=True),
    
    276: State(REGDEF['alphanumeric'], [277, 278]), 
    277: State(DELIMS['identifier_delim'], end=True),
    
    278: State(REGDEF['alphanumeric'], [279, 280]), 
    279: State(DELIMS['identifier_delim'], end=True),
    
    280: State(REGDEF['alphanumeric'], [281, 282]), 
    281: State(DELIMS['identifier_delim'], end=True),
    
    282: State(REGDEF['alphanumeric'], [283, 284]), 
    283: State(DELIMS['identifier_delim'], end=True),
    
    284: State(REGDEF['alphanumeric'], [285, 286]), 
    285: State(DELIMS['identifier_delim'], end=True),
    
    286: State(REGDEF['alphanumeric'], [287, 288]), 
    287: State(DELIMS['identifier_delim'], end=True),
    
    288: State(REGDEF['alphanumeric'], [289, 290]), 
    289: State(DELIMS['identifier_delim'], end=True),
    
    290: State(REGDEF['alphanumeric'], [291, 292]), 
    291: State(DELIMS['identifier_delim'], end=True),
    
    292: State(REGDEF['alphanumeric'], [293, 294]), 
    293: State(DELIMS['identifier_delim'], end=True),
    
    294: State(REGDEF['alphanumeric'], [295, 296]), 
    295: State(DELIMS['identifier_delim'], end=True),
    
    296: State(REGDEF['alphanumeric'], [297]), 
    297: State(DELIMS['identifier_delim'], end=True), 
    
    # --- Character Literals ---
    302: State('\'', [303, 306]), 
    303: State(REGDEF['ascii_298_302'], [304]), 
    304: State('\'', [305]), 
    305: State(DELIMS['most_data_type_delim'], end=True),
    306: State('\\', [307]), 
    307: State(REGDEF['ascii_298_302'], [304]), 
    
    # --- String Literals ---
    308: State('"', [309, 310, 312]), 
    309: State(REGDEF['ascii_298_302'], [309, 310, 312]), 
    310: State('"', [311]), 
    311: State(DELIMS['most_data_type_delim'], end=True),
    312: State('\\', [313]), 
    313: State(REGDEF['ascii'], [309, 310]),
    
    # --- Comments ---
    314: State('\\', [315, 318]), 
    315: State('\\', [316]), 
    316: State(REGDEF['ascii_no_newline'], [316, 317]), 
    317: State('\n', end=True),
    
    # Multi-line Comments
    318: State('*', [319]), 
    319: State(REGDEF['ascii_309'], [319, 320]), 
    320: State('*', [315, 320, 321]),
    321: State('\\', [322]),
    322: State(REGDEF['free_delim'], end=True), 
    
    # --- Leo Labels ---
    323: State(':', [324]), 
    324: State(':', [325]), 
    325: State([*REGDEF['alphanumeric'], '_'], [326, 330]), 
    326: State([*REGDEF['alphanumeric']], [327, 330]), 
    327: State([*REGDEF['alphanumeric']], [328, 330]), 
    328: State([*REGDEF['alphanumeric']], [329, 330]), 
    329: State([*REGDEF['alphanumeric']], [330]),      
    330: State(':', [331]), 
    331: State(':', [332]), 
    332: State(DELIMS['leo_delim'], end=True),

    # --- Zeta (Delayed) ---
    333: State('t', [334]), 
    334: State('a', [335]), 
    335: State(REGDEF['free_delim'], end=True), # 'zeta'
}

# Identifier End States for logic checking
ID_END_STATES = {
    263, 265, 267, 269, 271, 273, 275, 277, 279, 281, 
    283, 285, 287, 289, 291, 293, 295, 297, 299, 301
}