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
API_TOKEN = '6079104357:AAFrdpzM8pmSr2m6kcOOnu3ZbLYfKmFXZn0'
crypto_symbols = ['BTC', 'BCH', 'XRP', 'DOGE', 'ETH', 'BNB', 'LTC', 'LUNA', 'SOL', 'TRX', 'ADA', 'DOT', 'MATIC', 'XMR', 'EUR']
cryptocurrencies = ['bitcoin', 'bitcoin_cash', 'ripple', 'doge', 'ethereum', 'binance_coin', 'litecoin', 'terra', 'solana', 'tron', 'cardano', 'polkadot', 'polygon',
                    'polygon', 'monero', 'euro' ]


logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):



if __name__ == '__main__':
    from aiogram import executor

    storage = MemoryStorage()
    # Подключаем MemoryStorage к боту
    dp.storage = storage
    executor.start_polling(dp, skip_updates=True)


