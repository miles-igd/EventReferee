import asyncio
import discord
import instances
import traceback

from discord.ext import commands

UNEXPECTED_ERROR = 'An unexpected error ({}) occured, if this error persists please contact the author.'

class ActiveGame(Exception):
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
            self.bot.games[reaction.channel_id].vote(reaction.user_id, reaction.emoji.name)


    @commands.command(brief='Start a boggle game.', 
    description='Valid configurations (json): \n{rounds:[1,32], timer:[1,600], size:[3,9]}')
    async def boggle(self, ctx, *, config:str = None):
        '''
        Boggle is a word game of 16 or 25 dice.
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

    @commands.command(brief='Start an acro game.', 
    description='Valid configurations (json): \n{rounds:[1,32], timer:[1,600], vote_timer:[1,600], min:[3,9], max:[3,9]}')
    async def acro(self, ctx, *, config:str = None):
        '''
        Acro is a word game involving acronyms.
        Every round an acronym (eg. A L K I) is given and players will have to create a phrase out of the acronym.
        
        At the end of each round, anyone can vote for which phrase they liked the best by reacting to the emoji.
        Only the last react will count. There is no multiple voting. Feel free to obfuscate your voting with this.
        
        The phrase with the most votes gets 5 points, or if tied, 3 points. You can only get points if you have more than 1 vote!
        The winner at the end of the game is the player with the most points.
        '''
        await self.start('acro', ctx, config)

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
        except Exception as e:
            await ctx.send(UNEXPECTED_ERROR.format(e))
            print(traceback.format_exc())
        finally:
            #unregister game from Main registry, 
            #the instance should not have any flags.
            #Otherwise, there is an error inside the instance.
            await self.bot.unregister(instance)
            print(f'{instance} successfully unregistered from registry')
        
