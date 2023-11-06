
def create_mirror_of_escort_bot(token, admin_id):
    import os
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
    from aiogram.types import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, InputFile,InputMediaPhoto
    from aiogram.dispatcher.filters.state import State, StatesGroup
    from db import Worker, session, Mammoth, Futures, Withdraws,  MammonthTopUpWithCrypto, Sluts, ReviewsAboutSluts
    from img import generate_profile_stats_for_worker
    from aws import sns, aws_region, aws_access_key_id, aws_secret_access_key
    from main import API_TOKEN, support_team
    from diction import active_chats
    from config_for_bots import payout_for_admins_bot_token
    TOKEN_FOR_MAIN = API_TOKEN

    def show_kb_after_start_command(message_id, chat_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('Модели', callback_data=f'show_models'))
        return markup
    def show_kb_for_model(folder_path:str, photo_id, review_index=0):
        slut_id = int(folder_path.split('slut')[-1])
        markup = InlineKeyboardMarkup()
        if review_index ==0:

            markup.add(InlineKeyboardButton('Заказать', callback_data=f'book_a_slut_{folder_path}'))
            markup.add(InlineKeyboardButton('Написать', callback_data=f'send_message_to_slut_{folder_path}'))
            markup.add(InlineKeyboardButton('Отзывы', callback_data=f'reviews_about_slut_{folder_path}_{review_index}'))
            if photo_id > 0:
                markup.add(InlineKeyboardButton('Следуещее фото', callback_data=f'next_photo_of_slut_{folder_path}_{photo_id}'), InlineKeyboardButton('Предыдущее фото', callback_data=f'next_photo_of_slut_{folder_path}_{photo_id-2}'))
            else:
                markup.add(InlineKeyboardButton('Следуещее фото', callback_data=f'next_photo_of_slut_{folder_path}_{photo_id}'))

            markup.add(InlineKeyboardButton('Следующая', callback_data=f'next_slut_slut{slut_id+1}'))
            if folder_path.split('/')[-1] != 'slut1':
                markup.add(InlineKeyboardButton('Предыдущая', callback_data=f'next_slut_slut{slut_id-1}'))

            markup.add(InlineKeyboardButton('В главное меню', callback_data='to_the_main_menu'))
        else:
            markup.add(InlineKeyboardButton('Следующий отзыв', callback_data=f'reviews_about_slut_{folder_path}_{review_index+1}'))
        return markup
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    admin_chat_id = admin_id
    API_TOKEN = token

    logging.basicConfig(level=logging.DEBUG)

    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(bot)
    dp.middleware.setup(LoggingMiddleware())




    @dp.message_handler(commands=['start'])
    async def start_handler(message:types.Message):
        with open('secretroom.jpg', 'rb') as image:
            await message.answer_photo(photo=InputFile(image), caption='''
Добро пожаловать в Secret Room!

У нас вы можете найти лучших девочек для интимных встреч.

Выдача адресов происходит круглосуточно через бота или, в крайних случаях, через куратора!

Внимательней проверяйте адрес Telegram, остерегайтесь мошенников, спасибо, что выбираете нас!
            
            ''', reply_markup=show_kb_after_start_command(message_id=message.message_id, chat_id=message.chat.id))

    @dp.callback_query_handler(lambda callback_query: callback_query.data=='show_models' or callback_query.data.startswith('next_slut_') or
                                                      callback_query.data.startswith('next_photo_of_slut_') or callback_query.data.startswith('reviews_about_slut_'))
    async def show_models_handler(query:types.CallbackQuery):
        new_query = query.data

        if query.data == 'show_models':
            folder_path = 'slut1'
            file_list = os.listdir('shlyuhi/' + folder_path)
            slut = session.query(Sluts).filter(Sluts.slut_id == 1).first()
        elif query.data.startswith('reviews_about_slut_'):
            folder_path = query.data.split('_')[-2]
            slut_id = int(folder_path.split('slut')[-1])
            slut = session.query(Sluts).filter(Sluts.slut_id == slut_id).first()
            reviews = session.query(ReviewsAboutSluts).filter(ReviewsAboutSluts.slut_id == slut_id).all()
            review_index =int(query.data.split('_')[-1])
            template = f'''
💕*Отзывы о модели*:

*{reviews[review_index].name}* {reviews[review_index].date}
_{reviews[review_index].text}_
            '''
            await query.message.edit_caption(template, parse_mode=ParseMode.MARKDOWN, reply_markup=show_kb_for_model(folder_path, photo_id=0,
                                                                                                                     review_index=review_index+1))

        elif query.data.startswith('next_photo_of_slut_'):
            folder_path = query.data.split('_')[-2]
            file_list = os.listdir('shlyuhi/' + folder_path)
            photo_id = int(new_query.split('_')[-1].split('slut')[-1])

            slut_id = int(folder_path.split('slut')[-1])
            slut = session.query(Sluts).filter(Sluts.slut_id == slut_id).first()
            with open('shlyuhi/' + folder_path + '/' + file_list[photo_id+1], 'rb') as image:
                await query.message.edit_media(media=InputMediaPhoto(image))
                template = f'''
🦋*{slut.name}* (Одесса)

*Возраст*: {slut.age}

🌇 *Час* — {slut.prices['Час']} RUB
🏙 *2 часа* — {slut.prices['2 часа']} RUB
🌃 *Ночь* — {slut.prices['Ночь']} RUB

{slut.description}

*Услуги*
_{slut.services}_
                            '''
                await query.message.edit_caption(template, parse_mode=ParseMode.MARKDOWN, reply_markup=show_kb_for_model(folder_path, photo_id=photo_id+1))

                return
        else:
            folder_path = query.data.split('_')[-1]
            file_list = os.listdir('shlyuhi/' +folder_path)
            slut = session.query(Sluts).filter(Sluts.slut_id == int(folder_path.split('slut')[-1])).first()

        with open('shlyuhi/' + folder_path + '/' + file_list[0], 'rb') as image:
            template = f'''
🦋*{slut.name}* (Одесса)

*Возраст*: {slut.age}

🌇 *Час* — {slut.prices['Час']} RUB
🏙 *2 часа* — {slut.prices['2 часа']} RUB
🌃 *Ночь* — {slut.prices['Ночь']} RUB

{slut.description}

*Услуги*
_{slut.services}_
            '''

            await query.message.edit_media( media=InputMediaPhoto(image))
            await query.message.edit_caption(template, parse_mode=ParseMode.MARKDOWN, reply_markup=show_kb_for_model(folder_path, photo_id=0))


    from aiogram import executor

    storage = MemoryStorage()
    # Подключаем MemoryStorage к боту
    dp.storage = storage
    executor.start_polling(dp, skip_updates=True)
