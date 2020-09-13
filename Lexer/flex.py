import ply.lex as lex
import re


class LexerClass:
    reserved = {
        'end': 'END',
        'do': 'DO',
        'if': 'IF',
        'function': 'FUNC',
        'from': 'FROM',
        'to': 'TO',
        'with': 'WITH',
        'step': 'STEP'
    }

    tokens = [
        'LOGIC', 'TCELL', 'COMP', 'COMMAND', 'INT', 'FLOAT', 'STR',
        'OPBR', 'CLBR', 'EQ', 'PLUS', 'MINUS', 'AND', 'NL',
        'OR', 'EOE', 'ANY', 'COMMA', 'MOVE'
    ] + list(reserved.values())

    t_ignore = '[ ]|\t'

    def __init__(self):
        self.lexer = lex.lex(module=self)

    def input(self, smth):
        return self.lexer.input(smth)

    def token(self):
        return self.lexer.token()

    def t_LOGIC(self, t):
        r'true|false'
        return t

    def t_TCELL(self, t):
        r'EMPTY|WALL|BOX|EXIT|UNDEF'
        return t

    def t_COMP(self, t):
        r'((all|some)[ ]+(in|less))|in|less'
        return t

    def t_COMMAND(self, t):
        r'go|pick|drop|look'
        return t

    def t_MOVE(self, t):
        r'left|right|up|down'
        return t

    def t_FLOAT(self, t):
        r'[1-9][0-9]*\.[0-9]*'
        return t

    def t_INT(self, t):
        r'[0-9]+'
        return t

    def t_STR(self, t):
        r'\_?[a-zA-Z][\w]*'
        t.type = self.reserved.get(t.value, 'STR')
        return t

    def t_OPBR(self, t):
        r'\('
        return t

    def t_CLBR(self, t):
        r'\)'
        return t

    def t_EQ(self, t):
        r'<='
        return t

    def t_PLUS(self, t):
        r'\+'
        return t

    def t_MINUS(self, t):
        r'\-'
        return t

    def t_AND(self, t):
        r'&'
        return t

    def t_OR(self, t):
        r'\|'
        return t

    def t_COMMA(self, t):
        r'\,'
        return t

    def t_NL(self, t):
        r'\n'
        t.lexer.lineno += len(t.value)
        return t

    def t_EOE(self, t):
        r'\;'
        return t

    def t_ANY(self, t):
        r'.+'
        return t

    def t_error(self, t):
        print("Illegal character '%s' " % t.value[0])
        t.lexer.skip(1)
        return t


data = '''function fU0nc
if 0 some in x(1,1,2) do function
x(1) <= 1.12
end
if 0 all less x(1,1,2) do function 
x() <= 0
from x() to x(1,1,2) with step 1 do function
x(1) <= x(1) + x(1)
end
x(1,1,2) <= x(1,1,2) - 1
do func
end
x(1)
end
function main
x(1) <= 0
x(1,1,2) <= 41
do func;
end
0123
look down
'''

