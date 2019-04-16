import math

from tabulate import tabulate

def sec2min(seconds):
    return f'{(seconds/60):.3f}'

def header_code(header, code, syntax='css'):
    '''Helper function to format discord messages'''
    return f'{header}\n```{syntax}\n{code}```'

def board(board):
    return '\t'+'\n\t'.join(' '.join(row).upper() for row in board)

def table(results, headers, tablefmt='simple', limit=10):
    return tabulate(results[:limit], headers=headers, tablefmt=tablefmt)
