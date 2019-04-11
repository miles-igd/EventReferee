import discord
import asyncio
import offline
import loader

from discord.ext import commands

class Boggle(commands.Cog):
    words = loader.load(loader.files['words'])
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.guild.id in self.games:
            print(msg.content)
            print(msg.guild.id)

    @commands.command()
    async def boggle(self, ctx, rounds:int = 6, config=offline.Boggle_Instance.boggle5):
        if ctx.guild is None:
            return None
        elif ctx.guild in self.games:
            await ctx.send('Game has already started...')
            return None
        else:
            id = ctx.guild.id

        self.games[id] = offline.Boggle_Instance(id, self.words, config)
        rounds = min(rounds, 6)

        for round in range(1,rounds+1):
            await ctx.send(f'Round {round} starting in 10 seconds...')
            await asyncio.sleep(10)

            self.games[id].shuffle_board()
            await self.message(ctx, 'Boggle! You have three minutes to find words.', 
                          f'''```css\n\t{self.games[id].format_board()}```''')

            await asyncio.sleep(10)
            await self.message(ctx, 'Round over.', f'''```css\n\t{self.games[id].format_play()}```''')

        await self.message(ctx, 'Game over.', f'''```css\n\t{self.games[id].format_score()}```''')
        
        del self.games[id]

    async def message(self, ctx, title, message):
        await ctx.send(title)
        await ctx.send(message)

    @commands.command()
    async def active(self, ctx):
        await ctx.send(self.games)

    @commands.command()
    async def rules(self, ctx, mode):
        pass