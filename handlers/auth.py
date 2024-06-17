import json
import requests
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.utils.exceptions import Throttled
from states import AllStates

from loader import dp, db, bot
from handlers.misc import buttons

@dp.message_handler(Text(equals='Авторизоваться'))
async def auth(message: types.Message, state: FSMContext):
    try:
        await dp.throttle(str(message.from_user.id), rate = 60)
        info = dict(await db.select_user(user_id=message.from_user.id)) 

        if info.get('auth') == 0:
            await AllStates.waiting_for_email.set() # устанавливаем состояние ожидания ввода email
            await message.answer('Введите email')
    except Throttled:
        await message.answer('Команду можно использовать раз в одну минуту, чтобы избежать ограничений от дневника. (А то я один раз удивился, когда вылезла ошибка: ваш аккаунт заблокирован.)')


@dp.message_handler(state=AllStates.waiting_for_email)
async def email_auth(message: types.Message, state: FSMContext):
    email = message.text
    await state.update_data(email=email)
    await AllStates.waiting_for_password.set()
    await message.answer("Введите пароль")

async def totalauth(person, headers, user_id, choice = 1):
    url = 'https://dnevnik2.petersburgedu.ru/api'
    person = person[choice - 1]
    education_id, group_id = person['educations'][0]['education_id'], person['educations'][0]['group_id']
    response = requests.get(url=url + f'/journal/estimate/table?p_educations[]={education_id}&p_date_from=01.09.2023%2000:00:00&p_date_to=31.08.2024%2023:59:59&p_limit=9999',
                                    headers=headers).json()
    items = response.get('data')['items']   

    for item in items[::-1]:
        if item['estimate_value_name'] not in ['Замечание', 'Зачёт', 'усвоил'] and item['estimate_type_name'] != 'Посещаемость':
            info = await db.check_estimate_id(estimate_id=item["id"]) 

            if not info:
                await db.add_estimate_id(estimate_id=item["id"], user_id=user_id)
    response = requests.get(url=url + f'/group/group/get-list-period?p_group_ids%5B%5D={group_id}&p_page=1', 
                                    headers=headers).json()    
    items = response['data']['items'] 
    periods = {}

    for period in items:
        if period['name'] != 'Каникулы':
            period_id = period['identity']['id']
            periods.update({period["name"] : {'date_from' : period['date_from'],
                            'date_to' : period['date_to'], 'period_id' : period_id}})
            
    await db.update_auth(auth=1, education_id=education_id, token=headers.get('X-JWT-Token'), group_id=group_id, periods=json.dumps(periods), user_id=user_id)
    await bot.send_message(chat_id=-1001884034537, text=f'♥ Пользователь авторизовался в боте | {user_id}') 
    await bot.send_message(chat_id=user_id, text = '''✔️ Авторизация на сайте прошла успешно. Теперь можете пользоваться кнопками и прочитать информацию чуть ниже.
✨ Если что, логины и пароли у меня нигде не хранятся (пока что я не хочу нести за это ответственность :)), но у меня хранится как минимум токен авторизации (ключ) — самое необходимое для сбора данных с дневника, а также служебная информация: айди ученика, айди класса, айди оценки итп. Но стоит учитывать, что дневник через месяц сбросит токен, и вам придется снова авторизоваться (из-за моей политики не хранить логины и пароли), это дело 10 секунд, можете просто сообщение закрепить. Бот вас уведомит, если авторизация слетит. 
❗ К слову, бот сильно зависим от дневника, оно и понятно, потому что программа оттуда собирает информацию. Если бот не отвечает с 1 раза - не стоит по 1000 раз нажимать кнопку, скорее всего проблема на стороне дневника (либо я забыл оплатить хостинг).
🔷 Помимо вывода оценок, также в боте реализован автоматический запрос, в котором бот уведомит о новой оценке в дневнике. В общем, пользуйтесь! 💖''',
                            reply_markup=await buttons(message='', mode=1, user_id=user_id))

@dp.message_handler(state=AllStates.waiting_for_password)
async def auth_password(message: types.Message, state: FSMContext):
    try:
        url = 'https://dnevnik2.petersburgedu.ru/api' 
        password = message.text       
        info = await state.get_data() 
        email = info.get('email')
        data = {
            'login' : email, 
            'password' : password, 
            'type' : 'email'}
        headers = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
            'Content-Type': 'application/json, charset=utf-8',
            'Connection' : 'keep-alive',
            'X-Requested-With' : 'XMLHttpRequest'}
        
        response = requests.post(url=url + '/user/auth/login',
                                headers=headers,
                                data=json.dumps(data))    
        
        if response.status_code == 200:
            token = response.json()['data']['token']      
            headers.update({'X-JWT-Token' : token})

            response = requests.get(url=url + '/journal/person/related-child-list?p_page=1',
                                    headers=headers).json()  
        
            person = response['data']['items']
            if len(person) > 1:
                text = '❗️ На аккаунте зарегистрировано несколько учеников, выберите одного.'
                for k, v in enumerate(person, start=1):
                    student = v["firstname"] + ' ' + v["surname"]
                    text += f'\n🔆 {k} {student}'

                buttonss = [str(i) for i in range(1, len(person) + 1)]
                keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(*buttonss)
                await state.update_data(person=person, headers=headers)
                await message.answer(text=text, reply_markup=keyboard)
                await AllStates.waiting_for_student.set()

            else:
                await totalauth(person=person, user_id=message.from_user.id, headers=headers)  
                await state.finish()

        else:
            await state.finish()
            await bot.send_message(chat_id=-1001884034537,
                                   text=f'❓ У пользователя выбила ошибка при авторизации {response.json()["validations"][0]["message"]} | {message.from_user.id}')
            await message.answer(f'‼️ Произошла ошибка: {response.json()["validations"][0]["message"]}')

    except Exception as Ex:
        await state.finish()
        
@dp.message_handler(state=AllStates.waiting_for_student)
async def wait_student(message: types.Message, state: FSMContext):
    info = await state.get_data()
    person = info.get('person')
    headers = info.get('headers')
    await totalauth(person=person, user_id=message.from_user.id, headers=headers, choice=int(message.text))
    await state.finish()