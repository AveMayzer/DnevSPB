import json
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup
from aiogram import types
from loader import dp, db, bot
from data.config import ADMIN
@dp.message_handler(commands=['chat'])
async def chatinfo (message: types.Message):
    await message.answer(f"Чат айди: {message.chat.id}\nТип чата: {message.chat.type}")

@dp.message_handler(commands='sendmsg', user_id = int(ADMIN))
async def sendmsg(message : types.Message):
    args = message.get_args().split(maxsplit=1)
    await bot.send_message(chat_id=args[0], text=args[1])
    await message.reply(f'Отправил')
    
@dp.message_handler(commands='auth', user_id=int(ADMIN))
async def admdeauth(message: types.Message):
    args = message.get_args().split()
    await db.change_auth(auth=int(args[1]), user_id=int(args[0]))
    await message.answer(f'Готово')


@dp.message_handler(commands=['buttons'])
async def buttons(message : types.Message, mode=0, user_id = None):
    if user_id == None:
        user_id = message.from_user.id
    info = dict(await db.select_user(user_id=user_id))

    if info.get('auth') == 1:
        periods = json.loads(info.get('periods'))
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*periods)
        keyboard.add('Дополнительная информация')
        keyboard.add('Информация по предмету')
        
        if mode:
            return keyboard
        else:
            await bot.send_message(chat_id=user_id, text = 'Перевызываю кнопки.', reply_markup=keyboard)
