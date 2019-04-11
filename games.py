import discord
import asyncio
import offline
import loader

from discord.ext import commands

class Boggle(commands.Cog):
    words = loader.load(loader.files['words'])
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def host(self, ctx, rounds:int = 6, config=offline.Boggle_Instance.boggle4):
        rounds = min(rounds, 6)
        await ctx.send('Starting in 10 seconds...')
        instance = offline.Boggle_Instance(ctx, self.words, config)
        await asyncio.sleep(0)
        instance.shuffle_board()
        msg = 'Boggle! You have three minutes to find words.'

        board = f'''```css\n{instance.format()}```'''
        await ctx.send(msg)
        await ctx.send(board)

    @commands.command()
    async def rules(self, ctx, mode):
        pass