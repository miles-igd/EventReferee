import asyncio
import data
import formatting
import json
import math
import random
import re
import sql
import traceback

from collections import defaultdict, Counter, OrderedDict
from util import bounds

class ConfigError(Exception):
    pass

class NotEnoughPlayers(Exception):
    pass

class Instance():
    @classmethod
    def make(cls, ctx, bot, config=None):
        try: 
            return cls(ctx, bot, json.loads(config))
        except TypeError:
            return cls(ctx, bot)

    @staticmethod
    def warning(round_, timer=5):
        return f'Round {round_} is starting in {timer} seconds...', timer

    def get_users(self, iterable):
        for key, val in iterable:
            if key in self.bot.cache.mem['user']:
                yield self.bot.cache.mem['user'][key], key, val
            else:
                user = self.bot.get_user(key)
                print(f"Creating {key} in cache :) will delete after 1800secs")
                self.bot.cache.mem['user'][key] = user
                self.bot.loop.create_task(self.bot.cache.t_delete('user', key))
                yield user, key, val

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

    defaults = {"rounds": 3,
                "timer": 180,
                "size": 5}

    def __init__(self, ctx, bot, config = {}):
        self.ctx = ctx
        self.bot = bot
        
        self.rounds = bounds(1, 16, config.get('rounds', self.defaults['rounds']))
        self.timer =  bounds(10, 600, config.get('timer', self.defaults['timer']))
        self.size =  bounds(3, 9, config.get('size', self.defaults['size']))

        self.board = None
        self.words = None
        self.scores = defaultdict(int)
        self.plays = defaultdict(set)

    async def reset(self):
        try:
            await self.bot.unregister(self)
        except Exception:
            print(traceback.format_exc())
        

    async def start(self):
        yield "A game of boggle is starting! See !help boggle if you wish to see the rules."
        for round_ in range(1,self.rounds+1):
            warn, timer = self.warning(round_)
            yield warn
            await asyncio.sleep(timer)
            self.new_round()
            yield formatting.header_code(f'Boggle! You have {formatting.sec2min(self.timer)} minutes to find words.', 
                                        formatting.board(self.board),
                                        'css',)
            await asyncio.sleep(self.timer)
            table = self.round_over()
            yield formatting.header_code('Round over.',
                                        formatting.table(table, ['[Users', 'Best Word', 'Score]']),
                                        'ini')
            await asyncio.sleep(timer)

        try:
            table, winners = await self.game_over()
        except NotEnoughPlayers:
            table, winners = [], 'Not enough players? 😥'
        yield formatting.header_code(f'Game over. {winners}',
                                    formatting.table(table, ['[Users', 'Score]']),
                                    'ini')

    async def stop(self):
        '''To be used to stop, not necessarily end.'''
        return

    def play(self, userid, content):
        self.plays[userid].update(content.lower().split(' '))

    def new_round(self):
        self.plays = defaultdict(set)

        if self.size in self.explicit:
            dice = self.explicit[self.size]

            distribution = list(range(len(dice)))
            random.shuffle(distribution)

            flat = ''.join(random.choice(dice[choice]) for choice in distribution).lower()
            board = tuple(flat[i*self.size:i*self.size+self.size] for i in range(self.size))
        else:
            raise NotImplementedError 

        self.words = self.solve_board(flat, board)
        self.board = board

    def round_over(self):
        rounds = defaultdict(lambda: {'top': '', 'score': 0})

        for player, words in self.plays.items():
            for word in words:
                if word in self.words:
                    score = self.score[len(word)] or 11

                    if len(rounds[player]['top']) < len(word):
                        rounds[player]['top'] = word
                    self.scores[player] += score
                    rounds[player]['score'] += score

        self.board = None
        self.words = None

        data = [[user, rounds[key]['top'], rounds[key]['score']] for user, key, val in self.get_users(rounds.items())]
        data.sort(key=lambda x: x[-1], reverse=True)
        return data

    async def game_over(self):
        if len(self.scores) < 1:
            raise NotEnoughPlayers
        counts = Counter(self.scores)
        ordered = counts.most_common()

        data = [[user, score] for user, key, score in self.get_users(ordered)]
        winners = {user.name for user, score in data if score == ordered[0][1]}

        await sql.DBHandler.incr('win', ordered[:len(winners)])
        await sql.DBHandler.incr('loss', ordered[len(winners):])

        return data, f"Congratz to the winner(s), {', '.join(winners)}. 🎉"

    #Game-specific helper function
    def solve_board(self, letters, board):
        bogglable = re.compile(f'[{"".join(set(letters))}]{{3,}}$', re.I).match

        words = set(word for word in data.words if bogglable(word))
        prefixes = set(word[:i] for word in words for i in range(2, len(word)+1))

        return set(word for word in self.solve(board, prefixes, words))

    def solve(self, board, prefixes, words):
        for y, row in enumerate(board):
            for x, letter in enumerate(row):
                for result in self.extending(letter, board, prefixes, words, ((x, y),)):
                    yield result
                
    def extending(self, prefix, board, prefixes, words, path):
        if prefix in words:
            yield prefix #(prefix, path)
        for (nx, ny) in self.neighbors(*path[-1], self.size):
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

    #Magic
    def __repr__(self):
        return f'{self.ctx.message.channel.id}: rounds({self.rounds}), timer({self.timer}), size({self.size})'

games = {
    'boggle': BoggleInstance
}

if __name__ == "__main__":
    class dummyCH:
        id = 1
    class dummyMSG:
        channel = dummyCH
    class dummyCTX:
        message = dummyMSG
    loop = asyncio.get_event_loop()
    instance = BoggleInstance.make(dummyCTX, None, None)
    print(instance)