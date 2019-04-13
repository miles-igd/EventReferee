import discord
import asyncio
import offline
import offlinedb
import loader

from discord.ext import commands
from tabulate import tabulate

class boggle(commands.Cog):
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
        config = offline.Boggle_Instance.types[config]
        if ctx.guild is None:
            return None
        elif ctx.message.channel.id in self.Main.games:
            await ctx.send('Game has already started...')
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
            await self.message_table(ctx, f'Round {round} over. \nTop Ten', formatted[:10], headers=['[User', 'Top Word', 'Score]'])
            await asyncio.sleep(3)
            
        results = self.Main.games[id].game_over()
        data, formatted = self.Main.games[id].format_score(self.bot, results)
        try:
            winner = formatted[0][0]
            await self.message_table(ctx, f'Game over! \nThe winner is {winner}!', formatted[:10], headers=['[User', 'Score]'])
        except IndexError:
            await self.message_table(ctx, f'Game over! No one played? 😢', formatted[:10], headers=['[User', 'Score]'])

        if len(formatted) > 1:
            await self.db.record(data)
    
        del self.Main.games[id]

    async def message_table(self, ctx, title, message, headers=None):
        await ctx.send(f"{title}\n```ini\n{tabulate(message[:10], headers=headers, tablefmt='simple')}```")

    async def stats(self, userid):
        user_stats = await self.db.get(userid)
        if user_stats:
            return user_stats[3:]
        else:
            return None

class acro(commands.Cog):
    ''''''
    def __init__(self, bot):
        self.bot = bot
        self.Main = self.bot.get_cog('Main')
        self.db = offlinedb.DBHandler(self.__class__.__name__)

    pass