def bounds(min_, max_, n):
    '''Helper function to return min, or max or inbetween if in bounds'''
    return min(max_, max(min_, n))