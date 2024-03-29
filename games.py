import discord
import instances
import logging
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
        if msg.channel.id in self.bot.flags['playable']:
            self.bot.games[msg.channel.id].play(msg.author.id, msg.content)
        elif len(self.bot.flags['DMable']) > 0 and isinstance(msg.channel, discord.DMChannel):
            for channel in self.bot.flags['DMable']:
                self.bot.games[channel].play(msg.author.id, msg.content)


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if self.bot.user.id == reaction.user_id: return
        if reaction.channel_id in self.bot.flags['votable']:
            self.bot.games[reaction.channel_id].vote(reaction.user_id, reaction.emoji.name)


    @commands.command(brief='Start a boggle game.', 
    description='Valid configurations (json): \n{"rounds":[1,32], "timer":[1,600], "size":[3,9]}')
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
    description='Valid configurations (json): \n{"rounds":[1,32], "timer":[1,600], "vote_timer":[1,600], "min":[3,9], "max":[3,9]}')
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

    @commands.command(brief='Start an unscramble game.', 
    description='Valid configurations (json): \n{"rounds":[1,32], "timer":[1,600], "difficulty":["easy","medium","hard"]')
    async def unscramble(self, ctx, *, config:str = None):
        '''
        Unscramble is a word game.
        
        Every round, a scrambled word will appear, the first person to guess
        the word correctly wins the round.

        The winner is the player with the most wins at the end of the game.


        Easy: Any* of ~10000 most frequent English words. 
        Medium: Any* of ~50000 most frequent English words.
        Hard: Any* of ~350000 English words. Good luck.

        *Names included
        *Words greater than length 4
        '''
        await self.start('unscramble', ctx, config)

    async def start(self, game, ctx, config:str = None):
        '''Start an instance of [game] with json config [config], handling any errors'''
        if ctx.message.channel.id in self.bot.games:
            await ctx.send(
            '```diff\n- An instance in this channel is already running.'
            'If not, try running !reset in this channel.```')
            return

        try:
            instance = instances.games[game].make(ctx, self.bot, config)
        except instances.ConfigError as e:
            await ctx.send(e)
            logging.debug(traceback.format_exc())
            return
        except Exception as e:
            await ctx.send(UNEXPECTED_ERROR.format(e))
            logging.error(traceback.format_exc())
            return

        #register game to Main registry
        await self.bot.register(instance)
        try:
            async for message in instance.start():
                await ctx.send(message)
        except Exception as e:
            await ctx.send(UNEXPECTED_ERROR.format(e))
            logging.error(traceback.format_exc())
        finally:
            #Unregister game from Main registry, 
            #The instance should not have any flags.
            #Otherwise, there is an error inside the instance.
            await self.bot.unregister(instance)
            logging.info(f'{instance} successfully unregistered from registry')
        
