files = {
    'words': 'words.txt',
}

def load(file):
    with open('words.txt', 'r') as file:
        return set(line.strip('\n') for line in file if len(line) > 3)

if __name__ == "__main__":
    data = load(files['words'])
    print(len(data))
    print('alphabet' in data)
    print('anemone' in data)
    print('ass' in data)
    print(None in data)
    print('aa' in data)