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

bot.add_cog(games.Boggle(bot))
bot.run(creds)