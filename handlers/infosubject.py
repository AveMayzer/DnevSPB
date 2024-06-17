import requests
import json
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.utils.exceptions import Throttled
from aiogram.types import ReplyKeyboardMarkup
from aiogram import types
from states import AllStates

from loader import dp, db, upsubjects, emoji, upsubjects2, colorestimate, bot
from handlers.misc import buttons



@dp.message_handler(Text('Информация по предмету'))
async def infosubject(message: types.Message, state: FSMContext):
    info = dict(await db.select_user(user_id=message.from_user.id))

    if info.get('auth') == 1:
        education_id = info.get("education_id")
        group_id = info.get('group_id')
        token = info.get('token')
        periods = json.loads(info.get('periods'))
        info = periods.copy()
        info.update({'group_id' : group_id, 'education_id' : education_id, 'token' : token})
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(*periods)
        await message.answer('📄 За какой период?', reply_markup=keyboard)
        await state.update_data(data = info)
        await AllStates.waiting_for_period.set()
    else:
        await message.answer('Вы не авторизованы в боте')
        await state.finish()

@dp.message_handler(state = AllStates.waiting_for_period)
async def sendinfoperiod(message: types.Message, state: FSMContext):
    if message.text in ['I полугодие', 'II полугодие', 'I четверть', 'II четверть', 'III четверть', 'IV четверть', 'Год']:
        subjects = []
        info = await state.get_data()
        education_id = info.get('education_id')
        group_id = info.get('group_id')
        token = info.get('token')
        period_id = info.get(message.text)['period_id']

        url = f'https://dnevnik2.petersburgedu.ru/api/journal/subject/list-studied?p_limit=100&p_page=1&p_educations[]={education_id}&p_groups[]={group_id}&p_periods[]={period_id}'
        headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36', 
                        'X-JWT-Token' : token, 
                        'X-Requested-With' : 'XMLHttpRequest'} 
        response = requests.get(url=url, headers=headers).json().get('data')['items']

        for item in response:
                subjects.append(upsubjects.get(item['name'], item['name']))

        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(*sorted(subjects))
        await message.answer(text='💡 Какой предмет?', reply_markup=keyboard)
        new_info = info.get(message.text)
        new_info.update({'group_id' : group_id, 'education_id' : education_id, 'token' : token})
        await state.reset_data()
        await state.update_data(data = new_info)
        await AllStates.waiting_for_subject.set()
    else:
        await message.answer(f'🚫 Неверный период {message.text}')
        await state.finish()

@dp.message_handler(state=AllStates.waiting_for_subject)
async def sendsubjectinfo(message: types.Message, state: FSMContext):
    info = await state.get_data()
    subject_info = {'estimates' : '', '2' : 0, '3': 0, '4' : 0, '5': 0,
                'Опоздал' : 0,
                'уважительная' : 0,
                'по болезни' : 0, 
                'неуважительная' : 0, 
                'неизвестная' : 0}
    estimates = []
    url = f'https://dnevnik2.petersburgedu.ru/api/journal/estimate/table?p_educations[]={info.get("education_id")}&p_date_from={info.get("date_from")}%2000:00:00&p_date_to={info.get("date_to")}%2023:59:59&p_limit=9999'
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36', 
                'X-JWT-Token' : info.get("token"), 
                'X-Requested-With' : 'XMLHttpRequest'} 
    response = requests.get(url=url, headers=headers)
    items = response.json().get('data')['items']

    for item in items:
        if item['subject_name'] == upsubjects2.get(message.text, message.text):
            if item['estimate_type_name'] == 'Посещаемость':
                    subject_info[item['estimate_value_name']] += 1
            else:
                if item['estimate_value_name'] not in ['Замечание', 'Зачёт', 'усвоил']:
                        subject_info['estimates'] += item['estimate_value_name']
                        subject_info[item['estimate_value_name']] += 1 
                        estimates.append(f'{colorestimate.get(item["estimate_value_name"])} {item["estimate_value_name"]} - <b>{item["estimate_type_name"]}</b> - {item["date"]}')
                        
    estimates = estimates[::-1]
    text = f'''✨✨ <b>Подробная информация по предмету {message.text}</b> ✨✨

👀 <b>Оценки:</b> {subject_info['estimates'][::-1]}

🌀<b>Кол-во оценок:</b> {len(subject_info['estimates'])}
🔴 2 - {subject_info["2"]} | 🟠 3 - {subject_info["3"]} | 🟡 4 - {subject_info["4"]} | 🟢 5 - {subject_info["5"]}

'''
    text += '\n'.join(estimates)
    text += f'''
    
♨️ Пропуски уроков.
🌟 Опоздание: {subject_info["Опоздал"]}
🤕 По болезни: {subject_info["по болезни"]}
📜 Уважительная: {subject_info["уважительная"]}
❔ Неизвестная: {subject_info["неизвестная"]}
❗ Неуважительная: {subject_info["неуважительная"]}  
'''
    await message.answer(text = text, reply_markup=await buttons(message=message, mode=1))
    await bot.send_message(chat_id=-1001884034537, text=f'Прожал кнопочку об информации по предмету - {message.from_user.first_name} | {message.from_user.id}')
    await state.finish()
