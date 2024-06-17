import asyncio
import aiohttp
import json

from aiogram import executor
from loader import db, bot
from handlers import dp
from utils.request import request

async def check_requests():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                info = await db.select_all_users(auth=1)
                tasks = []
                for i in info:
                    user_id = i.get("user_id")
                    token = i.get("token")
                    education_id = i.get("education_id")
                    periods = json.loads(i.get('periods'))
                    task = request(user_id=user_id, token=token, education_id=education_id, session = session, periods=periods)
                    tasks.append(task)
                await asyncio.gather(*tasks)
        except Exception as Ex:

            await bot.send_message(chat_id=756042979, text=f'Произошла ошибка в функции on_startup, либо request: {Ex}')
        await asyncio.sleep(1200)

async def on_startup(dp):
    dp.loop.create_task(check_requests())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup, timeout=60)