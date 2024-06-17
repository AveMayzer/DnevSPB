import datetime
from aiogram import types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.dispatcher.filters.builtin import CommandStart

from loader import dp, db, bot

@dp.message_handler(CommandStart())
async def message_start(message: types.Message):
    keyboard = None
    info = await db.select_user(user_id = message.from_user.id)
    if not info:
        updated_current_date = datetime.date.today().strftime('%d.%m.%Y')
        await db.add_user(user_id=message.from_user.id,
                        first_name=message.from_user.first_name,
                        date=updated_current_date, auth=0)
        keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Авторизоваться')]], resize_keyboard=True)
        await bot.send_message(chat_id=-1001884034537, text=f"[#bd] Добавил в базу данных {message.from_user.id} | {message.from_user.first_name} | {message.from_user.username}")

    elif dict(info).get("auth") == 0:
        keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Авторизоваться')]], resize_keyboard=True)

    await message.reply("\U0001F52E В общем, ботик для вывода оценок и т. д. (логины и пароли не храню если что). После авторизации более подробно написано будет.", reply_markup=keyboard)