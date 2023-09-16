import requests
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

