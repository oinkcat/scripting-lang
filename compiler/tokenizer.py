""" Lexer """
import re
import compatibility

# Tokens
TOKEN_NAMES = [
    'T_STRING', 'T_DOT', 'T_COMMA', 'T_HASHKEY', 'T_NUMBER',
    'T_MATHASSIGN',
    'T_ADD', 'T_MUL', 'T_CMP', 'T_ASSIGN', 'T_CONCAT', 
    'T_LBR', 'T_RBR', 'T_LSBR', 'T_RSBR', 'T_LCBR', 'T_RCBR',
    'T_SPACE', 'T_COMMENT', 'T_IDENT', 'T_NOT',
    'T_IF', 'T_ELSEIF', 'T_ELSE', 'T_FOR',
    'T_BREAK', 'T_CONTINUE',
    'T_FUNC', 'T_RETURN', 'T_END', 'T_USE',
    'T_IMPORT', 'T_NATIVE',
    'T_EMIT', 'T_AS', 'T_LOGIC',
    'T_FUNCREF', 'T_NEW'
]

# Special token values
T_EOL = 100
T_EOF = -1

# Evaluate token names
for idx, name in enumerate(TOKEN_NAMES):
    exec('%s = %d' % (name, idx))


def get_token_name(value):
    """ Get token name by it's value """

    special = { T_EOF: 'T_EOF', T_EOL: 'T_EOL' }

    if value not in special:
        return TOKEN_NAMES[value]
    else:
        return special[value]

class InvalidSequence(Exception):
    """ Invalid sequence on input """
    
    def __init__(self, line_num, line, seq):
        args = (seq, line_num, line)
        msg = "Invalid sequence on input: %s\nLine: %d, %s" % args
        Exception.__init__(self, msg)

class Tokenizer:
    """ Performs string tokenization """

    # Complex templates
    TMPL_MAIN = '("[^"]*")|(\.)|(,)|' + \
                '([0-9a-z_]+:)|' + \
                '([0-9]+(?:\.[0-9]+)?)|' + \
                '(\+=|-=|\*=|/=|%=)|' + \
                '([+\-])|([*/%])|' + \
                '(<=|>=|<|>|==|!=)|' + \
                '(=)|(&)|' + \
                '(\()|(\))|(\[)|(\])|(\{)|(\})|' + \
                '(\s+)|(#.+$)|' + \
                '([$_a-z][_0-9a-z]*)'
                
    # Simple literal templates
    TMPL_WORD = '(not)|' + \
                '(if)|(elsif)|(else)|(for)|' + \
                '(break)|(continue)|' + \
                '(func)|(return)|(end)|(use)|(import)|(native)|' + \
                '(emit)|(as)|' + \
                '(or|and|xor)|' + \
                '(ref)|(new)'

    # Substitution pattern for string interpolation
    TMPL_STRING_SUB = '\$\{[^}]+\}'

    def __init__(self, source):
        self.re_main = re.compile(Tokenizer.TMPL_MAIN, re.IGNORECASE)
        self.re_word = re.compile(Tokenizer.TMPL_WORD, re.IGNORECASE)
        self.re_sub = re.compile(Tokenizer.TMPL_STRING_SUB)
        self.gen = self.tokenize(source)
        # Current token information
        self.t_type = None
        self.t_val = None
        self.line_number = 0
        self.line = None
        self.retry = False

    def hold(self):
        """ Tell tokenizer to retry current token later """
        self.retry = True
        
    def next(self):
        """ Get next token """
        
        if not self.retry:
            try:
                token = compatibility.gen_next(self.gen)
                self.t_type, self.t_val = token
            except StopIteration:
                pass
        
        else:
            self.retry = False
            
    def tokenize(self, lines):
        """ Tokenize source lines """
        
        for num, line in enumerate(lines):
            self.line_number = num + 1
            self.line = line
            for token in self.tokenize_line(line):
                yield token
        
        yield (T_EOF, None)
        

    def interpolate_string(self, string):
        """ Transform string that contains substitution tokens """

        def expander(match):
            return '" & (%s) & "' % match.group()[2: -1]

        transformed_str = re.sub(self.re_sub, expander, string)

        if string != transformed_str:
            inner_expr = transformed_str
            if transformed_str.startswith('"" & '):
                inner_expr = transformed_str[4:]
            if transformed_str.endswith(' & ""'):
                inner_expr = transformed_str[0:-5]
            return self.tokenize_line(inner_expr, True)
        else:
            return None


    def tokenize_line(self, line, in_string=False):
        """ Get tokens from one source line """
    
        SKIP_TOKENS = {T_SPACE, T_COMMENT}
    
        prev_end = 0
        for t in self.re_main.finditer(line):
            # Check match position
            if t.start() - prev_end > 0:
                seq = line[prev_end : t.start()]
                raise InvalidSequence(self.line_number, line, seq)
            
            tok_idx = None
            tok_val = None
            matched_groups = t.groups()
            
            # Check matching token
            for idx, val in enumerate(matched_groups):
                if not (val is None or idx in SKIP_TOKENS):
                    tok_idx, tok_val = idx, val
                    break
            
            if tok_idx is not None:
                # Check if keyword matched
                if tok_idx == T_IDENT:
                    word_matches = self.re_word.findall(tok_val)
                    if len(word_matches) > 0:
                        matches = word_matches[0]
                        for i in compatibility.num_range(0, len(matches)):
                            if tok_val == matches[i]:
                                tok_idx += i + 1
                                break
                
                # Try interpolate expressions in string
                if (not in_string) and (tok_idx == T_STRING):
                    interpolator = self.interpolate_string(tok_val)
                    if interpolator != None:
                        for inner_token in interpolator:
                            if inner_token[0] != T_EOL:
                                yield inner_token
                    else:
                        yield (tok_idx, tok_val)
                else:
                    yield (tok_idx, tok_val)
            
            prev_end = t.end()

        if prev_end != len(line):
            raise Exception("Unexpected sequence at end!")
        
        yield (T_EOL, None)