import asyncio
import discord
import games

from discord.ext import commands

bot = commands.Bot(command_prefix='!', description='Referee Core Bot.')
with open('_bot.creds', 'r') as file:
    creds = file.read()

@bot.event
async def on_ready():
    print(f'{bot.user.name}: {bot.user.id}')

@bot.command()
async def users(ctx):
    print(bot.users)
    print(bot.guilds)
    print(vars(ctx))
    await ctx.send(f'```{vars(ctx)}```')

@bot.command()
async def rules(ctx, game:str = None):
    if not game:
        await ctx.send('```Usage: !rules <game> (eg. !rules boggle)```')
        return
    await ctx.send(f'```{game}```')

@bot.command()
async def stats(ctx, game:str = None):
    if not game:
        await ctx.send('```Usage: !stats <game> (eg. !stats boggle)```')
        return
    cog = bot.get_cog(game.lower())
    if not cog:
        await ctx.send('```The game {game} does not exist.```')
        return
    stats = await cog.stats(ctx.author.id)
    await ctx.send(f'```{stats}```')

bot.add_cog(games.boggle(bot))
bot.run(creds)