from pyrogram import Client, filters
from pyrogram.enums.parse_mode import ParseMode
from config import api_id, api_hash, api_hash_for_gorilla, api_id_for_gorilla, api_hash_for_valeria, api_id_for_valeria
import asyncio
import logging
import time
import asyncio
import threading
from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, DateTime, Boolean, ForeignKey,ARRAY, Table, MetaData
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship

Base = declarative_base()


ids = set()
class ChatsForDistribution(Base):
    __tablename__ = 'chats_for_distribution'
    chat_telegram_id = Column(Integer, primary_key=True)

class ChatsForDatabase(Base):
    __tablename__ = 'chats_for_database'
    link = Column(String, primary_key=True)

    category = Column(String)
    region = Column(String)
    num_of_members = Column(Integer)
    telegram_id = Column(Integer)


engine = create_engine('sqlite:///mydatabase.db')


Base.metadata.create_all(engine)
# Создаем сессию SQLAlchemy
Session = sessionmaker(bind=engine)
session = Session()
metadata = MetaData()

logging.basicConfig(level=logging.INFO)
app = Client('my_account_valeria', api_id= api_id, api_hash=api_hash)

chat_id = 189165596

async def send_message():
    while True:
        await app.send_message(chat_id, "Ебать зацени рассылку")
        await asyncio.sleep(0.25)

async def process_favorite_messages():
    # Получаем избранные сообщения

    ids = {}
    # Проходимся по каждому сообщению
    async for message in app.get_chat_history(chat_id=chat_id):
        try:
            short_link = message.text.split('@')[1].split('\n')[0]
            chat_name = f"https://t.me/{short_link}"
            chat = session.query(ChatsForDatabase).filter(ChatsForDatabase.link == chat_name).first()

            id = int(message.text.split('\n')[0].replace('👥', '').replace('\u2063', ''))
            ids[chat_name] = id
            if chat:
                print(chat.link)
                chat.telegram_id = id

            session.commit()
        except:
            ''
    return ids


async def process_sergey():

    async for message in app.get_chat_history(chat_id=782266258):
        try:
            id = message.text.split('id: -')[1]
            id = -int(id)
            ids.add(id)
        except:
            'ok'
def get_members_of_chat(chat_id, quantity=50):
    members = []
    with app:
        for message in (app.get_chat_history(chat_id)):
            if len(members)>quantity:
                break
            members.append(message.from_user.id)
        return members

async def distribute_black_cats():

    while True:
        try:
            template = '''
**😩ЗАЕБАЛСЯ СИДЕТЬ БЕЗ ДЕНЕГ?😩

💵💸💲ХОЧЕШЬ ЗАРАБОТАТЬ БЕЗ ВЛОЖЕНИЙ НЕ ВЫХОДЯ ИЗ ДОМА?💲💸💵

ТЕБЕ КО МНЕ😏

🤥🦣САМЫЙ ДЕШЕВЫЙ БОТ ДЛЯ СКАМА МАММОНТОВ🦣🤥

РАБОТАЕТ ПО ВСЕМУ СНГ🇷🇺🇺🇦🇰🇿🇧🇾🇲🇩🇺🇿🇹🇲🇰🇬🇹🇯

БОТ🤖 ВКЛЮЧАЕТ В СЕБЯ АДМИН ПАНЕЛЬ⌨️, ТРЕЙДИНГ БОТА💱💹, ЭСКОРТ БОТА💦🔞 и БОТА ДЛЯ ВЫПЛАТ

УСПЕЙ ЗАКАЗАТЬ ПО СКИДОЧНОЙ ЦЕНЕ**

__1 месяц - 100$
3 месяца - 250$
неограниченное время - 500$

ПИШИ В ЛС⬇__️
||@Karina_PR_manager||
    '''
            await app.send_message(chat_id=-1001348448051, text=template, parse_mode=ParseMode.MARKDOWN)
            await asyncio.sleep(60)
        except Exception as ex:
            print(ex)


async def distribute_other_chats(ids_of_chats):

    messages_sent = 0
    import os
    import random
    folder_path = 'photo/'
    files = os.listdir(folder_path)

    # Выбираем случайный файл из списка

    while True:
        random_file = random.choice(files)



        template_my = '''
**💵📣ТЫ ЗАКАЗАЛ РАССЫЛКУ, НО ТЕБЕ НИКТО И НЕ НАПИСАЛ?🤥😩**

**💹ТЕБЕ К НАМ😏**

**💯НАШИ ПРЕИМУЩЕСТВА😎**

__💾 Ежеминутно пополняющаяся БАЗА из более {500|1000|1500} РЕАЛЬНЫХ ЧАТОВ💬
💾БАЗА распределена по РЕГИОНАМ🌍 и КАТЕГОРИЯМ🔣
🤑10 КАТЕГОРИЙ ЧАТОВ на ВАШ выбор🫵
🌏РАБОТАЕМ ПО ВСЕМУ СНГ🌍
🔥ОТЗЫВЧИВАЯ и БЫСТРАЯ ТЕХ ПОДДЕРЖКА💯
✍️КОРРЕКТИРУЕМ и СОСТАВЛЯЕМ ТЕКСТ для ЭФФЕКТИВНОЙ РАССЫЛКИ✉️
🫵ВЫ можете НАБЛЮДАТЬ за процессом РАССЫЛКИ⌨__

**📬PACCЫЛKA ВAШEГО ОБЬЯВЛЕНИЯ ПО {700|1000|1200} ЧAТАМ КAЖДУЮ МИНУTУ**

__📚12 часов paccылки - 5$
📚1 День paccылки - 7$
📚3 Дня paccылки - 18$
📚7 Дней paccылки + ПРЕМИУМ(РАССЫЛКА ПО ЛС) - 60$__
||Полный Прайс в ЛС||

**🔔Рекламируем:**
__🔺Каналы
🔺Объявления о работе
🔺Реферальные ссылки
🔺Боты
🔺Сайты
И многое другое!__

**🔥Огромный приход!
🔥Классное оформление вашего поста, советы от настоящих профи!**

    '''
        template = '''
**🔥 АРЕНДА ВАШЕГО АККАУНТА АВИТО 🔥

❗️ВЛОЖЕНИЯ НЕ НУЖНЫ❗**️

``💸 Оплата 3.500 за 5 дней аренды + % с продажи!
⭐️ Минимальная занятость
😉 Все прозрачно и честно, никакого обмана!
✅Есть отзывы!
``
🔴 Работа не сложная, мы ищем людей, которые готовы сдать свой аккаунтна Avito.

** 📌Требования для аккаунта:📌**
``▫️Зарегистрирован более месяца назад``

**💳Формат оплаты:💳**
__- 5 дней аренды: 3.500 руб.
- 10 дней аренды: 7.500 руб.
- 30 дней аренды: 25.000 руб.__

**Оплата каждые 5 дней. Вы также получаете 2.5% от продаж.**

За подробностями: @arend_avit0
        '''
        for id_of_chat in ids_of_chats:
            try:

                await app.send_photo(id_of_chat, f'{os.path.join(folder_path, random_file)}', template_my)
                print(id_of_chat)
                messages_sent += 1
                await app.send_message(881704893, f'{messages_sent} сообщение было отправлено в чат {id_of_chat}')

                await asyncio.sleep(300 )


            except Exception as ex:
                try:
                    await app.send_message(id_of_chat, template_my)
                    messages_sent += 1
                    await app.send_message(881704893, f'{messages_sent} сообщение было отправлено в чат {id_of_chat}')
                    await asyncio.sleep(300)
                except:
                    print(ex)
                    print(id_of_chat)
                    await app.send_message(881704893, f'{ex}')


async def main(ids):
    # Запускаем две асинхронные функции в бесконечном цикле
    await asyncio.gather(distribute_other_chats(ids), distribute_black_cats())

def get_chats_2(ids):
        chats = set()
        with app:
            for message in app.get_chat_history(-1002031389938):
                try:
                    if message.forward_from.id == 850434834 and 'Chat id' not in message.text:
                        
                        

                        chats.add('@'+message.text.split('@')[1].split('\n')[0])

                except:
                    'ok'
        return list(chats)
def get_chats():
    with app:
        chats = set()
        for message in app.get_chat_history(-1002031389938):
            try:
                if '@' in message.text:

                    if message.forward_from.id == 6032759612:
                        for strin in message.text.split(' '):
                            if '@' in strin:
                                chats.add(strin.replace('🕑', '').replace('\n',''))
            except:
                'ok'

        chats = list(chats)
        return chats

async def print_in_chanel_chats():
    for chat in session.query(ChatsForDatabase).all()[100:]:
        if chat.telegram_id:
            await app.send_message(-1002024797560, text=chat.link)
            await asyncio.sleep(1)
if __name__ == "__main__":
    with app:
        ids_of_chats = []



        loop = asyncio.get_event_loop()

        #loop.run_until_complete(print_in_chanel_chats())

        #loop.run_until_complete(distribute_other_chats(ids_of_chats))
        #loop.run_until_complete(process_sergey())
        #ids =         loop.run_until_complete(process_favorite_messages())


        print(len(ids))

        session.commit()
        region_values = set()
        categories = set()
        chat_instances = session.query(ChatsForDatabase).all()
        for chat_instance in chat_instances:
            region_values.add(chat_instance.region)
            categories.add(chat_instance.category)
            ids_of_chats.append(chat_instance.telegram_id)

        print(len(ids_of_chats))
        loop.run_until_complete(distribute_other_chats(ids_of_chats))



        session.commit()

        #loop.run_until_complete(main(ids))




