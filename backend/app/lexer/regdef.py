REGDEF = {
    #for states 307 and 310
    'ascii': {chr(i) for i in range(128)}, 

    'ascii_no_newline': {chr(i) for i in range(128) if chr(i) not in ['\n', '\0']},

    #for states 298 and 302
    'ascii_298_302': {chr(i) for i in range(128) if chr(i) not in ['\'', '"', '\n', '\\', '\0']},
    
    #for state 309
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
def ascii_except(chars: list[chr] = []):
    chars = list(chars) if type(chars) is str else chars
    ascii = REGDEF['ascii'].copy()
    for char in chars:
        ascii.remove(char)
    return ascii