def bounds(min_, max_, n):
    '''Helper function to return min, or max or inbetween if in bounds'''
    return min(max_, max(min_, n))

def header_code(header, code, syntax='css'):
    '''Helper function to format discord messages'''
    return f'{header}\n```{syntax}\n{code}```'