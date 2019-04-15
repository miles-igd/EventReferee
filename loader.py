files = {
    'words': 'words.txt',
    'blacklist': 'blacklist.txt',
}

def load(file):
    with open(file, 'r') as file:
        return {line.strip('\n') for line in file if len(line) > 3}