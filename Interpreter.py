import sys
from Parser.Parcer import ParserClass
from SyntaxTree.Tree import SyntaxTreeNode
from Errors.Errors import Error_handler
from Errors.Errors import InterpreterApplicationCall
from Errors.Errors import InterpreterIndexError
from Errors.Errors import InterpreterNameError
from Errors.Errors import InterpreterValueError
from Errors.Errors import InterpreterTypeError
from Errors.Errors import InterpreterVarError
from Errors.Errors import InterpreterFuncCallError
from Robot.Robot import Robot, Cell, cells
from Errors.Errors import Exit


class Variable:
    def __init__(self, var_value, var_index):
        self.index = var_index
        if isinstance(var_value, bool):
            self.type = 'bool'
            self.value = var_value
        elif var_value == 'EMPTY' or var_value == 'WALL' or var_value == 'BOX' or var_value == 'EXIT' or var_value == 'UNDEF':
            self.type = 'cell'
            self.value = var_value
        elif isinstance(var_value, int):
            self.type = 'int'
            self.value = var_value

    def __repr__(self):
        return f'{self.type} {self.index} {self.value}'

class TypeConverter:
    def __init__(self):
        pass

    def converse(self, type, var, index):
        if type == var.type:
            return var
        elif type == 'bool':
            if var.type == 'int':
                return self.int_to_bool(var, index)
            elif var.type == 'cell':
                return self.cell_to_bool(var, index)
        elif type == 'int':
            if var.type == 'bool':
                return self.bool_to_int(var, index)
        elif type == 'cell':
            if var.type == 'bool':
                return self.bool_to_cell(var, index)
        elif type.find(var.type) != -1:
            return Variable(var.value, index)

    @staticmethod
    def cell_to_bool(var, index):
        if var.value == 'empty' or var.value == 'wall' or var.value == 'box' or var.value == 'exit':
            return Variable(True, index)
        elif var.value == 'undef':
            return Variable(False, index)

    @staticmethod
    def bool_to_cell(var, index):
        if not var.value:
            return Variable('undef', index)

    @staticmethod
    def int_to_bool(var, index):
        if var.value == 0:
            return Variable(False, index)
        else:
            return Variable(True, index)

    @staticmethod
    def bool_to_int(var, index):
        if var.value:
            return Variable(1, index)
        else:
            return Variable(0, index)


class Interpreter:
    def __init__(self, parser=ParserClass(), converter=TypeConverter()):
        self.parser = parser
        self.converter = converter
        self.map = None
        self.program = None
        self.symbol_table = [dict()]
        self.scope = 0
        self.tree = None
        self.functions = None
        self.robot = None
        self.exit_found = False
        self.error = Error_handler()
        self.error_types = {'UnexpectedError': 0,
                            'NoStartPoint': 1,
                            'UndeclaredError': 2,
                            'IndexError': 3,
                            'FuncCallError': 4,
                            'ValueError': 5,
                            'ApplicationCall': 6,
                            'TypeError': 7}

    def interpreter(self, program=None, robot=None):
        self.robot = robot
        self.program = program
        self.symbol_table = [dict()]
        self.tree, self.functions, _correct = self.parser.parse(self.program)
        if _correct:
            if 'main' not in self.functions.keys():
                print(self.error.up(self.error_types['NoStartPoint']))
                return
            self.interpreter_tree(self.tree)
            try:
                self.interpreter_node(self.functions['main'].children['body'])
                return True
            except RecursionError:
                sys.stderr.write(f'RecursionError: function calls itself too many times\n')
                sys.stderr.write("========= Program has finished with fatal error =========\n")
                return False
            except Exit:
                return True
        else:
            sys.stderr.write(f'Can\'t interpretate incorrect input file\n')

    def interpreter_tree(self, tree):
        print("Program tree:\n")
        tree.print()
        print("\n")

    def interpreter_node(self, node):
        if self.exit_found:
            raise Exit
        if node is None:
            return ''
        elif node.type == 'program':
            self.interpreter_node(node.children)
        elif node.type == 'stmt_list':
            for ch in node.children:
                self.interpreter_node(ch)
        elif node.type == 'assignment':
            var = node.children[0].value  # variable.value(name of var)
            tmp_index = self.list_of_ind(node.children[0])
            if self.scope == 0:
                if var not in self.symbol_table[self.scope].keys():
                    if node.children[0].type == 'variable':
                        self.symbol_table[self.scope][var] = [
                            Variable(self.interpreter_node(node.children[1]), tmp_index), ]
                    elif node.children[0].type == 'var' and node.children[1].type == 'var':
                        self.symbol_table[self.scope][var] = self.interpreter_node(node.children[1])
                    elif node.children[0].type == 'var' and isinstance(self.interpreter_node(node.children[1]), list):
                        v = self.interpreter_node(node.children[1])
                        j = [0, ]
                        for i in v:
                            self.symbol_table[self.scope][var] = [Variable(i, tuple(j)), ]
                            j = list(j)
                            j[0] += 1
                else:
                    if node.children[0].type == 'variable':
                        sch = False
                        amount = 0
                        for count in self.symbol_table[self.scope][var]:
                            if tmp_index == count.index:
                                sch = True
                                amount = count
                        if sch:
                            try:
                                amount.value = self.interpreter_node(node.children[1])
                            except InterpreterNameError:
                                self.error.up(self.error_types['UndeclaredError'], node)
                            except InterpreterIndexError:
                                self.error.up(self.error_types['IndexError'], node)
                            except InterpreterTypeError:
                                self.error.up(self.error_types['TypeError'], node)
                        else:
                            try:
                                self.add_in_tab(Variable(self.interpreter_node(node.children[1]), tmp_index), var)
                            except InterpreterNameError:
                                self.error.up(self.error_types['UndeclaredError'], node)
                            except InterpreterIndexError:
                                self.error.up(self.error_types['IndexError'], node)
                            except InterpreterTypeError:
                                self.error.up(self.error_types['TypeError'], node)
                    elif node.children[0].type == 'var' and node.children[1].type == 'var':
                        self.symbol_table[self.scope][var] = self.interpreter_node(node.children[1])
                    elif node.children[0].type == 'var' and isinstance(self.interpreter_node(node.children[1]), list):
                        v = self.interpreter_node(node.children[1])
                        j = [0, ]
                        for i in v:
                            self.symbol_table[self.scope][var].append(Variable(i, tuple(j)))
                            j = list(j)
                            j[0] += 1
            else:
                if node.children[0]. type == 'variable':
                    counter = 0
                    flag = False
                    sch = False
                    amount = 0
                    while counter <= self.scope:
                        if var in self.symbol_table[counter].keys():
                            for count in self.symbol_table[counter][var]:
                                if tmp_index == count.index:
                                    flag = True
                                    amount = count
                                    break
                            if flag:
                                try:
                                    amount.value = self.interpreter_node(node.children[1])
                                except InterpreterNameError:
                                    self.error.up(self.error_types['UndeclaredError'], node)
                                except InterpreterIndexError:
                                    self.error.up(self.error_types['IndexError'], node)
                                except InterpreterTypeError:
                                    self.error.up(self.error_types['TypeError'], node)
                                sch = True
                                break
                        counter += 1
                    if not sch:
                        if var not in self.symbol_table[self.scope].keys():
                            self.symbol_table[self.scope][var] = [
                                Variable(self.interpreter_node(node.children[1]), tmp_index), ]
                        else:
                            try:
                                self.add_in_tab(Variable(self.interpreter_node(node.children[1]), tmp_index), var)
                            except InterpreterNameError:
                                self.error.up(self.error_types['UndeclaredError'], node)
                            except InterpreterIndexError:
                                self.error.up(self.error_types['IndexError'], node)
                            except InterpreterTypeError:
                                self.error.up(self.error_types['TypeError'], node)
                elif node.children[0].type == 'var':
                    c = 0
                    v = self.interpreter_node(node.children[1])
                    flag = False
                    while c <= self.scope:
                        if var in self.symbol_table[c].keys():
                            flag = True
                            j = [0, ]
                            self.symbol_table[c][var].clear()
                            for i in v:
                                self.symbol_table[c][var].append(Variable(i, tuple(j)))
                                j = list(j)
                                j[0] += 1
                        c += 1
                    if not flag:
                        j = [0, ]
                        self.symbol_table[self.scope][var] = list()
                        for i in v:
                            self.symbol_table[self.scope][var].append(Variable(i, tuple(j)))
                            j = list(j)
                            j[0] += 1
        elif node.type == 'variable':
            if self.scope == 0:
                flag = False
                if node.value in self.symbol_table[self.scope].keys():
                    tmp = self.list_of_ind(node)
                    for count in self.symbol_table[self.scope][node.value]:
                        if tmp == count.index:
                            flag = True
                            return count.value
                else:
                    raise InterpreterNameError
                if not flag:
                    raise InterpreterIndexError
            else:
                c = 0
                flag = False
                fl = False
                while c <= self.scope:
                    if node.value in self.symbol_table[c].keys():
                        fl = True
                        tmp = self.list_of_ind(node)
                        for count in self.symbol_table[c][node.value]:
                            if tmp == count.index:
                                flag = True
                                return count.value
                    c += 1
                if not fl:
                    raise InterpreterNameError
                if not flag:
                    raise InterpreterIndexError
        elif node.type == 'var':
            if self.scope == 0:
                if node.value in self.symbol_table[self.scope].keys():
                    return self.symbol_table[self.scope][node.value]
                else:
                    raise InterpreterNameError
            else:
                c = self.scope
                while c >= 0:
                    if node.value in self.symbol_table[c].keys():
                        return self.symbol_table[c][node.value]
                    c -= 1
                raise InterpreterNameError
        elif node.type == 'const':
            try:
                tmp = float(node.value)
            except Exception:
                if node.value == 'true':
                    tmp = True
                elif node.value == 'false':
                    tmp = False
                else:
                    try:
                        tmp = int(node.value)
                    except Exception:
                        return node.value
                return tmp
            else:
                return int(tmp)
        elif node.type == 'operation':
            if node.value == '+':
                var1 = self.interpreter_node(node.children[0])
                var2 = self.interpreter_node(node.children[1])
                if isinstance(var1, int) and isinstance(var2, int):
                    return var1 + var2
                else:
                    raise InterpreterTypeError
            elif node.value == '-':
                var1 = self.interpreter_node(node.children[0])
                var2 = self.interpreter_node(node.children[1])
                if isinstance(var1, int) and isinstance(var2, int):
                    return var1 - var2
                else:
                    raise InterpreterTypeError
        elif node.type == 'un_operation':
            var = self.interpreter_node(node.children)
            if isinstance(var, bool):
                if not var:
                    return True
                else:
                    return False
            elif isinstance(var, int):
                return -var
            else:
                raise InterpreterTypeError
        elif node.type == 'logic_oper':
            if node.value == '&':
                return self.interpreter_node(node.children[0]) and self.interpreter_node(node.children[1])
            elif node.value == '|':
                if node.children[0].type == 'variable' and node.children[1].type == 'variable':
                    return self.interpreter_node(node.children[0]) | self.interpreter_node(node.children[1])
            elif node.value == 'in':
                if (node.children[0].type == 'variable' or node.children[0].type == 'const') and node.children[1].type == 'variable':
                    if self.interpreter_node(node.children[0]) == self.interpreter_node(node.children[1]):
                        return True
                    else:
                        return False
                elif (node.children[0].type == 'variable' or node.children[0].type == 'const') and node.children[1].type == 'var':
                    for count in self.symbol_table[0][node.children[1].value]:
                        if self.interpreter_node(node.children[0]) == count.value:
                            return True
                    return False
            elif node.value == 'all in':
                if node.children[0].type == 'var' and node.children[1].type == 'var':
                    sch = 0
                    for count1 in self.symbol_table[self.scope][node.children[0].value]:
                        for count2 in self.symbol_table[self.scope][node.children[1].value]:
                            if count1.value == count2.value:
                                sch += 1
                                break
                    if sch == len(self.symbol_table[self.scope][node.children[0].value]):
                        return True
                    else:
                        return False
                else:
                    raise InterpreterVarError
            elif node.value == 'some in':
                if node.children[0].type == 'var' and node.children[1].type == 'var':
                    sch = 0
                    for count1 in self.symbol_table[self.scope][node.children[0].value]:
                        for count2 in self.symbol_table[self.scope][node.children[1].value]:
                            if count1.value == count2.value:
                                sch += 1
                                break
                    if sch > 0:
                        return True
                    else:
                        return False
                else:
                    raise InterpreterVarError
            elif node.value == 'less':
                if (node.children[0].type == 'variable' or node.children[0].type == 'const') and node.children[1].type == 'variable':
                    if self.interpreter_node(node.children[0]) < self.interpreter_node(node.children[1]):
                        return True
                    else:
                        return False
                elif (node.children[0].type == 'variable' or node.children[0].type == 'const') and node.children[1].type == 'var':
                    sch = 0
                    for count in self.symbol_table[self.scope][node.children[1].value]:
                        if self.interpreter_node(node.children[0]) < count.value:
                            sch += 1
                    if sch == len(self.symbol_table[self.scope][node.children[1].value]):
                        return True
                    else:
                        return False
            elif node.value == 'all less':
                if node.children[0].type == 'var' and node.children[1].type == 'var':
                    sch = 0
                    for count1 in self.symbol_table[self.scope][node.children[0].value]:
                        for count2 in self.symbol_table[self.scope][node.children[1].value]:
                            if count1.value > count2.value:
                                sch += 1
                                break
                    if sch > 0:
                        return False
                    else:
                        return True
                else:
                    raise InterpreterVarError
            elif node.value == 'some less':
                if node.children[0].type == 'var' and node.children[1].type == 'var':
                    sch = 0
                    for count1 in self.symbol_table[self.scope][node.children[0].value]:
                        for count2 in self.symbol_table[self.scope][node.children[1].value]:
                            if count1.value > count2.value:
                                sch += 1
                                break
                    if sch == len(self.symbol_table[self.scope][node.children[0].value]):
                        return False
                    else:
                        return True
                else:
                    raise InterpreterVarError
            elif node.value.type == 'variable':
                var = self.interpreter_node(node.value)
                if var == 0:
                    return False
                else:
                    return True
        elif node.type == 'if':
            cond = False
            try:
                cond = self.interpreter_node(node.children[0])
            except InterpreterVarError:
                self.error.up(self.error_types['TypeError'], node)
            except InterpreterNameError:
                self.error.up(self.error_types['UndeclaredError'], node)
            except InterpreterIndexError:
                self.error.up(self.error_types['IndexError'], node)
            if cond:
                self.interpreter_node(node.children[1])
        elif node.type == 'from_cycle':
            try:
                self.op_from(node)
            except InterpreterNameError:
                self.error.up(self.error_types['UndeclaredError'], node)
            except InterpreterIndexError:
                self.error.up(self.error_types['IndexError'], node)
            except InterpreterTypeError:
                self.error.up(self.error_types['TypeError'], node)
        elif node.type == 'from_cycle_wh':
            try:
                self.op_from(node)
            except InterpreterNameError:
                self.error.up(self.error_types['UndeclaredError'], node)
            except InterpreterIndexError:
                self.error.up(self.error_types['IndexError'], node)
            except InterpreterTypeError:
                self.error.up(self.error_types['TypeError'], node)
        elif node.type == 'call_func':
            try:
                return self.function_call(node)
            except InterpreterApplicationCall:
                self.error.up(self.error_types['ApplicationCall'], node)
            except InterpreterFuncCallError:
                self.error.up(self.error_types['FuncCallError'], node)
        elif node.type == 'function':
            pass
        elif node.type =='robot_com':
            self.exit_found = self.robot.exit()
            if self.exit_found:
                raise Exit
            if node.value == 'go':
                res = self.go(node.children)
            elif node.value == 'pick':
                res = self.pick(node.children)
            elif node.value == 'drop':
                res = self.drop(node.children)
            else:
                res = self.look(node.children)
            return res

    def add_in_tab(self, var, name):
        if self.symbol_table[self.scope][name][0].type == var.type:
            self.symbol_table[self.scope][name].append(var)
        else:
            raise InterpreterTypeError

    def list_of_ind(self, node):
        tmp_index = list()
        child = node.children  # index
        if child.type == 'zero_index':
            tmp_index.append(0)
        elif child.type == 'index':
            tmp_index.append(int(child.value))
        else:
            child = child.children
            while child[0].type != 'index':
                tmp_index.append(int(child[1].value))
                child = child[0].children
            tmp_index.append(int(child[1].value))
            tmp_index.append(int(child[0].value))
            tmp_index.reverse()
        return tuple(tmp_index)

    def op_from(self, node):
        if node.type == 'from_cycle':
            if node.children['from'].type == 'variable' and node.children['to'].type == 'variable':
                f = node.children['from']
                t = self.interpreter_node(node.children['to'])
                ind1 = self.list_of_ind(f)
                a1 = 0
                for i in range(len(self.symbol_table[self.scope][f.value])):
                    if ind1 == self.symbol_table[self.scope][f.value][i].index:
                        while self.symbol_table[self.scope][f.value][i].value < t:
                            self.interpreter_node(node.children['body'])
        else:
            f = self.interpreter_node(node.children['from'])
            t = self.interpreter_node(node.children['to'])
            if not (isinstance(f, int) and isinstance(t, int)):
                raise InterpreterTypeError
            step = self.interpreter_node(node.children['with_step'])
            if not isinstance(step, int):
                raise InterpreterTypeError
            if step > 0:
                while f < t:
                    self.interpreter_node(node.children['body'])
                    f += step
            elif step < 0:
                while f > t:
                    self.interpreter_node(node.children['body'])
                    f += step

    def check_index(self, node):
        index = self.list_of_ind(node)
        for count in self.symbol_table[self.scope][node.value]:
            if index == count.index:
                return True
        return False

    def function_call(self, node):
        if node.children.value == 'main':
            raise InterpreterApplicationCall
        if node.children.value in self.functions.keys():
            self.scope += 1
            if self.scope > 1000:
                self.scope -= 1
                raise RecursionError from None
            self.symbol_table.append(dict())
            body = self.functions[node.children.value].children['body']
            self.interpreter_node(body)
            if body.children[1] == 'variable' or body.children[1] == 'var' or body.children[1] == 'const':
                var = self.interpreter_node(body.children[1])
                self.scope -= 1
                self.symbol_table.pop()
                return var
            else:
                self.scope -= 1
                self.symbol_table.pop()
        else:
            raise InterpreterFuncCallError

    def go(self, children):
        self.exit_found = self.robot.exit()
        if not self.exit_found:
            return self.robot.go(children.value)

    def pick(self, children):
        return self.robot.pick(children.value)

    def drop(self, children):
        return self.robot.drop(children.value)

    def look(self, children):
        self.exit_found = self.robot.exit()
        if not self.exit_found:
            return self.robot.look(children.value)

    def exit(self):
        result = self.robot.exit()
        if result:
            self.exit_found = True
        return result


def make_robot(descriptor):
    with open(descriptor) as file:
        info = file.read()
    info = info.split('\n')
    map_size = info.pop(0).split()
    robot_coordinates = info.pop(0).split()
    x = int(robot_coordinates[0])
    y = int(robot_coordinates[1])
    m = [0] * int(map_size[0])
    for i in range(int(map_size[0])):
        m[i] = [0] * int(map_size[1])
    for i in range(int(map_size[0])):
        for j in range(int(map_size[1])):
            m[i][j] = Cell('EMPTY')
    buf = 0
    while len(info) > 0:
        ln = list(info.pop(0))
        ln = [Cell(cells[i]) for i in ln]
        m[buf] = ln
        buf += 1
    return Robot(x, y, m)

prog_names = ['Data/factorial.txt', 'Data/factorial_rec.txt', 'Data/without_main.txt']
maps = ['Data/simple_map.txt', 'Data/Island.txt', 'Data/Big.txt', 'Data/A_lot_box.txt']
algo = ['Data/algo.txt']
print("What do you want to do? \n 0 - Run the algorithm \n 1 - Start the robot \n")
n = int(input())
if n == 0:
    i = Interpreter()
    print("What do you want to run ? \n 0 - Factorial \n 1 - Rec Factorial \n 2 - No main error \n")
    number = int(input())
    if number not in range(4):
        print("Bad number!")
    else:
        prog = open(prog_names[number], 'r').read()
        res = i.interpreter(program=prog)
        if res:
            print('Symbol table:')
            for symbol_table in i.symbol_table:
                for k, v in symbol_table.items():
                    print(k, v)
elif n == 1:
    print("Please choose the map: \n 0 - Simple map \n 1 - Island \n 2 - Big \n 3 - A lot of boxes \n")
    number = int(input())
    if number not in range(4):
        print("Bad number!")
    else:
        robot = make_robot(maps[number])
        i = Interpreter()
        prog = open(algo[0], 'r').read()
        res = i.interpreter(program=prog, robot=robot)
        if res:
            for symbol_table in i.symbol_table:
                for k, v in symbol_table.items():
                    print(k, v)
        if i.exit_found:
            print("\n\n========== EXIT HAS BEEN FOUND ==========\n\n")
        else:
            print("\n\n========== EXIT HAS NOT BEEN FOUND ==========\n\n")
        print('\nRobot:', i.robot)
        print('\nMap: ')
        i.robot.show()

# import sys
# from Parcer import ParserClass
# from Tree import SyntaxTreeNode
# from Errors import Error_handler
# from Errors import InterpreterApplicationCall
# from Errors import InterpreterIndex
# from Errors import InterpreterName
# from Errors import InterpreterValue
# from Errors import InterpreterType
# from Errors import InterpreterVar
# from Errors import InterpreterFuncCall
# from Robot import Robot, Cell, cells
# from Errors import Exit
#
#
# class Variable:
#     def __init__(self, val, ind):
#         self.ind = ind
#         if isinstance(val, bool):
#             self.type = 'bool'
#             self.val = val
#         elif val == 'EMPTY' or val == 'WALL' or val == 'BOX' or val == 'EXIT' or val == 'UNDEF':
#             self.type = 'cell'
#             self.val = val
#         elif isinstance(val, int):
#             self.type = 'int'
#             self.val = val
#
#     def __repr__(self):
#         return f'{self.type} {self.ind} {self.val}'
#
#
# class Interpreter:
#     def __init__(self, parser=ParserClass()):
#         self.pars = parser
#         self.map = None
#         self.prog = None
#         self.s_t = [dict()]
#         self.scope = 0
#         self.tree = None
#         self.funcs = None
#         self.robot = None
#         self.exit = False
#         self.s = 1000
#         self.error = Error_handler()
#         self.error_types = {'UnexpectedError': 0,
#                             'NoStartPoint': 1,
#                             'UndeclaredError': 2,
#                             'IndexError': 3,
#                             'FuncCallError': 4,
#                             'ValueError': 5,
#                             'ApplicationCall': 6,
#                             'TypeError': 7}
#
#     def interpreter_tree(self, tree):
#         tree.print()
#         print("\n")
#
#     def interpreter(self, program=None, robot=None):
#         self.robot = robot
#         self.prog = program
#         self.s_t = [dict()]
#         self.tree, self.funcs, _correct = self.pars.parse(self.prog)
#         if _correct:
#             if 'main' not in self.funcs.keys():
#                 print(self.error.up(self.error_types['NoStartPoint']))
#                 return
#             self.interpreter_tree(self.tree)
#             try:
#                 self.interpreter_node(self.funcs['main'].children['body'])
#                 return True
#             except RecursionError:
#                 sys.stderr.write(f'RecursionError: function calls itself too many times\n')
#                 sys.stderr.write("========= Program has finished with fatal error =========\n")
#                 return False
#             except Exit:
#                 return True
#         else:
#             sys.stderr.write(f'Can\'t interpretate incorrect input file\n')
#
#     def interpreter_node(self, node):
#         if self.exit_found:
#             raise Exit
#         if node is None:
#             return ''
#         elif node.type == 'program':
#             self.interpreter_node(node.children)
#         elif node.type == 'stmt_list':
#             for ch in node.children:
#                 self.interpreter_node(ch)
#         elif node.type == 'assignment':
#             var = node.children[0].value  # variable.value(name of var)
#             ind = self.indexs(node.children[0])
#             if self.scope == 0:
#                 if var not in self.s_t[self.scope].keys():
#                     if node.children[0].type == 'variable':
#                         self.s_t[self.scope][var] = [
#                             Variable(self.interpreter_node(node.children[1]), ind), ]
#                     elif node.children[0].type == 'var' and node.children[1].type == 'var':
#                         self.s_t[self.scope][var] = self.interpreter_node(node.children[1])
#                     elif node.children[0].type == 'var' and isinstance(self.interpreter_node(node.children[1]), list):
#                         v = self.interpreter_node(node.children[1])
#                         j = [0, ]
#                         for i in v:
#                             self.s_t[self.scope][var] = [Variable(i, tuple(j)), ]
#                             j = list(j)
#                             j[0] += 1
#                 else:
#                     if node.children[0].type == 'variable':
#                         schet = False
#                         a = 0
#                         for count in self.s_t[self.scope][var]:
#                             if ind == count.index:
#                                 schet = True
#                                 a = count
#                         if schet:
#                             try:
#                                 a.value = self.interpreter_node(node.children[1])
#                             except InterpreterName:
#                                 self.error.up(self.error_types['Undeclared'], node)
#                             except InterpreterIndex:
#                                 self.error.up(self.error_types['Index'], node)
#                             except InterpreterType:
#                                 self.error.up(self.error_types['Type'], node)
#                         else:
#                             try:
#                                 self.add(Variable(self.interpreter_node(node.children[1]), ind), var)
#                             except InterpreterName:
#                                 self.error.up(self.error_types['Undeclared'], node)
#                             except InterpreterIndex:
#                                 self.error.up(self.error_types['Index'], node)
#                             except InterpreterType:
#                                 self.error.up(self.error_types['Type'], node)
#                     elif node.children[0].type == 'var' and node.children[1].type == 'var':
#                         self.s_t[self.scope][var] = self.interpreter_node(node.children[1])
#                     elif node.children[0].type == 'var' and isinstance(self.interpreter_node(node.children[1]), list):
#                         v = self.interpreter_node(node.children[1])
#                         j = [0, ]
#                         for i in v:
#                             self.s_t[self.scope][var].append(Variable(i, tuple(j)))
#                             j = list(j)
#                             j[0] += 1
#             else:
#                 if node.children[0]. type == 'variable':
#                     c = 0
#                     flag = False
#                     schet = False
#                     a = 0
#                     while c <= self.scope:
#                         if var in self.s_t[c].keys():
#                             for count in self.s_t[c][var]:
#                                 if ind == count.ind:
#                                     flag = True
#                                     a = count
#                                     break
#                             if flag:
#                                 try:
#                                     a.value = self.interpreter_node(node.children[1])
#                                 except InterpreterName:
#                                     self.error.up(self.error_types['Undeclared'], node)
#                                 except InterpreterIndex:
#                                     self.error.up(self.error_types['Index'], node)
#                                 except InterpreterType:
#                                     self.error.up(self.error_types['Type'], node)
#                                 schet = True
#                                 break
#                         c += 1
#                     if not schet:
#                         if var not in self.s_t[self.scope].keys():
#                             self.s_t[self.scope][var] = [
#                                 Variable(self.interpreter_node(node.children[1]), ind), ]
#                         else:
#                             try:
#                                 self.add(Variable(self.interpreter_node(node.children[1]), ind), var)
#                             except InterpreterName:
#                                 self.error.up(self.error_types['Undeclared'], node)
#                             except InterpreterIndex:
#                                 self.error.up(self.error_types['Index'], node)
#                             except InterpreterType:
#                                 self.error.up(self.error_types['Type'], node)
#                 elif node.children[0].type == 'var':
#                     c = 0
#                     v = self.interpreter_node(node.children[1])
#                     flag = False
#                     while c <= self.scope:
#                         if var in self.s_t[c].keys():
#                             flag = True
#                             j = [0, ]
#                             self.s_t[c][var].clear()
#                             for i in v:
#                                 self.s_t[c][var].append(Variable(i, tuple(j)))
#                                 j = list(j)
#                                 j[0] += 1
#                         c += 1
#                     if not flag:
#                         j = [0, ]
#                         self.s_t[self.scope][var] = list()
#                         for i in v:
#                             self.s_t[self.scope][var].append(Variable(i, tuple(j)))
#                             j = list(j)
#                             j[0] += 1
#         elif node.type == 'variable':
#             if self.scope == 0:
#                 flag = False
#                 if node.value in self.s_t[self.scope].keys():
#                     tmp = self.indexs(node)
#                     for count in self.s_t[self.scope][node.value]:
#                         if tmp == count.index:
#                             flag = True
#                             return count.value
#                 else:
#                     raise InterpreterNameError
#                 if not flag:
#                     raise InterpreterIndexError
#             else:
#                 c = 0
#                 flag = False
#                 f = False
#                 while c <= self.scope:
#                     if node.value in self.s_t[c].keys():
#                         f = True
#                         tmp = self.indexs(node)
#                         for count in self.s_t[c][node.value]:
#                             if tmp == count.ind:
#                                 flag = True
#                                 return count.value
#                     c += 1
#                 if not f:
#                     raise InterpreterName
#                 if not flag:
#                     raise InterpreterIndex
#         elif node.type == 'var':
#             if self.scope == 0:
#                 if node.value in self.s_t[self.scope].keys():
#                     return self.s_t[self.scope][node.value]
#                 else:
#                     raise InterpreterName
#             else:
#                 c = self.scope
#                 while c >= 0:
#                     if node.value in self.s_t[c].keys():
#                         return self.s_t[c][node.value]
#                     c -= 1
#                 raise InterpreterName
#         elif node.type == 'const':
#             try:
#                 tmp = float(node.value)
#             except Exception:
#                 if node.value == 'true':
#                     tmp = True
#                 elif node.value == 'false':
#                     tmp = False
#                 else:
#                     try:
#                         tmp = int(node.value)
#                     except Exception:
#                         return node.value
#                 return tmp
#             else:
#                 return int(tmp)
#         elif node.type == 'un_operation':
#             var = self.interpreter_node(node.children)
#             if isinstance(var, bool):
#                 if not var:
#                     return True
#                 else:
#                     return False
#             elif isinstance(var, int):
#                 return -var
#             else:
#                 raise InterpreterType
#         elif node.type == 'operation':
#             if node.value == '+':
#                 var1 = self.interpreter_node(node.children[0])
#                 var2 = self.interpreter_node(node.children[1])
#                 if isinstance(var1, int) and isinstance(var2, int):
#                     return var1 + var2
#                 else:
#                     raise InterpreterType
#             elif node.value == '-':
#                 var1 = self.interpreter_node(node.children[0])
#                 var2 = self.interpreter_node(node.children[1])
#                 if isinstance(var1, int) and isinstance(var2, int):
#                     return var1 - var2
#                 else:
#                     raise InterpreterType
#         elif node.type == 'logic_oper':
#             if node.value == '&':
#                 return self.interpreter_node(node.children[0]) and self.interpreter_node(node.children[1])
#             elif node.value == '|':
#                 if node.children[0].type == 'variable' and node.children[1].type == 'variable':
#                     return self.interpreter_node(node.children[0]) | self.interpreter_node(node.children[1])
#             elif node.value == 'in':
#                 if (node.children[0].type == 'variable' or node.children[0].type == 'const') and node.children[1].type == 'variable':
#                     if self.interpreter_node(node.children[0]) == self.interpreter_node(node.children[1]):
#                         return True
#                     else:
#                         return False
#                 elif (node.children[0].type == 'variable' or node.children[0].type == 'const') and node.children[1].type == 'var':
#                     for count in self.s_t[0][node.children[1].value]:
#                         if self.interpreter_node(node.children[0]) == count.value:
#                             return True
#                     return False
#             elif node.value == 'less':
#                 if (node.children[0].type == 'variable' or node.children[0].type == 'const') and node.children[1].type == 'variable':
#                     if self.interpreter_node(node.children[0]) < self.interpreter_node(node.children[1]):
#                         return True
#                     else:
#                         return False
#                 elif (node.children[0].type == 'variable' or node.children[0].type == 'const') and node.children[1].type == 'var':
#                     sch = 0
#                     for count in self.s_t[self.scope][node.children[1].value]:
#                         if self.interpreter_node(node.children[0]) < count.value:
#                             sch += 1
#                     if sch == len(self.s_t[self.scope][node.children[1].value]):
#                         return True
#                     else:
#                         return False
#             elif node.value == 'all in':
#                 if node.children[0].type == 'var' and node.children[1].type == 'var':
#                     sch = 0
#                     for count1 in self.s_t[self.scope][node.children[0].value]:
#                         for count2 in self.s_t[self.scope][node.children[1].value]:
#                             if count1.value == count2.value:
#                                 sch += 1
#                                 break
#                     if sch == len(self.s_t[self.scope][node.children[0].value]):
#                         return True
#                     else:
#                         return False
#                 else:
#                     raise InterpreterVar
#             elif node.value == 'all less':
#                 if node.children[0].type == 'var' and node.children[1].type == 'var':
#                     sch = 0
#                     for count1 in self.s_t[self.scope][node.children[0].value]:
#                         for count2 in self.s_t[self.scope][node.children[1].value]:
#                             if count1.value > count2.value:
#                                 sch += 1
#                                 break
#                     if sch > 0:
#                         return False
#                     else:
#                         return True
#                 else:
#                     raise InterpreterVarError
#
#             elif node.value == 'some less':
#                 if node.children[0].type == 'var' and node.children[1].type == 'var':
#                     sch = 0
#                     for count1 in self.symbol_table[self.scope][node.children[0].value]:
#                         for count2 in self.symbol_table[self.scope][node.children[1].value]:
#                             if count1.value > count2.value:
#                                 sch += 1
#                                 break
#                     if sch == len(self.symbol_table[self.scope][node.children[0].value]):
#                         return False
#                     else:
#                         return True
#                 else:
#                     raise InterpreterVarError
#             elif node.value.type == 'variable':
#                 var = self.interpreter_node(node.value)
#                 if var == 0:
#                     return False
#                 else:
#                     return True
#         elif node.type == 'if':
#             cond = False
#             try:
#                 cond = self.interpreter_node(node.children[0])
#             except InterpreterVarError:
#                 self.error.up(self.error_types['TypeError'], node)
#             except InterpreterNameError:
#                 self.error.up(self.error_types['UndeclaredError'], node)
#             except InterpreterIndexError:
#                 self.error.up(self.error_types['IndexError'], node)
#             if cond:
#                 self.interpreter_node(node.children[1])
#         elif node.type == 'from_cycle':
#             try:
#                 self.op_from(node)
#             except InterpreterNameError:
#                 self.error.up(self.error_types['UndeclaredError'], node)
#             except InterpreterIndexError:
#                 self.error.up(self.error_types['IndexError'], node)
#             except InterpreterTypeError:
#                 self.error.up(self.error_types['TypeError'], node)
#         elif node.type == 'from_cycle_wh':
#             try:
#                 self.op_from(node)
#             except InterpreterNameError:
#                 self.error.up(self.error_types['UndeclaredError'], node)
#             except InterpreterIndexError:
#                 self.error.up(self.error_types['IndexError'], node)
#             except InterpreterTypeError:
#                 self.error.up(self.error_types['TypeError'], node)
#         elif node.type == 'call_func':
#             try:
#                 return self.function_call(node)
#             except InterpreterApplicationCall:
#                 self.error.up(self.error_types['ApplicationCall'], node)
#             except InterpreterFuncCallError:
#                 self.error.up(self.error_types['FuncCallError'], node)
#         elif node.type == 'function':
#             pass
#         elif node.type =='robot_com':
#             self.exit_found = self.robot.exit()
#             if self.exit_found:
#                 raise Exit
#             if self.step == 0:
#                 raise Exit
#             if node.value == 'go':
#                 res = self.go(node.children)
#             elif node.value == 'pick':
#                 res = self.pick(node.children)
#             elif node.value == 'drop':
#                 res = self.drop(node.children)
#             else:
#                 res = self.look(node.children)
#             return res
#
#     def indexs(self, node):
#         tmp = list()
#         child = node.children  # index
#         if child.type == 'zero_index':
#             tmp.append(0)
#         elif child.type == 'index':
#             tmp.append(int(child.value))
#         else:
#             child = child.children
#             while child[0].type != 'index':
#                 tmp.append(int(child[1].value))
#                 child = child[0].children
#             tmp.append(int(child[1].value))
#             tmp.append(int(child[0].value))
#             tmp.reverse()
#         return tuple(tmp)
#
#     def check_index(self, node):
#         index = self.indexs(node)
#         for count in self.s_t[self.scope][node.value]:
#             if index == count.index:
#                 return True
#         return False
#
#     def add(self, var, name):
#         if self.s_t[self.scope][name][0].type == var.type:
#             self.s_t[self.scope][name].append(var)
#         else:
#             raise InterpreterTypeError
#
#     def from_oper(self, node):
#         if node.type == 'from_cycle':
#             if node.children['from'].type == 'variable' and node.children['to'].type == 'variable':
#                 f = node.children['from']
#                 t = self.interpreter_node(node.children['to'])
#                 ind1 = self.indexs(f)
#                 a1 = 0
#                 for i in range(len(self.s_t[self.scope][f.value])):
#                     if ind1 == self.s_t[self.scope][f.value][i].index:
#                         while self.s_t[self.scope][f.value][i].value < t:
#                             self.interpreter_node(node.children['body'])
#         else:
#             f = self.interpreter_node(node.children['from'])
#             t = self.interpreter_node(node.children['to'])
#             if not (isinstance(f, int) and isinstance(t, int)):
#                 raise InterpreterTypeError
#             step = self.interpreter_node(node.children['with_step'])
#             if not isinstance(step, int):
#                 raise InterpreterTypeError
#             if step > 0:
#                 while f < t:
#                     self.interpreter_node(node.children['body'])
#                     f += step
#             elif step < 0:
#                 while f > t:
#                     self.interpreter_node(node.children['body'])
#                     f += step
#
#     def function_call(self, node):
#         if node.children.value == 'main':
#             raise InterpreterApplicationCall
#         if node.children.value in self.funcs.keys():
#             self.scope += 1
#             if self.scope > 1000:
#                 self.scope -= 1
#                 raise RecursionError from None
#             self.s_t.append(dict())
#             body = self.funcs[node.children.value].children['body']
#             self.interpreter_node(body)
#             if body.children[1] == 'variable' or body.children[1] == 'var' or body.children[1] == 'const':
#                 var = self.interpreter_node(body.children[1])
#                 self.scope -= 1
#                 self.s_t.pop()
#                 return var
#             else:
#                 self.scope -= 1
#                 self.s_t.pop()
#         else:
#             raise InterpreterFuncCall
#
#     def go(self, children):
#         self.exit = self.robot.exit()
#         if not self.exit_found:
#             flag = self.robot.go(children.value)
#             if flag:
#                 self.s -= 1
#             return flag
#
#     def pick(self, children):
#         return self.robot.pick(children.value)
#
#     def drop(self, children):
#         return self.robot.drop(children.value)
#
#     def look(self, children):
#         self.exit = self.robot.exit()
#         if not self.exit:
#             return self.robot.look(children.value)
#
#     def exit(self):
#         result = self.robot.exit()
#         if result:
#             self.exit = True
#         return result
#
#
# def make_robot(descriptor):
#     with open(descriptor) as file:
#         info = file.read()
#     info = info.split('\n')
#     map_size = info.pop(0).split()
#     robot_coordinates = info.pop(0).split()
#     x = int(robot_coordinates[0])
#     y = int(robot_coordinates[1])
#     m = [0] * int(map_size[0])
#     for i in range(int(map_size[0])):
#         m[i] = [0] * int(map_size[1])
#     for i in range(int(map_size[0])):
#         for j in range(int(map_size[1])):
#             m[i][j] = Cell('EMPTY')
#     buf = 0
#     while len(info) > 0:
#         ln = list(info.pop(0))
#         ln = [Cell(cells[i]) for i in ln]
#         m[buf] = ln
#         buf += 1
#     return Robot(x, y, m)
#
# prog_names = ['10th_Fib.txt', 'factorial.txt', 'factorial_rec.txt', 'without_main.txt']
# maps = ['simple_map.txt', 'Island.txt', 'Big.txt', 'A_lot_box.txt', 'center.txt', 'without_exit.txt']
# algo = ['algo.txt']
# print("What do you want to do? \n 0 - Run the algorithm \n 1 - Start the robot \n")
# n = int(input())
# if n == 0:
#     i = Interpreter()
#     print("What do you want to run ? \n 0 - Fibonacci \n 1 - Factorial \n 2 - Rec Factorial \n 3 - No main error \n")
#     number = int(input())
#     if number not in range(4):
#         print("Bad number!")
#     else:
#         prog = open(prog_names[number], 'r').read()
#         res = i.interpreter(program=prog)
#         if res:
#             print('Symbol table:')
#             for symbol_table in i.symbol_table:
#                 for k, v in symbol_table.items():
#                     print(k, v)
# elif n == 1:
#     print("Please choose the map: \n 0 - Simple map \n 1 - Island \n 2 - Big \n 3 - A lot of boxes \n"
#           " 4 - Start in center \n 5 - Without exit \n")
#     number = int(input())
#     if number not in range(6):
#         print("Bad number!")
#     else:
#         robot = make_robot(maps[number])
#         i = Interpreter()
#         prog = open(algo[0], 'r').read()
#         res = i.interpreter(program=prog, robot=robot)
#         if res:
#             for symbol_table in i.symbol_table:
#                 for k, v in symbol_table.items():
#                     print(k, v)
#         if i.exit_found:
#             print("\n\n========== EXIT HAS BEEN FOUND ==========\n\n")
#         else:
#             print("\n\n========== EXIT HAS NOT BEEN FOUND ==========\n\n")
#         print('\nRobot:', i.robot)
#         print('\nMap: ')
#         i.robot.show()
