import asyncio
import discord
import instances
import traceback

from discord.ext import commands
from tabulate import tabulate

UNEXPECTED_ERROR = 'An unexpected error ({}) occured, if this error persists please contact the author.'

class NotInCog(Exception):
    pass

class Games(commands.Cog):
    '''Current available games:
    -Boggle
    -Acro'''
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.content == 'stop': await self.bot.logout()
        if msg.author.bot: return
        if msg.channel.id in self.bot.games:
            self.bot.games[msg.channel.id].play(msg.author.id, msg.content)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if self.bot.user.id == reaction.user_id: return
        if reaction.channel_id in self.bot.flags['voting']:
            self.bot.flags['voting'][reaction.channel_id].vote(reaction.user_id, reaction.emoji.name)
        print(reaction)


    @commands.command(brief='Start a boggle game!', description='Valid configurations (json): \n{rounds:[1,32], timer:[1,600], size:[3,9]}')
    async def boggle(self, ctx, *, config:str = None):
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
        await self.start('boggle', ctx, config)


    async def start(self, game, ctx, config:str = None):
        '''Start an instance of [game] with json config [config], handling any errors'''
        try:
            instance = instances.games[game].make(ctx, self.bot, config)
        except instances.ConfigError as e:
            await ctx.send(e)
            print(traceback.format_exc())
            return
        except Exception as e:
            await ctx.send(UNEXPECTED_ERROR.format(e))
            print(traceback.format_exc())
            return

        #register game to Main registry
        try:
            await self.bot.register(instance)
        except ActiveGame as e:
            await ctx.send(e)
            print(traceback.format_exc())
            return

        try:
            #await messages, until rounds are over.
            async for message in instance.start():
                await ctx.send(message)
            #game end
            #await ctx.send(await instance.stop())
        except Exception as e:
            await ctx.send(UNEXPECTED_ERROR.format(e))
            print(traceback.format_exc())
            await instance.reset() #This will unregister and unflag for you
            print(f'{instance} successfully unregistered from registry')
            return
        
        #unregister game from Main registry
        await self.bot.unregister(instance)