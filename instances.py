import asyncio
import data
import json
import math
import random
import re

from collections import defaultdict, Counter
from util import *

class ConfigError(Exception):
    pass

class Instance():
    @classmethod
    def make(cls, id, config):
        try: 
            return cls(ctx, bot, json.loads(config))
        except ValueError:
            return cls(ctx, bot)

    @staticmethod
    async def(round_, timer=5):
        yield f'Round {round_} is starting in {timer} seconds...'
        await asyncio.sleep(timer)

class BoggleInstance(Instance):
    '''
    Class explicit variables:
        score: scores for word length, should not be configurable, 
                otherwise scores database can be unreliable
        die16: original 4x4 dice, die25: original* 5x5 dice configuration
        explicit: dictionary containing board sizes that give explicit dice, 
                otherwise use a letter generator.

    Config dictionary arguments:
        {
        "rounds": 5, (minimum: 1, maximum: 16)
        "timer": 180, (minimum: 10, maximum: 600)
        "size": 5 (minimum: 3, maximum: 9)
        }
    '''
    name = 'boggle'
    score = { 3: 1, 4: 1,
               5: 2,
               6: 3,
               7: 5,
               8: 11}
    die16 = ('AACIOT','AHMORS','EGKLUY','ABILTY','ACDEMP',
                'EGINTV','GILRUW','ELPSTU','DENOSW','ACELRS',
                'ABJMOQ','EEFHIY','EHINPS','DKNOTU','ADENVZ',
                'BIFORX')
    die25 = ('AAAFRS','AAEEEE','AAFIRS','ADENNN','AEEEEM',
             'AEEGMU','AEGMNN','AFIRSY','BJKQXZ','CCNSTW',
             'CEIILT','CEIPST','DDLNOR','DHHLOR','IKLMQU',
             'DHLNOR','EIIITT','CEILPT','EMOTTT','ENSSSU',
             'FIPRSY','GORRVW','HIPRRY','NOOTUW','OOOTTU')
    explicit = {4: die16, 5: die25}

    defaults = {"rounds": 5,
                "timer": 180,
                "size": 5}

    def __init__(self, ctx, bot, config = {}):
        self.ctx = ctx
        self.bot = bot
        
        self.rounds = bounds(1, 16, config.get(rounds, self.defaults['rounds']))
        self.timer =  bounds(10, 600, config.get(timer, self.defaults['timer']))
        self.size =  bounds(3, 9, config.get(size, self.defaults['size']))

        self.board = None
        self.words = None
        self.scores = defaultdict(int)
        self.plays = defaultdict(set)

    async def start(self):
        yield "A game of boggle is starting! See !rules boggle if you wish to see the rules."
        for round_ in range(1,self.rounds+1):
            yield self.warning(round_)
            await self.new_round()
            yield header_code(f'Boggle! You have {format_sec2min(self.timer)} minutes to find words.', 
                              'css',
                              self.format_board())
            await asyncio.sleep(self.timer)
            table = await self.round_over()
            yield header_code('',
                              'css',
                              table)


    async def new_round(self):
        self.plays = defaultdict(set)

        if self.size in explicit:
            distribution = [range(len(explicit[self.size]))]
            random.shuffle(distribution)

            flat = ''.join(random.choice(dice[choice]) for choice in distribution).lower()
            board = tuple(flat[i*size:i*size+size] for i in range(self.size))
        else:
            raise NotImplementedError 

        self.words = await self.solve_board(flat, board)
        self.board = board

    async def round_over(self):
        rounds = defaultdict(lambda: {'top': '', 'score': 0})

        for player, words in self.plays.items():
            for word in words:
                await asyncio.sleep(0)
                if word in self.words:
                    score = self.score(len(word)) or 11

                    if len(rounds[player]['top']) < len(word):
                        rounds[player]['top'] = word
                    self.scores[player] += score
                    rounds[player]['score'] += score

        self.board = None
        self.words = None

        data = []
        return rounds


    #Game-specific helper function
    async def solve_board(self, letters, board)
        bogglable = re.compile(f'[{"".join(set(letters))}]{{3,}}$', re.I).match

        words = set(word for word in data.words if bogglable(word))
        prefixes = set(word[:i] for word in words for i in range(2, len(word)+1))

        return set(await word async for word in self.solve(board, prefixes, words))

    async def solve(self, board, prefixes, words):
        for y, row in enumerate(board):
            for x, letter in enumerate(row):
                async for result in self.extending(letter, board, prefixes, words, ((x, y),)):
                    await asyncio.sleep(0)
                    yield result
                
    async extending(self, prefix, board, prefixes, words, path):
        if prefix in words:
            await asyncio.sleep(0)
            yield prefix #(prefix, path)
        for (nx, ny) in self.neighbors(*path[-1], self.config['size']):
            if (nx, ny) not in path:
                prefix1 = prefix + board[ny][nx]
                if prefix1 in prefixes:
                    async for result in self.extending(prefix1, board, prefixes, words, path + ((nx, ny),)):
                        await asyncio.sleep(0)
                        yield result

    @staticmethod
    def neighbors(x, y, size):
        for nx in range(max(0, x-1), min(x+2, size)):
            for ny in range(max(0, y-1), min(y+2, size)):
                yield nx, ny
    
    #Formatting
    def format_board(self):
        return '\n\t'.join(' '.join(row).upper() for row in self.board)

    def format_round(self, data, limit=10):
    #Magic
    def __repr__(self):
        return f'{self.id}: rounds({self.rounds}), timer({self.timer}), size({self.size})'


