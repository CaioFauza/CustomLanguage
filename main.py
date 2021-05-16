import sys
import numpy as np
import ply.lex as lex
import ply.yacc as yacc
from nodes import Bin_op, Assignment_op, Condition_Op, Input_op, While_Op, Un_op, Print_op, Statement_Op, Bool_val, Identifier_val, Int_val, String_val

reserved = {
    'toolkit': 'FUNCTION',
    'recover': 'RETURN',
    'door': 'INPUT',
    'show': 'PRINT',
    'until': 'WHILE',
    'over': 'FOR',
    'if': 'IF',
    'else': 'ELSE',
    'or': 'OR',
    'and': 'AND',
    'true': 'TRUE',
    'false': 'FALSE'
}

tokens = ['NUMBER', 'PLUS', 'MINUS', 'MULT', 'DIV', 'LPAR', 'RPAR', 'IDENTIFIER',
          'STRING', 'EQUAL', 'ATTRIB', 'NOTEQUAL', 'NOT', 'BIGGER', 'SMALLER', 'BIGGEREQUAL',
          'SMALLEREQUAL', 'SEMICOLLON', 'OPENBLOCK', 'CLOSEBLOCK'] + list(reserved.values())

t_PLUS = r'\+'
t_MINUS = r'\-'
t_MULT = r'\*'
t_DIV = r'\/'
t_LPAR = r'\('
t_RPAR = r'\)'
t_STRING = r'\".*"'
t_ATTRIB = r'\='
t_EQUAL = r'\=='
t_NOTEQUAL = r'\!='
t_NOT = r'\!'
t_BIGGER = r'\>'
t_SMALLER = r'\<'
t_BIGGEREQUAL = r'\>='
t_SMALLEREQUAL = r'\<='
t_SEMICOLLON = r'\;'
t_OPENBLOCK = r'\{'
t_CLOSEBLOCK = r'\}'
t_ignore = ' \t'

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t

def t_COMMENT(t):
    r'\//.*'
    pass

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print('Invalid syntax. Character {} is invalid'.format(t.value[0]))
    t.lexer.skip(1)

precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQUAL', 'NOTEQUAL'),
    ('nonassoc', 'BIGGER', 'SMALLER', 'BIGGEREQUAL', 'SMALLEREQUAL'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MULT', 'DIV'),
    ('right', 'UMINUS', 'UPLUS', 'UNOT')
)

def p_block(p):
    '''block : OPENBLOCK listcommand CLOSEBLOCK'''
    if(len(p) == 4):
        p[0] = Statement_Op('BLOCK', p[2])

def p_listcommand(p):
    '''listcommand : listcommand command 
                   | command'''
    if(len(p) == 2):
        p[0] = [p[1]]
    else:
        commands = np.ndarray.flatten(np.array(p[1])).tolist()
        commands.append(p[2])
        p[0] = commands

def p_command(p):
    '''command : IDENTIFIER ATTRIB orexpr SEMICOLLON
               | PRINT LPAR orexpr RPAR SEMICOLLON
               | block
               | WHILE LPAR orexpr RPAR command
               | IF LPAR orexpr RPAR command
               | IF LPAR orexpr RPAR command ELSE command'''

    if(len(p) == 2):
        p[0] = p[1]
    else:
        if(p[2] == '='):
            p[0] = Assignment_op(p[2], [Identifier_val(p[1]), p[3]])
        elif(p[1] == 'show'):
            p[0] = Print_op(p[1], [p[3]])
        elif(p[1] == 'until'):
            p[0] = While_Op(p[1], [p[3], p[5]])
        elif(p[1] == 'if'):
            if(len(p) == 6):
                p[0] = Condition_Op(p[1], [p[3], p[5]])
            else:
                p[0] = Condition_Op(p[1], [p[3], p[5], p[7]])

def p_orexpr(p):
    '''orexpr : orexpr OR andexpr
              | andexpr'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = Bin_op(p[2], [p[1], p[3]])

def p_andexpr(p):
    '''andexpr : andexpr AND eqexpr
              | eqexpr'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = Bin_op(p[2], [p[1], p[3]])

def p_eqexpr(p):
    '''eqexpr : eqexpr EQUAL relexpr
               | eqexpr NOTEQUAL relexpr
               | relexpr'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = Bin_op(p[2], [p[1], p[3]])

def p_relexpr(p):
    '''relexpr : relexpr BIGGER expression
               | relexpr SMALLER expression
               | relexpr BIGGEREQUAL expression
               | relexpr SMALLEREQUAL expression
               | expression'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = Bin_op(p[2], [p[1], p[3]])

def p_expression(p):
    '''expression : expression PLUS term
                  | expression MINUS term
                  | term'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = Bin_op(p[2], [p[1], p[3]])

def p_term(p):
    '''term : term MULT factor
            | term DIV factor
            | factor'''
    if(len(p) == 2):
        p[0] = p[1]
    else:
        p[0] = Bin_op(p[2], [p[1], p[3]])

def p_factor(p):
    '''factor : NUMBER
              | IDENTIFIER
              | TRUE
              | FALSE
              | STRING
              | LPAR orexpr RPAR 
              | PLUS factor %prec UPLUS
              | MINUS factor %prec UMINUS
              | NOT factor %prec UNOT
              | INPUT LPAR RPAR'''

    if(len(p) == 2):
        if(isinstance(p[1], int)):
            p[0] = Int_val(p[1])
        elif(p[1][0] == '"' and p[1][-1] == '"'):
            p[0] = String_val(p[1])
        elif(isinstance(p[1], str)):
            p[0] = Identifier_val(p[1])
        elif(p[1] == 'true' or p[1] == 'false'):
            p[0] = Bool_val(p[1])
    else:
        if(p[1] == '('):
            p[0] = Statement_Op('BLOCK', [p[2]])
        elif(p[1] == 'door'):
            p[0] = Input_op(p[1])
        else:
            p[0] = Un_op(p[1], [p[2]])

def p_error(p):
    print('Invalid syntax. Command: {}'.format(p.value))

def get_tokens():
    tokens = []
    while True:
        token = lexer.token()
        if not token:
            break
        tokens.append(token)
    return tokens

input_file = open(sys.argv[1], 'r')
input_code = input_file.readlines()
raw_tokens = ''.join([i.strip() for i in input_code])

lexer = lex.lex()
lexer.input(raw_tokens)

token_list = get_tokens()

parser = yacc.yacc(debug=True)

result = parser.parse(raw_tokens)
result.evaluate()

input_file.close()