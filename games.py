import discord
import asyncio
import offline
import offlinedb
import loader

from discord.ext import commands
from tabulate import tabulate

class boggle(commands.Cog):
    round_timer = 180 #3 minutes
    words = loader.load(loader.files['words'])

    def __init__(self, bot):
        self.bot = bot
        self.games = {}
        self.db = offlinedb.DBHandler(self.__class__.__name__)

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.channel.id in self.games and msg.author.bot is False:
            self.games[msg.channel.id].play(msg.author.id, msg.content)

    @commands.command()
    async def boggle(self, ctx, rounds:int = 3, config=offline.Boggle_Instance.boggle5):
        if ctx.guild is None:
            return None
        elif ctx.message.channel.id in self.games:
            await ctx.send('Game has already started...')
            return None
        else:
            id = ctx.message.channel.id

        self.games[id] = offline.Boggle_Instance(id, self.words, config)
        rounds = min(rounds, 6)

        for round in range(1,rounds+1):
            await ctx.send(f'Round {round} starting in 5 seconds...')
            await asyncio.sleep(5)

            self.games[id].shuffle_board()
            await ctx.send(f"Boggle! You have three minutes to find words.\n```css\n\t{self.games[id].format_board()}```")

            await asyncio.sleep(30)
            results = self.games[id].round_over()
            data, formatted = self.games[id].format_play(self.bot, results)
            await self.message_table(ctx, f'Round {round} over. \nTop Ten', formatted[:10], headers=['[User', 'Top Word', 'Score]'])
            await asyncio.sleep(3)
            
        results = self.games[id].game_over()
        data, formatted = self.games[id].format_score(self.bot, results)
        try:
            winner = formatted[0][0]
            await self.message_table(ctx, f'Game over! \nThe winner is {winner}!', formatted[:10], headers=['[User', 'Score]'])
        except IndexError:
            await self.message_table(ctx, f'Game over! No one played? 😢', formatted[:10], headers=['[User', 'Score]'])

        if len(formatted) > 1:
            await self.db.record(data)
    
        del self.games[id]

    async def message_table(self, ctx, title, message, headers=None):
        await ctx.send(f"{title}\n```ini\n{tabulate(message[:10], headers=headers, tablefmt='simple')}```")

    async def stats(self, userid):
        return await self.db.get(userid)