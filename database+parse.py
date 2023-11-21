from main import session, app, ChatsForDatabase
import pyautogui
import time
import requests
from bs4 import BeautifulSoup

def parse_info_from_tg_cats(key_word:str):
    link = f'https://tg-cat.com/?search={key_word}&type=supergroup'
    chats = {}
    all_chats = session.query(ChatsForDatabase).all()
    chat_links = []
    for chat_instance in all_chats:
        chat_links.append(chat_instance.link)
    try:
        response = requests.get(link)

        soup = BeautifulSoup(response.text, 'lxml')
        '📌'
        cols_of_chat = soup.findAll(class_='col-12 col-lg-9 pb-3')
        titles = []
        for col_of_chat in cols_of_chat:

            title = col_of_chat.find(class_='badge rounded-pill bg-light text-dark mr-1')


            try:
                text_title = title.find('a').text
                a = title.find('a')


                if not( "📌" in text_title or 'Разработка Телеграм ботов для бизнеса от 9000 руб.' in text_title):


                    num_of_members = int(col_of_chat.findAll(class_= 'badge rounded-pill bg-light text-dark mr-1')[1].text.split('members')[0].replace(',', ''))
                    link = a.get('data-url')
                    title_of_chat = a.text
                    print(link)
                    if link not in chat_links:

                        chat = ChatsForDatabase(link= link, category='entertainment',region='CIS', num_of_members=num_of_members)
                        session.add(chat)
                        titles.append(title_of_chat)
                        session.commit()
            except Exception:
                ''

        print(titles)
    except Exception as ex:
        print(ex)

all_chats = session.query(ChatsForDatabase).all()
chat_links = []
for chat_instance in all_chats:
    print(chat_instance.link)
    if chat_instance.telegram_id == None:
        print(chat_instance.link)
        chat_links.append(chat_instance.link)
session.commit()
print(chat_links)
from gui import paste_the_chat_links_to_the_bot
paste_the_chat_links_to_the_bot(chat_links)