from collections import defaultdict
import random
import re
import asyncio
import string

class Boggle_Instance():
    score = { 3: 1, 4: 1,
               5: 2,
               6: 3,
               7: 5,
               8: 11}
    die16 = ('AAEEGN','ELRTTY','AOOTTW','ABBJOO','EHRTVW', #New Boggle
             'CIMOTU','DISTTY','EIOSST','DELRVY','ACHOPS',
             'HIMNQU','EEINSU','EEGHNW','AFFKPS','HLNNRZ',
             'DEILRX',)
    die16_ = ('AACIOT','AHMORS','EGKLUY','ABILTY','ACDEMP', #Old Boggle
              'EGINTV','GILRUW','ELPSTU','DENOSW','ACELRS',
              'ABJMOQ','EEFHIY','EHINPS','DKNOTU','ADENVZ',
              'BIFORX',)
    die25 = ('AAAFRS','AAEEEE','AAFIRS','ADENNN','AEEEEM', #Big Boggle
             'AEEGMU','AEGMNN','AFIRSY','BJKQXZ','CCNSTW', #disallows 3 letter words.
             'CEIILT','CEIPST','DDLNOR','DHHLOR','IKLMQU',
             'DHLNOR','EIIITT','CEILPT','EMOTTT','ENSSSU',
             'FIPRSY','GORRVW','HIPRRY','NOOTUW','OOOTTU',)
    types = {4: {'size': 4, 'dice': die16_},
             5: {'size': 5, 'dice': die25}
            }

    def __init__(self, id, word_list, config):
        self.id = id
        self.word_list = word_list
        self.config = config

        self.board = None
        self.words = None

        self.scores = defaultdict(int)
        self.plays = defaultdict(set)

    def format_board(self):
        return '\n\t'.join([' '.join(row).upper() for row in self.board])

    def format_play(self, bot, results, limit=10):
        data = [[key, bot.get_user(key), value['top'], value['score']] for key, value in results.items()]
        data.sort(key=lambda x: x[-1], reverse=True)
        table = [[l[1].name, l[2], l[3]] for l in data]
        return data, table

    def format_score(self, bot, results, limit=10):
        data = [[key, bot.get_user(key), value] for key, value in results.items()]
        data.sort(key=lambda x: x[-1], reverse=True)
        table = [[l[1].name, l[2]] for l in data]
        return data, table

    def shuffle_board(self):
        self.plays.clear()

        dice = self.config['dice']
        size = self.config['size']

        distribution = list(range(len(dice)))
        random.shuffle(distribution)

        flat = ''.join(random.choice(dice[choice]) for choice in distribution).lower()
        board = tuple(flat[i*size:i*size+size] for i in range(size))

        self.words = self.solve_board(flat, board)
        self.board = board

    def solve_board(self, letters, board):
        bogglable = re.compile(f'[{"".join(set(letters))}]{{3,}}$', re.I).match

        words = set(word for word in self.word_list if bogglable(word))
        prefixes = set(word[:i] for word in words for i in range(2, len(word)+1))

        return set([word for word in self.solve(board, prefixes, words)])
        
    def solve(self, board, prefixes, words):
        for y, row in enumerate(board):
            for x, letter in enumerate(row):
                for result in self.extending(letter, board, prefixes, words, ((x, y),)):
                    yield result

    def extending(self, prefix, board, prefixes, words, path):
        if prefix in words:
            yield prefix #(prefix, path)
        for (nx, ny) in self.neighbors(*path[-1], self.config['size']):
            if (nx, ny) not in path:
                prefix1 = prefix + board[ny][nx]
                if prefix1 in prefixes:
                    for result in self.extending(prefix1, board, prefixes, words, path + ((nx, ny),)):
                        yield result
                        
    @staticmethod
    def neighbors(x, y, size):
        for nx in range(max(0, x-1), min(x+2, size)):
            for ny in range(max(0, y-1), min(y+2, size)):
                yield nx, ny

    def play(self, user, words):
        self.plays[user].update(words.lower().split(' '))

    def round_over(self):
        rounds = defaultdict(lambda: defaultdict(int))

        for player, words in self.plays.items():
            for word in words:
                if word in self.words:
                    length = len(word)
                    score = self.score[length] or 11
                    self.scores[player] += score

                    try:
                        if len(rounds[player]['top']) < length:
                            rounds[player]['top'] = word
                    except TypeError:
                        rounds[player]['top'] = word
                    
                    rounds[player]['score'] += score

        self.board = None
        self.words = None
        return rounds

    def game_over(self):
        return self.scores

class Acro_Instance():
    weights = [0.0639, 0.046, 0.0936, 0.0487, 0.0416, 
               0.0464, 0.0316, 0.0331, 0.0357, 0.0127, 
               0.0098, 0.0432, 0.0576, 0.0306, 0.0237, 
               0.0853, 0.0044, 0.0531, 0.1078, 0.0512, 
               0.0204, 0.0162, 0.0333, 0.0025, 0.0056, 
               0.002]

    def __init__(self, id, config):
        self.id = id
        self.config = config

        self.acro = None

        self.scores = defaultdict(int)
        self.plays = defaultdict(set)

    def new_acronym(self):
        self.plays.clear()

        size = random.randint(self.config['min'], self.config['max'])
        acro = [random.choices(string.ascii_lowercase, weights=self.weights)[0] for _ in range(size)]


        return acro

    def play(self, user, words):
        self.plays[user] = words

    def round_over(self):
        valid = {}
        for player, acro in self.plays.items():
            

if __name__ == "__main__":
    #import loader
    class dummy_user():
        def __init__(self):
            self.name = 'Dummy'
    class dummy_bot():
        @staticmethod
        def get_user(*args):
            return dummy_user()
    from tabulate import tabulate

    offline_acro = Acro_Instance(0, {'min': 3, 'max': 5})
    a = offline_acro.new_acronym()
    print(a)

    input_ = input()
    offline_acro.play(0, input_)
    print(offline_acro.plays)
    