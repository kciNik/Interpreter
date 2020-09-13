import sys
from SyntaxTree.Tree import SyntaxTreeNode


class Error_handler:
    def __init__(self):
        self.type = None
        self.node = None
        self.types = ['UnexpectedError',
                      'NoStartPoint',
                      'UndeclaredError',
                      'IndexError',
                      'FuncCallError',
                      'ValueError',
                      'ApplicationCall',
                      'TypeError']

    def up(self, err_type, node=None):
        self.type = err_type
        self.node = node
        sys.stderr.write(f'Error {self.types[int(err_type)]}: ')
        if self.type == 0:
            sys.stderr.write(f' incorrect syntax at '
                             f'{self.node.children[0].lineno} line \n')
            return
        elif self.type == 1:
            sys.stderr.write(f'No "main" function detected\n')
            return
        elif self.type == 2:
            if node.type == 'assignment':
                sys.stderr.write(f'Variable for assignment at line '
                                 f'{self.node.children[1].lineno} is used before declaration\n')
            elif node.type == 'from':
                sys.stderr.write(f'Variable for cycle at line '
                                 f'{self.node.lineno} is used before declaration\n')
            elif node.type == 'if':
                sys.stderr.write(f'Variable for condition if at line '
                                 f'{self.node.lineno} is used before declaration\n')
        elif self.type == 3:
            sys.stderr.write(f'Variable index at line '
                             f'{self.node.lineno} is used before declaration\n')
        elif self.type == 4:
            sys.stderr.write(f'Unknown function call "{self.node.children.value}" at line '
                             f'{self.node.lineno} \n')
        elif self.type == 5:
            if node.type == 'assignment':
                sys.stderr.write(f'Bad value for variable "{self.node.children[0].value}" at line '
                                 f'{self.node.value.lineno} \n')
        elif self.type == 6:
            sys.stderr.write(f'Tried to call main function at line'
                             f' {self.node.lineno} \n')
        elif self.type == 7:
            if node.type == 'assignment':
                sys.stderr.write(f'Bad values at assignment "{self.node.children[1].value}" at line '
                                 f'{self.node.children[1].lineno}\n')
            if node.type == 'from':
                sys.stderr.write(f'Type of variables in cycle "{self.node.value}" at line '
                                 f'{self.node.lineno} do not match\n')
            if node.type == 'if':
                sys.stderr.write(f'Type of variables in condition "{self.node.value}" at line '
                                 f'{self.node.lineno} do not match\n')


class Exit(Exception):
    pass


class InterpreterFuncCallError(Exception):
    pass


class InterpreterNameError(Exception):
    pass


class InterpreterVarError(Exception):
    pass


class InterpreterIndexError(Exception):
    pass


class InterpreterValueError(Exception):
    pass


class InterpreterApplicationCall(Exception):
    pass


class InterpreterTypeError(Exception):
    pass
