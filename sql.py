import asyncio
import aiosqlite
import discord
import inspect
import sqlite3

from collections import defaultdict

class Cache():
    '''Cache discord results so we do not spam the API'''
    dbNAME = 'db/_cache.db' #do not change unless you know what you're doing

    tables = {
        'users': "id INTEGER PRIMARY KEY, username TEXT, discriminator INTEGER, avatar TEXT",
        'channels': "id INTEGER PRIMARY KEY, type INTEGER, guildid INTEGER, owner_id INTEGER",
        'servers': "id INTEGER PRIMARY KEY, name TEXT, owner_id INTEGER" 
    }

    @staticmethod
    def startup(bot):
        with sqlite3.connect(Cache.dbNAME) as con:
            for table, columns in Cache.tables.items():
                con.execute(f'CREATE TABLE IF NOT EXISTS {table}({columns})')
        return Cache(bot)

    def __init__(self, *args, **kwargs):
        self.mem = defaultdict(dict)

    async def t_delete(self, key, id, timer=1800):
        await asyncio.sleep(timer)
        del self.mem[key][id]
        print(f'Successfully deleted {id} from cache')

    def __repr__(self):
        return str(self.mem)

class DBHandler:
    '''Statistics
    user:
    wins:
    losses:
    win/loss:

    for any game.
    '''
    games = {'acro': 'acro.db', 
             'boggle': 'boggle.db'}

    @classmethod
    def startup(cls):
        for game in cls.games.values():
            with sqlite3.connect(f'database/{game}') as con:
                con.execute(f'''CREATE TABLE IF NOT EXISTS winloss
                (userid INTEGER PRIMARY KEY, name TEXT, discriminator TEXT, 
                wins INTEGER, losses INTEGER, winloss REAL)''')

    @classmethod
    async def incr(cls, name, col, users):
        async with aiosqlite.connect(cls.games[name]) as con:
            

if __name__ == '__main__':
    pass