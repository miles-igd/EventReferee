import asyncio
import discord
import games
import inspect

from discord.ext import commands

bot = commands.Bot(command_prefix='!', description='Referee Core Bot.')

@bot.event
async def on_ready():
    print(f'{bot.user.name}: {bot.user.id}')

class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.channel.id in self.games and msg.author.bot is False:
            self.games[msg.channel.id].play(msg.author.id, msg.content)

    @commands.command(brief='Get the rules for a game.', description='Usage: !rules <game> (eg. !rules boggle)')
    async def rules(self, ctx, game:str = None):
        if not game:
            await ctx.send('```Usage: !rules <game> (eg. !rules boggle)```')
            return
        name = game.lower()
        cog = self.bot.get_cog(name)
        if cog:
            await ctx.send(f'```{inspect.cleandoc(cog.__doc__)}```')
            return

    @commands.command(brief='Get win/loss for a game.', description='Usage: !stats <game> (eg. !stats boggle)')
    async def stats(self, ctx, game:str = None):
        if not game:
            await ctx.send('```Usage: !stats <game> (eg. !stats boggle)```')
            return
        name = game.lower()
        cog = self.bot.get_cog(name)
        if not cog:
            await ctx.send('```The game {game} does not exist.```')
            return
        stats = await cog.stats(ctx.author.id)
        if stats:
            await ctx.send(f'```diff\n  {name.capitalize()} stats for {ctx.author.name}\n+ Wins: {stats[0]}\n- Losses: {stats[1]}```')
        else:
            await ctx.send(f'You have no stats for {name}.')


with open('_bot.creds', 'r') as file:
    creds = file.read()

bot.add_cog(Main(bot))
bot.add_cog(games.boggle(bot))
bot.run(creds)