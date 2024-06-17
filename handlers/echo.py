import json
import aiohttp
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup
from aiogram.dispatcher.filters import ChatTypeFilter, Text

from loader import dp, db, upsubjects, emoji, bot



@dp.message_handler(ChatTypeFilter(chat_type=types.ChatType.PRIVATE), Text(['I полугодие', 'II полугодие', 'I четверть', 'II четверть', 'III четверть', 'IV четверть', 'Год']))
async def check_message(message: types.Message):
    information = dict(await db.select_user(user_id = message.from_user.id))

    if information.get('auth') == 1:
        periods = json.loads(information.get('periods'))
        messagee = message.text
        education_id = information.get("education_id")
        token = information.get("token")
        date_from = periods.get(message.text)['date_from']
        date_to = periods.get(message.text)['date_to']
              
        url = f'https://dnevnik2.petersburgedu.ru/api/journal/estimate/table?p_educations[]={education_id}&p_date_from={date_from}%2000:00:00&p_date_to={date_to}%2023:59:59&p_limit=9999'
        headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36', 
                'X-JWT-Token' : token, 
                'X-Requested-With' : 'XMLHttpRequest'} 
        async with aiohttp.ClientSession() as session:
            async with session.get(url = url, headers = headers) as resp:
                

                if resp.status == 401:
                    await db.change_auth(auth = 0, user_id=message.from_user.id)
                    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
                    keyboard.add('Авторизоваться')
                    await message.answer('Выбила ошибка Unauthorized, дневник решил сбросил токен и придется переавторизоваться в боте, поэтому сбрасываю авторизацию. Кнопка снизу.', reply_markup=keyboard)

                elif resp.status == 200:
                    response = await resp.json()
                    items = response.get('data')['items']
                    
                    estimates_message = f'<b>🔥🔥 Оценки за {message.text} 🔥🔥\n\n🔍 Предмет: оценки | Кол-во оценок | Ср. балл | Итог. балл</b>\n\n'
                    info = await get_subjects_info(data = items, message=messagee, mode = 1, user_id=message.from_user.id)
                    subjects = info[0]
                    information = info[1]
                    for k, v in sorted(subjects.items()):
                        estimates_message += f'<b>{emoji.get(k,"🔰")} {k}:</b> {v["estimates"]} | {v["counter"]} | {v["average_estimate"]} | <b>{v["final"]}</b>\n'
                    
                    estimates_message += f'\n<b>📊Кол-во оценок: {information["total_estimates"]} </b>\n🔴 2: {information["2"]} | 🟠 3: {information["3"]} | 🟡 4: {information["4"]} | 🟢 5: {information["5"]}\n\n<b>💫 Лучший предмет по ср. баллу:</b> {information["best_subject"]} <b>({information["best_average_estimate"]})</b>\n😟 <b>Худший предмет по ср. баллу:</b> {information["worst_subject"]} <b>({information["worst_average_estimate"]})</b>'

                    await message.answer(estimates_message)
                    await bot.send_message(chat_id=-1001884034537, text=f'Прожал кнопочку об оценках - {message.from_user.first_name} | {message.from_user.id}')

async def check_upsubjects(subject):
    return upsubjects.get(subject, subject)     # возвращет изменённое название предмета из словаря upsubjects, если нету, то возвращает тот-же предмет

async def get_subjects_info(data, message, mode, user_id):
    subjects = {} 
    estimates = {}
    information = {
        '2' : 0,
        '3' : 0,
        '4' : 0,
        '5' : 0,  
        'total_estimates' : 0,
        'worst_subject' : '',               
        'worst_average_estimate' : '',      
        'best_subject' : '',                
        'best_average_estimate' : ''} 
    for item in reversed(data):
        if item['estimate_value_name'] not in ['Замечание', 'Зачёт', 'усвоил'] and item['estimate_type_name'] != 'Посещаемость':
            if mode == 2: # mode 2 используется для функции автоматического запроса.
                info = await db.check_estimate_id(estimate_id=item["id"])
                if not info:
                    await db.add_estimate_id(estimate_id=item["id"], user_id=user_id)
                    item['subject_name'] = await check_upsubjects(item['subject_name'])
                    if item['subject_name'] not in estimates:
                        estimates.update({
                            item['subject_name']: {
                                'estimates': [int(item['estimate_value_name'])],
                                'dates': [item['date']],
                                'estimate_types': [item['estimate_type_name']]
                            }
                        })
                    else:
                        estimates[item['subject_name']]['estimates'].append(int(item['estimate_value_name']))
                        estimates[item['subject_name']]['dates'].append(item['date'])
                        estimates[item['subject_name']]['estimate_types'].append(item['estimate_type_name'])
            subject = await check_upsubjects(item['subject_name']) 
            if subject not in subjects: 
                subjects[subject] = {
                    'estimates' : item['estimate_value_name'],
                    'average_estimate' : 0,
                    'counter' : 0,
                    'final' : ''}

            elif item['estimate_type_name'].split()[-1] == message.split()[-1]: # проверка на полугодовые/четвертные оценки.
                subjects[subject]['final'] = item['estimate_value_name']
            else:
                subjects[subject]['estimates'] += item['estimate_value_name'] 

    for subject, data in subjects.items():

        for estimate in ['2', '3', '4', '5']: 
            information[estimate] += subjects[subject]['estimates'].count(estimate) 
        
        subjects[subject]['counter'] = len(subjects[subject]['estimates']) 
        subjects[subject]['average_estimate'] = round(sum(map(int, subjects[subject]['estimates'])) / subjects[subject]['counter'], 2) 
        
        if not information['worst_average_estimate'] or data['average_estimate'] < information['worst_average_estimate']:            
            information['worst_average_estimate'] = data['average_estimate'] 
            information['worst_subject'] = subject 
            
        if not information['best_average_estimate'] or data['average_estimate'] > information['best_average_estimate']: 
            information['best_average_estimate'] = data['average_estimate']
            information['best_subject'] = subject
        
        information['total_estimates'] += subjects[subject]['counter']
    return subjects, information, estimates

