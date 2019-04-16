import asyncio
import discord
import inspect
import games
import sql

from collections import defaultdict
from discord.ext import commands

class ActiveGame(Exception):
    pass

class RefBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.games = {}
        self.active = defaultdict(set)
        self.flags = defaultdict(set)

        self.cache = sql.Cache.startup(self)
        sql.DBHandler.startup()

    async def register(self, instance):
        '''If a game is running, it HAS to be in the registry, otherwise it's broken.
        This function should only be called at the beginning of an instance's life.'''
        if instance.ctx.message.id in self.games:
            raise ActiveGame('An instance in this channel is already running. If not, try running !reset in this channel.')

        self.games[instance.ctx.message.channel.id] = instance

        if instance.name in ['acro']:
            self.games[instance.name].add(instance)

    async def unregister(self, instance):
        '''If a game is running, it HAS to be in the registry, otherwise it's broken.
        This function should only be called at the end of an instance's life, otherwise
        an error occured.'''
        del self.games[instance.ctx.message.channel.id]

        if instance.name in ['acro']:
            self.games[instance.name].remove(instance)

    async def add_flag(self, instance, flag):
        '''Flags should only be added or removed by an instance'''
        self.flags[flag].add(instance.id)

    async def remove_flag(self, instance, flag):
        '''Flags should only be added or removed by an instance'''
        self.flags[flag].remove(instance.id)

class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

class Debug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def games(self, ctx):
        await ctx.send(self.bot.games)

    @commands.command()
    async def cache(self, ctx):
        await ctx.send(self.bot.cache)

if __name__ == '__main__':
    bot = RefBot(command_prefix='!', description='Referee Core Bot.')
    @bot.event
    async def on_ready():
        print(f'{bot.user.name}: {bot.user.id}')


    with open('_bot.creds', 'r') as file:
        creds = file.read()

    bot.add_cog(Debug(bot))
    bot.add_cog(Main(bot))
    bot.add_cog(games.Games(bot))
    bot.run(creds)