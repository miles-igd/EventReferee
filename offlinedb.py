import asyncio
import aiosqlite
import sqlite3

class DBHandler():
    FNAME = '_bot.db' #Do not change unless you know what you're doing.

    def __init__(self, name : str):
        self.name = name.lower()
        with sqlite3.connect(self.FNAME) as con:
            con.execute(f'CREATE TABLE IF NOT EXISTS {name}(userid INTEGER PRIMARY KEY, name TEXT, discriminator TEXT, wins INTEGER, losses INTEGER)')

    async def record(self, data):
        async with aiosqlite.connect(self.FNAME) as con:
            id = data[0][0]
            row = await con.execute(f'SELECT * FROM {self.name} WHERE userid=?', (id,))
            if await row.fetchone():
                await con.execute(f'UPDATE {self.name} SET wins = wins + 1 WHERE userid=?', (id,))
            else:
                await con.execute(f'''INSERT INTO {self.name}(userid, name, discriminator, wins, losses) VALUES (?, ?, ?, ?, ?)''', 
                            (id, data[0][1].name, data[0][1].discriminator, 1, 0))
            for user in data[1:]:
                id = user[0]
                row = await con.execute(f'SELECT * FROM {self.name} WHERE userid=?', (id,))
                if await row.fetchone():
                    await con.execute(f'UPDATE {self.name} SET losses = losses + 1 WHERE userid=?', (id,))
                else:
                    await con.execute(f'''INSERT INTO {self.name}(userid, name, discriminator, wins, losses) VALUES (?, ?, ?, ?, ?)
                                        ON DUPLICATE KEY UPDATE losses = losses+1''', 
                                (id, user[1].name, user[1].discriminator, 0, 1))
            await con.commit()

    async def get(self, userid):
        async with aiosqlite.connect(self.FNAME) as con:
            stats = await con.execute(f'SELECT * FROM {self.name} WHERE userid=?', (userid,))
            return await stats.fetchall()
