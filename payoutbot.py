def create_mirror_of_payout_bot(token):
    import asyncio
    import logging
    from datetime import timedelta, datetime
    import json
    from aws import sns, aws_region, aws_access_key_id, aws_secret_access_key
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
    from aiobotocore.session import get_session
    import requests
    from diction import active_chats
    from config_for_bots import payout_for_admins_bot_token
    from main import API_TOKEN
    from monobank import cryptomus
    admintoken = API_TOKEN
    admin_chat_id = '881704893'
    # API_TOKEN = '6686215620:AAHPv-qUVFsAKH4ShiaGNfZWd0fHVYCX2qg'
    API_TOKEN = token
    from aws import sqs
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(bot)
    dp.middleware.setup(LoggingMiddleware())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    @dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('approve_payout_') or callback_query.data.startswith('disapprove_payout'))
    async def approve_or_disapprove_payout(query:types.CallbackQuery):
        await query.message.answer('dsdfdsf')
        decision = query.data.split('_')[0]
        order_id = int(query.data.split('_')[2])

        payout = session.query(Payouts).filter(Payouts.order_id == order_id).first()
        worker = session.query(Worker).filter(Worker.telegram_id == payout.worker_id).first()
        if decision == 'approve':
            worker.balance -= payout.amount
            session.commit()
            data = {
                'chat_id': worker.telegram_id,
                'text': f'''
Ваш запрос на вывод был принят. Подробнее - @yuriy_bsrb
            '''
            }
            requests.get(url=f'https://api.telegram.org/bot{admintoken}/sendMessage', json=data)
            resp = await cryptomus({'amount':str(int(payout.amount)), 'currency' : payout.currency, 'order_id':str(payout.order_id), 'address' : payout.address,
                             'is_subtract':payout.is_subtract, 'network':payout.network, 'course_source':payout.course_source }, url='https://api.cryptomus.com/v1/payout')
        else:

            data = {
                'chat_id': worker.telegram_id,
                'text':f'''
Ва запрос на вывод был отклонен. Подробнее - @yuriy_bsrb
'''
            }
            '''
 v3iCEi27CxbNFSkPJCn2dnlRospRw7AiZktqpMINhM0npVmJvYtSAVr4uyyMxRS7mPAlSiFGVfeJEJIRN1vzlYMT814O8ILUondkcAwqxpeDu3csX7nii0Brc9lEuK2d           
            
            '''
            requests.get(url=f'https://api.telegram.org/bot{admintoken}/sendMessage', json=data)
            session.delete(payout)
            session.commit()

    from aiogram import executor

    storage = MemoryStorage()
    # Подключаем MemoryStorage к боту
    dp.storage = storage
    executor.start_polling(dp, skip_updates=True)