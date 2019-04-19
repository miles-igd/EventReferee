files = {
    'words': 'data/words.txt',
    'medium': 'data/medium.txt',
    'easy': 'data/easy.txt'
}

with open(files['words'], 'r') as file:
    words = {line.strip('\n') for line in file if len(line) > 3}

with open(files['medium'], 'r') as file:
    medium = tuple(line.strip('\n') for line in file if len(line) >= 5)

with open(files['easy'], 'r') as file:
    easy = tuple(line.strip('\n') for line in file if len(line) >= 5)
    hard = tuple(word for word in words if len(word) >= 4)
        
