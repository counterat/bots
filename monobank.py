import requests
from bs4 import BeautifulSoup

from mamonts import show_all_currencies

token = 'u3dL8d8BJIbUvxNFME1wIOOGdb6BDWUlnX3_Zc9976dc'
import datetime
import time
# Создайте объект datetime для указанной даты и времени
date_time = datetime.datetime(2023, 8, 15, 23, 14)

# Преобразуйте в UNIX времени
unix_timestamp = int(date_time.timestamp())
header = {'X-Token':token}

import aiohttp
import asyncio


async def waiting_for_mamont_async(unix_timestamp, min_amount, token):
    start_time = time.time()

    header = {'X-Token': token}
    interval_seconds = 20
    duration_seconds = 900

    async with aiohttp.ClientSession(headers=header) as session:
        while (time.time() - start_time) < duration_seconds:
            async with session.get(f'https://api.monobank.ua/personal/statement/wxgvgkFSeH5B9FHP9RtPPQ/{unix_timestamp}/') as resp:
                try:
                    data = await resp.json()
                    for transaction in data:
                        if transaction['amount'] >= min_amount / 100:
                            print(transaction)
                            print('всеее')
                            return
                except Exception as ex:
                    print(ex)

            await asyncio.sleep(interval_seconds)

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

async def main():
    ez = await fetch_usd_to_rub_currency()
    print(type(ez))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())