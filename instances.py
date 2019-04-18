import asyncio
import data
import formatting as fmt
import json
import logging
import math
import random
import re
import string
import sql
import traceback

from collections import defaultdict, Counter, OrderedDict
from util import bounds, flagger

class ConfigError(Exception):
    pass

class NotEnoughPlayers(Exception):
    pass

class Instance():
    @classmethod
    def make(cls, ctx, bot, config=None):
        try: 
            if len(config) > 128:
                raise ConfigError('''```diff\n-The config is too large, what are you trying to do?```''')
            config = json.loads(config)
            if not isinstance(config, dict):
                raise ConfigError('''```diff\n-The config must be a json object. (eg. {"rounds": 6, "timer":30})```''')
            return cls(ctx, bot, config)
        except (TypeError, json.decoder.JSONDecodeError):
            if config:
                raise ConfigError('''```diff\n-The config must be a json object with integers. (eg. {"rounds": 6, "timer":30})```''')
            else:
                return cls(ctx, bot)

    @staticmethod
    def warning(round_, timer=5):
        return f'Round {round_} is starting in {timer} seconds...', timer

    def get_users(self, iterable):
        for key, val in iterable:
            if key in self.bot.cache.mem['user']:
                yield self.bot.cache.mem['user'][key], (key, val)
            else:
                user = self.bot.get_user(key)
                logging.info(f"Creating {key} in cache :) will delete after 1800secs")
                self.bot.cache.mem['user'][key] = user
                self.bot.loop.create_task(self.bot.cache.t_delete('user', key))
                yield user, (key, val)

    async def game_over(self):
        try:
            table, winners = await self._game_over()
        except NotEnoughPlayers:
            table, winners = [], 'Not enough players? 😥'
        return fmt.header_code(f'Game over. {winners}',
                                    fmt.table(table, ['Users', 'Score'], fmt.two),
                                    'md')

    async def _game_over(self):
        if len(self.scores) == 0:
            raise NotEnoughPlayers
        counts = Counter(self.scores)
        ordered = counts.most_common()

        data = [[user, score] for user, (key, score) in self.get_users(ordered)]
        winners = {user.name for user, score in data if score == ordered[0][1]}

        if len(self.scores) > 1:
            await sql.DBHandler.incr(self.name, 'wins', ordered[:len(winners)])
            await sql.DBHandler.incr(self.name, 'losses', ordered[len(winners):])

        return data, f"Congratz to the winner(s), {', '.join(winners)}. 🎉"

    async def reset(self):
        try:
            await self.bot.unregister(self)
        except Exception:
            logging.error(traceback.format_exc())

        try:
            for flag in self.possible_flags:
                if self.ctx.message.channel.id in self.bot.flags[flag]:
                    await self.bot.remove_flag(self, flag)
        except Exception:
            logging.error(traceback.format_exc())


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

    possible_flags = {}

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
        
    async def start(self):
        yield "A game of boggle is starting! See !help boggle if you wish to see the rules."
        await asyncio.sleep(1)
        for round_ in range(1,self.rounds+1):
            warn, timer = self.warning(round_)
            yield warn
            await asyncio.sleep(timer)
            self.new_round()
            yield fmt.header_code(f'Boggle! You have {fmt.sec2min(self.timer)} minutes to find words.', 
                                        fmt.board(self.board),
                                        'css',)
            await self.guess_phase()
            table = self.round_over()
            yield fmt.header_code('Round over.',
                                        fmt.table(table, ['Users', 'Best Word', 'Score'], fmt.three),
                                        'md')
            await asyncio.sleep(timer)
        yield await self.game_over()

    @flagger('playable', 'deletable')
    async def guess_phase(self):
        await asyncio.sleep(self.timer)

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
            raise NotImplementedError('This config is not yet implemented.')

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

        data = [[user, rounds[key]['top'], rounds[key]['score']]
                 for user, (key, val) in self.get_users(rounds.items())]
        data.sort(key=lambda x: x[-1], reverse=True)
        return data

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
        return f'{self.ctx.message.channel.id} {self.name}: rounds({self.rounds}), timer({self.timer}), size({self.size})'


class AcroInstance(Instance):
    '''
    Class explicit variables:
        freq: distribution of first letter of 100,000+ words not including
              stop words. 
        emojis: a string of emojis

    Config dictionary arguments:
        {
        "rounds": 3, (minimum: 1, maximum: 16)
        "timer": 120, (minimum: 10, maximum: 600)
        "min": 4 (minimum: 3, maximum: 9)
        "max": 7 (minimum: 3, maximum: 9)
        }
        if min is less than max than the range is reversed (ie. [max, min])
        later this might raise an exception
    '''
    name = 'acro'
    freq = (0.0639, 0.046, 0.0936, 0.0487, 0.0416, 
            0.0464, 0.0316, 0.0331, 0.0357, 0.0127, 
            0.0098, 0.0432, 0.0576, 0.0306, 0.0237, 
            0.0853, 0.0044, 0.0531, 0.1078, 0.0512, 
            0.0204, 0.0162, 0.0333, 0.0025, 0.0056, 
            0.002)

    emojis = ("🍕🍔🍟🌭🍿🥓🥚🥞🍳🍞🥐🥨🧀🥗🥪🌮🌯🥫🍖🍠🥡🍙🍚🍣🍤🍦🍩🍪🍰🍫🍭🍮🍼🍸🥤🏺🥝🍇🍈🍉"
             "🍊🍋🍌🍍🍎🍑🍒🍓🍅🍆🌽🥕🌰🥜🎈🎆✨🎉🎊🎃🎏🎎🎐🎑🎀🎁🎠🎡🎢🎪🎭🎨🛒👓⚽⚾🏀🏐🏈"
             "🎱🎳🥌⛳🎣🛶🏑🏏🏓🎾🎯🥊🎲🔮📣🔔🎵🎤🎧📯🥁🎷🎸🎹🎺🎻📻🔑🔨🏹🔗🔪💣🔫📞📟📠"
             "🗿🔌💻💽💾💿📀🎥🎬📡🐭🐹🐰🐶🐺🦊🐵🐸🙈🙉🙊🐯🦁🐴🐮🐷🐻🐼🐲🦄")

    defaults = {"rounds": 3,
                "timer": 120,
                "vote_timer": 60,
                "min": 4,
                "max": 7}

    possible_flags = {'voting'}

    def __init__(self, ctx, bot, config = {}):
        self.ctx = ctx
        self.bot = bot

        self.rounds = bounds(1, 16, config.get('rounds', self.defaults['rounds']))
        self.timer =  bounds(10, 600, config.get('timer', self.defaults['timer']))
        self.vote_timer = bounds(10, 600, config.get('vote_timer', self.defaults['vote_timer']))
        self.min =  bounds(3, 9, config.get('size', self.defaults['min']))
        self.max =  bounds(3, 9, config.get('size', self.defaults['max']))

        self.scores = defaultdict(int)
        self.plays = defaultdict(set)
        self.amt = 0
        self.acro = None
        self.votes = {}
        
    async def start(self):
        yield "A game of acro is starting! See !help acro if you wish to see the rules."
        await asyncio.sleep(1)
        for round_ in range(1,self.rounds+1):
            warn, timer = self.warning(round_)
            yield warn
            await asyncio.sleep(timer)
            self.new_round()
            yield fmt.header_code(f'Acro! You have {fmt.sec2min(self.timer)} minutes to DM me a phrase.', 
                                fmt.acro(self.acro),
                                'css',)
            await self.phrase_phase()
            try:
                yield await self.voting_phase()
            except NotEnoughPlayers:
                yield fmt.header_code('Round over. No one played? 😢',
                                    fmt.table([], ['React', 'Phrase'], fmt.two),
                                    'md')
            await asyncio.sleep(timer)
        yield await self.game_over()

    @flagger('DMable', 'playable', 'deletable')
    async def phrase_phase(self):
        await asyncio.sleep(self.timer)

    @flagger('votable')
    async def voting_phase(self):
        table, vote_table, reacts = await self.round_over()
        msg = await self.ctx.send(fmt.header_code(f'Vote now! You have {fmt.sec2min(self.vote_timer)} minutes.',
                                    fmt.table(table, ['React', 'Phrase'], fmt.two),
                                    'md'))
        for emoji in vote_table:
            await msg.add_reaction(emoji)
        await asyncio.sleep(self.vote_timer)

        header, table = await self.vote_over(vote_table, reacts)
        return fmt.header_code(header,
                                    fmt.table(table, ['User', 'Phrase', 'Votes'], fmt.three),
                                    'md')

    def new_round(self):
        self.plays = defaultdict(set)

        size = random.randint(min(self.min, self.max), max(self.min, self.max))
        self.acro = [random.choices(string.ascii_lowercase, weights=self.freq)[0] for _ in range(size)]

    async def round_over(self):
        if len(self.plays) == 0:
            raise NotEnoughPlayers

        return await self.vote_start()

    async def vote_start(self):
        self.votes = {}

        reacts = random.choices(self.emojis, k=len(self.plays))
        data = {reacts[i]: (user, fmt.phrase(phrase)) for i, (user, phrase) in enumerate(self.plays.items())}
        table = [(f'{emoji}​', phrase) for emoji, (user, phrase) in data.items()]

        return table, data, reacts

    async def vote_over(self, vote_table, reacts):
        if not self.votes: return None

        reactions = {user: emoji for user, emoji in self.votes.items() if emoji in reacts}
        if len(reactions) == 0:
            return 'No voters. 😢', []
        counts = Counter(reactions.values())
        votes = counts.most_common()
        
        table = [(user, phrase, counts[emoji]) for emoji, (user, (userid, phrase)) in zip(vote_table.keys(), self.get_users(vote_table.values()))]
        winners = [user for user, phrase, count in table if count == votes[0][1]]
        
        if len(winners) > 1:
            for winner in winners:
                self.scores[winner.id] += 3
        else:
            self.scores[winners[0].id] += 5
        
        return f"Vote over. Congratz {', '.join(winner.name for winner in winners)}. 🎉", table

    def play(self, userid, content):
        play_ = content.split(' ')
        if self.check_valid(play_):
            self.plays[userid] = play_

    def vote(self, user, vote):
        self.votes[user] = vote
    
    #Game-specific helper functions:
    def check_valid(self, acro):
        try:
            if len(acro) != len(self.acro): return False
            for letter, word in zip(self.acro, acro):
                if letter != word[0].lower():
                    return False
            
            return True
        except TypeError as e:
            logging.info(e)
            return False

    #Magic
    def __repr__(self):
        return f'{self.ctx.message.channel.id} {self.name}: rounds({self.rounds}), timer({self.timer})'


class UnscrambleInstance(Instance):
    pass

games = {
    'boggle': BoggleInstance,
    'acro': AcroInstance
}

if __name__ == "__main__":
    class dummyCH:
        id = 1
    class dummyMSG:
        channel = dummyCH
    class dummyCTX:
        message = dummyMSG