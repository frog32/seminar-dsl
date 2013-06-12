from ply import yacc

from .lexer import tokens
from . import language
from .exceptions import CompileException


# parser
def p_statement_list(p):
    '''
    statement_list : statement_list NEWLINE statement
                   | statement
    '''
    if len(p) == 2:
        p[0] = language.StatementList(p[1])
    else:
        p[1].append(p[3])
        p[0] = p[1]


def p_statement(p):
    '''
    statement : assignment
              | if_statement
              | for_statement
              | nop
              | print
    '''
    p[0] = p[1]


def p_if_statement(p):
    '''if_statement : IF expr NEWLINE START_BLOCK statement_list END_BLOCK'''
    p[0] = language.If(p[2], p[5])


def p_list(p):
    '''
    list : LSPAREN list_inner RSPAREN
    '''
    p[0] = p[2]


def p_list_inner(p):
    '''
    list_inner : list_part
               | list_inner COMMA list_part
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1]
        p[0].append(p[3])


def p_list_part(p):
    '''
    list_part : NUMBER
              | STRING
              | variable
    '''
    p[0] = p[1]


def p_for_statement(p):
    '''
    for_statement : FOR NAME IN expr NEWLINE START_BLOCK statement_list END_BLOCK
    '''
    p[0] = language.Forloop(p[2], p[4], p[7])


def p_assignment(p):
    '''assignment : variable ASSIGN expr'''
    if p[2] == '=':
        p[0] = language.Assignment(p[1], p[3])
    elif p[2] == '+=':
        p[0] = language.Assignment(p[1], language.Addition(p[1], p[3]))
    elif p[2] == '-=':
        p[0] = language.Assignment(p[1], language.Substraction(p[1], p[3]))
    elif p[2] == '*=':
        p[0] = language.Assignment(p[1], language.Multiplication(p[1], p[3]))
    elif p[2] == '/=':
        p[0] = language.Assignment(p[1], language.Division(p[1], p[3]))


def p_nop(p):
    '''nop : NOP'''
    p[0] = language.Nop()


def p_expr(p):
    '''
    expr : term
         | expr PLUS term
         | expr MINUS term
    '''
    if len(p) == 2:
        if isinstance(p[1], language.Expression):
            p[0] = p[1]
        else:
            p[0] = language.Expression(p[1])
    elif p[2] == '+':
        p[0] = language.Addition(p[1], p[3])
    elif p[2] == '-':
        p[0] = language.Substraction(p[1], p[3])
    else:
        raise CompileException("can't understand expr %s %s %s" % (p[1], p[2], p[3]))


def p_term(p):
    '''
    term : term TIMES factor
         | term DIVIDE factor
         | factor
    '''
    if len(p) == 2:
        p[0] = p[1]
    elif p[2] == '*':
        p[0] = language.Multiplication(p[1], p[3])
    elif p[2] == '/':
        p[0] = language.Division(p[1], p[3])
    else:
        raise CompileException("can't understand term %s %s %s" % (p[1], p[2], p[3]))


def p_factor(p):
    '''
    factor : NUMBER
           | STRING
           | list
           | variable
           | result
           | LPAREN expr RPAREN
    '''
    if len(p) > 2:
        p[0] = p[2]
    elif isinstance(p[1], language.Expression):
        p[0] = p[1]
    else:
        p[0] = language.Expression(p[1])


def p_variable(p):
    '''
    variable : NAME
             | variable DOT NAME
             | variable LSPAREN expr RSPAREN
    '''
    if len(p) == 2:
        p[0] = language.Variable(p[1])
    else:
        p[0] = p[1]
        p[0].add_subscription(p[3])


def p_call(p):
    '''
    result : variable LPAREN list_inner RPAREN
    '''
    p[0] = language.Call(p[1], *p[3])


def p_print(p):
    '''
    print : PRINT expr
    '''
    p[0] = language.PrintStatement(p[2])


def p_error(p):
    if p is None:
        return
    raise CompileException("Can't make use of %s on line %s" % (p.type, p.lineno))


parser = yacc.yacc()
