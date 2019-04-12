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

@bot.command(brief='Get the rules for a game.', description='Usage: !rules <game> (eg. !rules boggle)')
async def rules(ctx, game:str = None):
    if not game:
        await ctx.send('```Usage: !rules <game> (eg. !rules boggle)```')
        return
    await ctx.send(f'```{game}```')

@bot.command(brief='Get win/loss for a game.', description='Usage: !stats <game> (eg. !stats boggle)')
async def stats(ctx, game:str = None):
    if not game:
        await ctx.send('```Usage: !stats <game> (eg. !stats boggle)```')
        return
    name = game.lower()
    cog = bot.get_cog(name)
    if not cog:
        await ctx.send('```The game {game} does not exist.```')
        return
    stats = await cog.stats(ctx.author.id)
    if stats:
        await ctx.send(f'```diff\n  {name.capitalize()} stats for {ctx.author.name}\n+ Wins: {stats[0]}\n- Losses: {stats[1]}```')
    else:
        await ctx.send(f'You have no stats for {name}.')

bot.add_cog(games.boggle(bot))
bot.run(creds)