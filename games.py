import discord
import asyncio
import offline
import offlinedb
import loader

from discord.ext import commands
from tabulate import tabulate

class NotInCog(Exception):
    pass

async def message_table(ctx, title, message, headers=None):
    return await ctx.send(f"{title}\n```ini\n{tabulate(message[:10], headers=headers, tablefmt='simple')}```")

class Base():
    def __init__(self):
        self.db = None

    async def stats(self, userid):
        user_stats = await self.db.get(userid)
        if user_stats:
            return user_stats[3:]
        else:
            return None

class boggle(commands.Cog, Base):
    '''Boggle is a word game of 16 or 25 dice.
    There are letters on the 6 sides of the die.
    
    A round of boggle starts with the shuffling and rolling of the dice into a 4x4 or 5x5 square.
    Players must find words formed on the board.
    Words are formed by connecting letters on the board with their adjacent or diagonal letters.
    
    Words are scored by their length, the longer the word, the larger the score!
    3,4 = 1 pts
    5 = 2 pts
    6 = 3 pts
    7 = 5 pts
    8+ = 11pts
    
    In the 5x5 version, 3 letter words are disallowed.
    
    After a set of rounds, the player with the most points is the winner.'''
    round_timer = 180 #3 minutes
    words = loader.load(loader.files['words'])

    def __init__(self, bot):
        self.bot = bot
        self.Main = self.bot.get_cog('Main')
        self.db = offlinedb.DBHandler(self.__class__.__name__)

    @commands.command(brief='Start a boggle game!', description='Usage: !boggle <rounds(1-6)> <board_size(4-5)> (eg. !boggle 6 5)[Default: 3 rounds, board_size 5]')
    async def boggle(self, ctx, rounds:int = 3, config:int = 5):
        try:
            config = offline.Boggle_Instance.types[config]
        except KeyError:
            await ctx.send(f'```Board configuration not found, valid: {list(offline.Boggle_Instance.types.keys())}.```')
            return None
        if ctx.guild is None:
            return None
        elif ctx.message.channel.id in self.Main.games:
            await ctx.send('A game has already started...')
            return None
        else:
            id = ctx.message.channel.id

        self.Main.games[id] = offline.Boggle_Instance(id, self.words, config)

        rounds = max(1, min(rounds, 6))

        for round in range(1,rounds+1):
            await ctx.send(f'Round {round} starting in 5 seconds...')
            await asyncio.sleep(5)

            self.Main.games[id].shuffle_board()
            await ctx.send(f"Boggle! You have three minutes to find words.\n```css\n\t{self.Main.games[id].format_board()}```")

            await asyncio.sleep(self.round_timer)
            results = self.Main.games[id].round_over()
            data, formatted = self.Main.games[id].format_play(self.bot, results)
            await message_table(ctx, f'Round {round} over. \nTop Ten', formatted[:10], headers=['[User', 'Top Word', 'Score]'])
            await asyncio.sleep(3)
            
        results = self.Main.games[id].game_over()
        data, formatted = self.Main.games[id].format_score(self.bot, results)
        try:
            winner = formatted[0][0]
            await message_table(ctx, f'Game over! \nThe winner is {winner}!', formatted[:10], headers=['[User', 'Score]'])
        except IndexError:
            await message_table(ctx, f'Game over! No one played? 😢', formatted[:10], headers=['[User', 'Score]'])

        if len(formatted) > 1:
            await self.db.record(data)
    
        del self.Main.games[id]

class acro(commands.Cog, Base):
    '''Acro is a word game involving acronyms.
    Every round an acronym (eg. A L K I) is given and players will have to create a phrase out of the acronym.
    
    At the end of each round, anyone can vote for which phrase they liked the best by reacting to the emoji.
    Only the last react will count. There is no multiple voting. Feel free to obfuscate your voting with this.
    
    The phrase with the most votes gets 5 points, or if tied, 3 points. You can only get points if you have more than 1 vote!
    The winner at the end of the game is the player with the most points.
    '''
    round_timer = 120 #2 minutes
    emojis = '''🍕🍔🍟🌭🍿🥓🥚🥞🍳🍞🥐🥨🧀🥗🥪🌮🌯🥫🍖🍠🥡🍙🍚🍣🍤🍦🍩🍪🍰🍫🍭🍮🍼🍸🥤🏺🥝
    🍇🍈🍉🍊🍋🍌🍍🍎🍑🍒🍓🍅🍆🌽🥕🌰🥜🎈🎆✨🎉🎊🎃🎏🎎🎐🎑🎀🎁🎠🎡🎢🎪🎭🎨🛒👓⚽⚾🏀🏐
    🏈🏉🎱🎳🥌⛳🎣🛶🏑🏏🏓🎾🎯🥊🎲🔮📣🔔🎵🎶🎤🎧📯🥁🎷🎸🎹🎺🎻📻🔑🔨📿🏹🔗🔪💣🔫📞📟📠
    📱🔋🗿🔌💻💽💾💿📀🎥🎬📡📼📹📷'''


    def __init__(self, bot):
        self.bot = bot
        self.Main = self.bot.get_cog('Main')
        self.db = offlinedb.DBHandler(self.__class__.__name__)

    @commands.command(brief='Start an acro game!')
    async def acro(self, ctx, rounds:int = 3, config:int = 5):
        try:
            config = offline.Acro_Instance.types[config]
        except KeyError:
            await ctx.send(f'```Board configuration not found, valid: {list(offline.Acro_Instance.types.keys())}.```')
            return None
        if ctx.guild is None:
            return None
        elif ctx.message.channel.id in self.Main.games:
            await ctx.send('A game has already started...')
            return None
        else:
            id = ctx.message.channel.id

        self.Main.active[id] = self.Main.games[id] = offline.Acro_Instance(id, config)

        rounds = max(1, min(rounds, 10))

        for round in range(1,rounds+1):
            await ctx.send(f'Round {round} starting in 5 seconds...')
            await asyncio.sleep(5)

            self.Main.games[id].new_acronym()
            await ctx.send(f"Acro! You have 2 minutes to DM me with your phrase.\n```css\n\t{self.Main.games[id].format_board()}```")

            await asyncio.sleep(20)
            results = self.Main.games[id].round_over()

            truncated = self.emojis[:len(results)]
            data, formatted = self.Main.games[id].format_play(self.bot, truncated, results)
            msg = await message_table(ctx, f'Voting phase! \nYou have 2 minutes to vote!', formatted, headers=['[React!', 'Phrase]'])
            for emoji in truncated:
                await msg.add_reaction(emoji)
            self.Main.voting_blocs[id] = self.Main.games[id]
            await asyncio.sleep(20)

            del self.Main.voting_blocs[id]
            results = self.Main.games[id].vote_over(data, truncated)
            await ctx.send(f'{results}')

        del self.Main.games[id]
        del self.Main.active[id]