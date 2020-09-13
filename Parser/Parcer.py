import os
import sys

from ply.lex import LexError
from Lexer.flex import LexerClass
from SyntaxTree.Tree import SyntaxTreeNode
import ply.yacc as yacc

class ParserClass(object):
    tokens = LexerClass.tokens

    def __init__(self):
        self.lexer = LexerClass()
        self.parser = yacc.yacc(module=self)
        self.functions = dict()
        self.ok = True

    def parse(self, t):
        try:
            res = self.parser.parse(t)
            return res, self.functions, self.ok
        except LexError:
            sys.stderr.write(f'Illegal token {t}\n')

    def p_program(self, p):
        """program : statements"""
        p[0] = SyntaxTreeNode('program', children=p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))

    def p_statements(self, p):
        """statements : statements statement
                     | statement"""
        if len(p) == 2:
            p[0] = SyntaxTreeNode('stmt_list', children=[p[1]])
        else:
            p[0] = SyntaxTreeNode('stmt_list', children=[p[1], p[2]])

    def p_statement(self, p):
        """statement : assignment eoe
                     | from eoe
                     | var_const eoe
                     | if eoe
                     | function eoe
                     | call_func eoe
                     | commands eoe"""
        p[0] = p[1]

    def p_commands(self, p):
        """commands : COMMAND MOVE"""
        p[2] = SyntaxTreeNode('robot_move', p[2], lineno=p.lineno(1), lexpos=p.lexpos(1))
        p[0] = SyntaxTreeNode('robot_com', p[1], children=p[2], lineno=p.lineno(1), lexpos=p.lexpos(1))

    def p_eoe(self, p):
        """eoe : NL
               | EOE
               | EOE NL"""
        p[0] = p[1]

    def p_assignment(self, p):
        """assignment : variable EQ expression"""
        p[0] = SyntaxTreeNode('assignment', value=p[2], children=[p[1], p[3]], lineno=p.lineno(1), lexpos=p.lexpos(1))

    def p_assigmnent_error(self, p):
        """assignment : variable EQ error"""
        p[0] = SyntaxTreeNode('assign_error', value="Wrong assign", children=p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))
        sys.stderr.write(f'>>> Wrong from\n')

    def p_variable(self, p):
        """variable : STR index
                   | STR OPBR index CLBR"""
        if len(p) == 3:
            p[0] = SyntaxTreeNode('var', value=p[1], children=p[2], lineno=p.lineno(1), lexpos=p.lexpos(1))
        else:
            #p[2] = SyntaxTreeNode('bracket', value=p[2], lineno=p.lineno(2), lexpos=p.lexpos(2))
            #p[4] = SyntaxTreeNode('bracket', value=p[4], lineno=p.lineno(4), lexpos=p.lexpos(4))
            p[0] = SyntaxTreeNode('variable', value=p[1], children=p[3], lineno=p.lineno(1), lexpos=p.lexpos(1))

    def p_index(self, p):
        """index :
                 | index COMMA INT
                 | INT"""
        if len(p) == 1:
            p[0] = SyntaxTreeNode('zero_index')
        elif len(p) == 4:
            p[3] = SyntaxTreeNode('index', value=p[3], lineno=p.lineno(3), lexpos=p.lexpos(3))
            p[0] = SyntaxTreeNode('list_index', children=[p[1], p[3]], lineno=p.lineno(3), lexpos=p.lexpos(3))
        else:
            p[0] = SyntaxTreeNode('index', value=p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))

    def p_expression(self, p):
        """expression : var_const
                      | operation
                      | un_operation
                      | call_func
                      | commands
                      | logic_oper"""
        p[0] = p[1]

    def p_var_const(self, p):
        """var_const : variable
                     | const"""
        p[0] = p[1]

    def p_const(self, p):
        """const : INT
                 | FLOAT
                 | LOGIC
                 | TCELL"""
        p[0] = SyntaxTreeNode('const', value=p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))

    def p_operation(self, p):
        """operation : expression PLUS expression
                     | expression MINUS expression"""
        p[0] = SyntaxTreeNode('operation', value=p[2], children=[p[1], p[3]], lineno=p.lineno(2), lexpos=p.lexpos(2))

    def p_un_operation(self, p):
        """un_operation : MINUS expression"""
        p[0] = SyntaxTreeNode('un_operation', value=p[1], children=p[2], lineno=p.lineno(1), lexpos=p.lexpos(1))

    def p_from(self, p):
        """from : FROM expression TO expression DO FUNC NL statements END
                | FROM expression TO expression call_func
                | FROM expression TO expression WITH STEP expression DO FUNC NL statements END
                | FROM expression TO expression WITH STEP expression call_func"""
        if len(p) == 10:
            p[0] = SyntaxTreeNode('from_cycle', children={'from': p[2], 'to': p[4], 'body': p[8]},
                                  lineno=p.lineno(1), lexpos=p.lexpos(1))
        elif len(p) == 6:
            p[0] = SyntaxTreeNode('from_cycle', children={'from': p[2], 'to': p[4], 'body': p[5]},
                                  lineno=p.lineno(1), lexpos=p.lexpos(1))
        elif len(p) == 13:
            p[0] = SyntaxTreeNode('from_cycle_wh', children={'from': p[2], 'to': p[4], 'body': p[11], 'with_step': p[7]},
                                  lineno=p.lineno(1), lexpos=p.lexpos(1))
        else:
            p[0] = SyntaxTreeNode('from_cycle_wh', children={'from': p[2], 'to': p[4], 'body': p[8], 'with_step': p[7]},
                                  lineno=p.lineno(1), lexpos=p.lexpos(1))

    def p_from_error(self, p):
        """from : FROM expression TO expression WITH STEP expression DO FUNC error statements END
                | FROM expression TO expression DO FUNC error statements END
                | FROM expression error expression WITH STEP expression DO FUNC NL statements END
                | FROM expression error expression DO FUNC NL statements END
                | FROM expression TO expression WITH STEP expression DO error NL statements END
                | FROM expression TO expression DO error NL statements END
                | FROM expression TO expression error FUNC NL statements END
                | FROM expression TO expression WITH STEP expression error FUNC NL statements END"""
        if len(p) == 10:
            p[0] = SyntaxTreeNode('error', value="Wrong from", children=p[2], lineno=p.lineno(1), lexpos=p.lexpos(1))
        else:
            p[0] = SyntaxTreeNode('error', value="Wrong from", children=p[2], lineno=p.lineno(1), lexpos=p.lexpos(1))
        sys.stderr.write(f'>>> Wrong from\n')

    def p_call_func(self, p):
        """call_func : DO STR"""
        p[2] = SyntaxTreeNode('name_func', value=p[2], lineno=p.lineno(1), lexpos=p.lexpos(1))
        p[0] = SyntaxTreeNode('call_func', value=p[1], children=p[2], lineno=p.lineno(1), lexpos=p.lexpos(1))

    def p_if(self, p):
        """if : IF expression call_func
              | IF expression DO FUNC NL statements END"""
        if len(p) == 4:
            p[0] = SyntaxTreeNode('if', p[1], children=[p[2], p[3]], lineno=p.lineno(1), lexpos=p.lexpos(1))
        else:
            p[0] = SyntaxTreeNode('if', p[1], children=[p[2], p[6]], lineno=p.lineno(1), lexpos=p.lexpos(1))

    def p_if_error(self, p):
        """if : IF expression DO FUNC error statements END
              | IF expression DO error NL statements END
              | IF error DO FUNC NL statements END
              | IF error call_func
              | IF expression error FUNC NL statements END"""
        if len(p) == 4:
            p[0] = SyntaxTreeNode('error', value="Wrong if", children=p[3], lineno=p.lineno(1), lexpos=p.lexpos(1))
        else:
            p[0] = SyntaxTreeNode('error', value="Wrong if", children=p[2], lineno=p.lineno(1), lexpos=p.lexpos(1))
        sys.stderr.write(f'>>> Wrong if\n')

    def p_logic_oper(self, p):
        """logic_oper : expression AND expression
                      | expression OR expression
                      | var_const COMP variable
                      | variable"""
        if len(p) == 4:
            p[0] = SyntaxTreeNode('logic_oper', p[2], children=[p[1], p[3]], lineno=p.lineno(1), lexpos=p.lexpos(1))
        else:
            p[0] = SyntaxTreeNode('logic_var', p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))

    def p_function(self, p):
        """function : FUNC STR NL statements END"""
        p[0] = SyntaxTreeNode('function', str(p[2]), children={'body': p[4]}, lineno=p.lineno(1),
                              lexpos=p.lexpos(1))
        self.functions[p[2]] = p[0]

    def p_function_error(self, p):
        """function : FUNC STR error statements END
                    | error STR NL statements END"""
        p[2] = SyntaxTreeNode('error_func', p[2], lineno=p.lineno(1), lexpos=p.lexpos(1))
        p[0] = SyntaxTreeNode('error', value="Wrong function", children=p[2], lineno=p.lineno(1), lexpos=p.lexpos(1))
        sys.stderr.write(f'>>> Wrong function\n')

    def p_error(self, p):
        try:
            sys.stderr.write(f'Syntax error at {p.lineno} line\n')
        except Exception:
            sys.stderr.write(f'Syntax error\n')
        self.ok = False

if __name__ == '__main__':
    parser = ParserClass()
    a = os.getcwd().split('/')
    del a[len(a) - 1]
    s = '/'.join(a)
    s += 'tests.txt'
    f = open(s, 'r')
    txt = f.read()
    f.close()
    print(f'INPUT: {txt}')
    #tree, func_table, ok = parser.parse(txt)
    tree = parser.parser.parse(txt, debug=True)
    tree.print()
