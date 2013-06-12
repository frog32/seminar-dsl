from itertools import takewhile
from copy import copy
from ply import lex

from .exceptions import CompileException


class PLYCompatLexer(object):
    def __init__(self, auto_end=True, debug=False):
        self.auto_end = auto_end
        self.debug = debug
        self.lexer = lex.lex()
        self.extra_tokens = []
        self.indent_levels = ['']

    def input(self, s):
        self.lexer.input(s)

    def token(self):
        token = self.get_token()
        if self.debug:
            print token
        return token

    def get_token(self):
        if len(self.extra_tokens):
            return self.extra_tokens.pop()
        token = self.lexer.token()

        if token is None:
            # end of file
            if not self.auto_end:
                return None
            if len(self.indent_levels) <= 1:
                return None
            self.indent_levels.pop()
            token = lex.LexToken()
            token.type = 'END_BLOCK'
            token.value = ''
            token.lineno = self.lexer.lineno
            token.lexpos = len(self.lexer.lexdata)

        if token.type == 'NEWLINE':
            input_len = len(self.lexer.lexdata)
            indent_level = ''.join(self.lexer.lexdata[pos] for pos in takewhile(lambda x: self.lexer.lexdata[x] in ' \t', xrange(self.lexer.lexpos, input_len)))

            # check for mismatched indent levels
            if not self.indent_levels[-1].startswith(indent_level) and not indent_level.startswith(self.indent_levels[-1]):
                raise Exception('problem')

            last_level = len(self.indent_levels[-1])
            level = len(indent_level)
            if level > last_level:
                self.indent_levels.append(indent_level)
                start_block = copy(token)
                start_block.type = 'START_BLOCK'
                self.extra_tokens.append(start_block)
            if level < last_level:
                newline = copy(token)
                self.extra_tokens.append(newline)
                token.type = 'END_BLOCK'
                self.indent_levels.pop()

        return token


# lexer
reserved = {
    'if': 'IF',
    # 'else': 'ELSE',
    'nop': 'NOP',
    'print': 'PRINT',
    'for': 'FOR',
    'in': 'IN',
}

tokens = [
    'STRING',
    'NUMBER',
    'NAME',
    'ASSIGN',
    'DOT',
    'NEWLINE',
    'START_BLOCK',
    'END_BLOCK',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'LPAREN',
    'RPAREN',
    'LSPAREN',
    'RSPAREN',
    'COMMA'
] + list(reserved.values())

t_ASSIGN = r'=|\+=|-=|\*=|\/='
t_DOT = r'\.'
t_PLUS = r'\+'
t_MINUS = r'\-'
t_TIMES = r'\*'
t_DIVIDE = r'\/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LSPAREN = r'\['
t_RSPAREN = r'\]'
t_COMMA = r','


def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return t


def t_STRING(t):
    r'"[^"]*"'
    t.value = t.value[1:-1]
    return t


def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t


t_NAME = r'[a-z]+'


# check for reserved words
def t_RESERVED(t):
    r'if|for|in|nop|print'
    t.type = reserved.get(t.value, 'ID')
    return t


def t_error(t):
    raise CompileException(u"Cannot make sense of char: %s" % t.value[0])

t_ignore = ' \t'
