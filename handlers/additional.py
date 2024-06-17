import json
import requests
from aiogram import types
from aiogram.dispatcher.filters import Text

from loader import dp, db

@dp.message_handler(Text(equals='Дополнительная информация'))
async def additional_information(message: types.Message):
    info = dict(await db.select_user(user_id=message.from_user.id))
    if info.get('auth') == 1:
        education_id = info.get('education_id')
        periods = json.loads(info.get('periods'))
        token = info.get('token')
        tgmessage = ''

        for k, v in periods.items():
            tgmessage += f"<b>💫 Посещаемость за {k}:</b>\n"
            url = f'https://dnevnik2.petersburgedu.ru/api/journal/estimate/table?p_educations[]={education_id}&p_date_from={v["date_from"]}%2000:00:00&p_date_to={v["date_to"]}%2023:59:59&p_limit=9999'
            response = requests.get(url=url, 
                                    headers={'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36', 
                                            'X-JWT-Token' : token, 
                                            'X-Requested-With' : 'XMLHttpRequest'}).json()
            data = response['data']['items']
            additions = {
                'Опоздал' : 0,
                'уважительная' : 0,
                'по болезни' : 0, 
                'неуважительная' : 0, 
                'неизвестная' : 0}
            
            for item in data:
                if item['estimate_type_name'] == 'Посещаемость':
                    additions[item['estimate_value_name']] += 1
            tgmessage += f'     🌟 Опоздание: {additions["Опоздал"]}\n     🤕 По болезни: {additions["по болезни"]}\n     📜 Уважительная: {additions["уважительная"]}\n     ❔ Неизвестная: {additions["неизвестная"]}\n     ❗ Неуважительная: {additions["неуважительная"]}\n\n'
        await message.answer(tgmessage)