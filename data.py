files = {
    'words': 'data/words.txt',
}

with open(files['words'], 'r') as file:
    words = {line.strip('\n') for line in file if len(line) > 3}
        