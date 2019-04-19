import math

three = ('<', '<', '>')
two = ('<', '>')

def sec2min(seconds):
    return f'{(seconds/60):.3f}'

def header_code(header, code, syntax='css'):
    '''Helper function to format discord messages'''
    return f'{header}\n```{syntax}\n{code}```'

def board(board):
    return '\t'+'\n\t'.join(' '.join(row).upper() for row in board)

def acro(acro):
    return ' '.join(acro).upper()

def phrase(phrase):
    return ' '.join(phrase)

def table(results, headers, align, tablefmt='simple', limit=10, default_width=4):
    results = results[:limit]
    widths = [len(header) for header in headers]
    for row in results:
        for i, cell in enumerate(row):
            cell = str(cell)
            if widths[i] < len(cell):
                widths[i] = len(cell)+1

    headers = [' | '.join([f'{header:{align[i]}{widths[i]}}'
                for i, header in enumerate(headers)])]
    for row in results:
        headers.append(' | '.join([f'{str(cell):{align[i]}{widths[i]}}' 
                        for i, cell in enumerate(row)]))
    headers.insert(1, '='*(sum(widths)+(len(widths)-1)*3))

    return '\n'.join(headers)

if __name__ == '__main__':
    tablet = [['Abby', 'Worcester Sauce', 72],
             ['Miles', 'Ketchup', 21],
             ['Avery', 'Mustard', 19],
             ['Bonny', 'Sugar', 55],
             ['Dave', 'Vanilla', 84],
             ['Sixy', 'Ketchup', 9],
             ['Matt', 'Mustard', 49],
             ['Kate', 'Sugar', 15],
             ['Mull', 'Ketchup', 68],
             ['Ava', 'Mustard', 75],
             ['Brit', 'Sugar', 2]]

    print(table(tablet, ['Name', 'Condiment', 'Number'], ('<', '<', '>')))
