
import aiohttp
from datetime import datetime
from loader import db, bot, colorestimate, emoji, upsubjects
from handlers.echo import check_upsubjects, get_subjects_info
from aiogram.types import ReplyKeyboardMarkup

async def request(education_id, user_id, token, session, periods):
        current_date = datetime.now()
        period = {}
        for k, v in periods.items():
            date_from = datetime.strptime(v['date_from'], '%d.%m.%Y')
            date_to = datetime.strptime(v['date_to'], '%d.%m.%Y')

            if date_from <= current_date <= date_to:
                period = v
                break

        url = f'https://dnevnik2.petersburgedu.ru/api/journal/estimate/table?p_educations[]={education_id}&p_date_from={period["date_from"]}%2000:00:00&p_date_to={period["date_to"]}%2023:59:59&p_limit=9999'
        headers = {'user-agent':  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
                    'X-JWT-Token' : f'{token}',
                    'X-Requested-With' : 'XMLHttpRequest'}
        
        async with session.get(url = url, headers = headers) as resp:
            if resp.status == 200:
                response = await resp.json()
                items = response.get('data')['items']
                message = '''<b>🌟🌟 Новая оценка 🌟🌟

❔оценка | предмет | тип | дата урока | изм. ср. балла
</b>
'''             
                subjects_info = await get_subjects_info(data=items, message = 'без разницы', mode = 2, user_id=user_id)
                subjects = subjects_info[0]
                new_estimates = subjects_info[2]
                if new_estimates:
                    print(user_id)
                    for k, v in new_estimates.items():
                        new_average = subjects[k].get('average_estimate')
                        old_counter = (subjects[k]['counter']) - len(new_estimates[k]['estimates'])
                        if old_counter == 0:
                            old_average = 0
                        else:
                            old_average = round((sum(map(int, subjects[k]['estimates'])) - sum(new_estimates[k]['estimates'])) / (old_counter), 2)
                        emojis = ''.join([colorestimate.get(str(estimate)) for estimate in new_estimates[k]['estimates']])
                        estimates = ', '.join(map(str, new_estimates[k]['estimates']))
                        estimate_types = ', '.join(new_estimates[k]['estimate_types'])
                        dates = ', '.join(new_estimates[k]['dates'])
                        message += f'<b>{emojis} {estimates} | {k} | {estimate_types} | {dates} | {old_average}</b> -> <b>{new_average}</b>\n\n'
                    await bot.send_message(chat_id=user_id, text = message)                       

            elif resp.status == 401:
                keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add('Авторизоваться')
                await db.change_auth(auth = 0, user_id=user_id)
                await bot.send_message(chat_id=user_id,
                                    text='❗Выбила ошибка 401 Unauthorized, это значит, что электронный дневник решил сбросить токен, поэтому тебе придётся снова авторизоваться.',
                                    reply_markup=keyboard)
                await bot.send_message(chat_id=-1001884034537, text=f'❗У пользователя {user_id} ошибка 401.')