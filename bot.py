import asyncio
import discord
import games

from discord.ext import commands

bot = commands.Bot(command_prefix='!', description='Referee Core Bot.')
integer = None
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
async def play(ctx, *, words):
    print(vars(ctx))
    print(words)

@bot.command()
async def test(ctx):
    msg = 'Boggle! You have three minutes to play words.'
    board = '''```css
    A H I J K
    E I T O C
    D E A A X
    G F T I E
    E A O U Z```'''
    await ctx.send(msg)
    await ctx.send(board)



bot.run(creds)