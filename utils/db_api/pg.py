import asyncio
import asyncpg

from data import config

class Database:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.pool: asyncpg.pool.Pool = loop.run_until_complete(
            asyncpg.create_pool(
            user = config.PGUSER,
            password = config.PGPASSWORD,
            host = config.PGHOST
            )
        )

    async def create_table_users(self):
        sql = '''
        CREATE TABLE users IF NOT EXISTS (
        user_id bigint not null,
        first_name VARCHAR(255),
        date VARCHAR(30),
        auth smallint,
        education_id int,
        token VARCHAR(255),
        group_id int, 
        periods VARCHAR(255),
        PRIMARY KEY (user_id)
        )

        '''
        await self.pool.execute(sql)

    @staticmethod
    def format_args (sql, parametrs: dict):
        sql += " AND ".join([
            f"{item} = ${num}" for num, item in enumerate(parametrs, start=1)
        ])
        return sql, tuple(parametrs.values()) 
    
    async def add_user(self, user_id: int, first_name: str,
                        date: str, auth=0, education_id=None,
                        token=None, group_id=None, periods=None):
        sql = "INSERT INTO users (user_id, first_name, date, auth, education_id, token, group_id, periods) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)"
        await self.pool.execute(sql, user_id, first_name, date, auth, education_id, token, group_id, periods)
    
    async def add_estimate_id(self, estimate_id: int, user_id: int):
        sql = "INSERT INTO estimates (estimate_id, user_id) VALUES ($1, $2)"
        await self.pool.execute(sql, estimate_id, user_id)

    async def check_estimate_id(self, **kwargs):
        sql = "SELECT estimate_id from estimates WHERE "
        sql, parametrs = self.format_args(sql, kwargs)
        return await self.pool.fetchrow(sql, *parametrs)
    
    async def select_all_users(self, **kwargs):
        sql = "SELECT * from users WHERE "
        sql, parametrs = self.format_args(sql, kwargs)
        return await self.pool.fetch(sql, *parametrs)

    async def select_user(self, **kwargs):
        sql = "SELECT * from users WHERE "
        sql, parametrs = self.format_args(sql, kwargs)
        return await self.pool.fetchrow(sql, *parametrs)
    
    async def update_auth(self, auth: int, education_id: int, token: str,
                            group_id: int, periods: str, user_id: int):
        sql = "UPDATE users SET auth = $1, education_id = $2, token = $3, group_id = $4, periods = $5 WHERE user_id = $6"
        return await self.pool.execute(sql, auth, education_id, token, group_id, periods, user_id)
    
    async def change_auth(self, auth: int, user_id: int):
        sql = "UPDATE users SET auth = $1 where user_id = $2"
        return await self.pool.execute(sql, auth, user_id)
    
    