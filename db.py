from datetime import datetime
from random import randint
from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, DateTime, Boolean, ForeignKey,ARRAY
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
import copy
Base = declarative_base()


class Worker(Base):
    __tablename__ = 'workers'
    service_id = Column(Integer, default=randint(100000000, 999999999))
    telegram_id = Column(Integer, primary_key=True)
    name = Column(String)
    profit = Column(Float, default=0.0)
    profit_quantity = Column(Integer, default=0)
    balance = Column(Float, default=0.0)
    warnings = Column(Integer, default=0)
    payment_method = Column(String, default='Crypto USDT')
    created_at = Column(DateTime, default=datetime.utcnow)
    mammonts = Column(String, default='')
    invited_worker = Column(String, default='')
    token = Column(String)
    token_for_escort_bot = Column(String)
    additional_models = Column(JSON)
    mammonts_from_escort = Column(String, default='')
    children = relationship("Mammoth", back_populates="parent")

class MammothFromEscort(Base):
    __tablename__ = 'mammonths_from_escort'
    first_name = Column(String)
    telegram_id = Column(Integer, primary_key=True)
    service_id = Column(Integer)
    balance = Column(Float, default=0.0)
    was_using_support = Column(Boolean, default=False)

class Mammoth(Base):
    __tablename__ = 'mammonths'
    first_name = Column(String)
    telegram_id = Column(Integer, primary_key=True)
    service_id = Column(Integer)
    balance = Column(Float, default=0.0)
    on_output = Column(Float, default=0.0)
    cryptoportfolio = Column(JSON, default={'btc': 0.0, 'eth': 0.0,'ltc':0.0})
    succesful_deals = Column(Integer, default=0)
    deals = Column(Integer, default=0)
    luck = Column(Integer, default=50)
    min_input_output_amount_value = Column(Integer, default=2000)
    created_at = Column(DateTime, default=datetime.now())
    belongs_to_worker = Column(Integer, ForeignKey('workers.telegram_id'))
    profit = Column(Float, default=0.0)
    was_using_support = Column(Boolean, default=False)

    parent = relationship("Worker", back_populates="children")
class Futures(Base):
    __tablename__ = 'futures'
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer)
    chat_id = Column(Integer)
    user_id = Column(Integer)
    cryptosymbol = Column(String)
    pool = Column(Float)
    is_increase = Column(Boolean)
    start_price = Column(Float)

class Withdraws(Base):
    __tablename__ = 'withdraws'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    card = Column(Integer)
    amount = Column(Float)

class Payouts(Base):
    __tablename__ = 'payouts'
    order_id = Column(Integer, primary_key=True)
    worker_id = Column(Integer)
    currency = Column(String, default='RUB')
    to_currency = Column(String, default='USDT')
    amount = Column(Float)
    address = Column(String)
    course_source = Column(String, default='Binance')
    is_subtract = Column(Boolean, default=False)
    network = Column(String, default='TRON')

class MammonthTopUpWithCrypto(Base):
    __tablename__ = 'mammonth_top_up_with_crypto'
    order_id = Column(String)
    mammonth_id = Column(Integer)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.now())
    cryptomus_link = Column(String)
    uuid = Column(String, primary_key=True)


class Sluts(Base):
    __tablename__ = 'sluts'
    slut_id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    prices = Column(JSON)
    description = Column(String)
    services = Column(String)

class ReviewsAboutSluts(Base):
    __tablename__ = 'reviews_about_sluts'
    review_id = Column(Integer, primary_key=True)
    slut_id = Column(Integer)
    name = Column(String)
    date = Column(DateTime)
    text = Column(String)


engine = create_engine('sqlite:///mydatabase.db')


Base.metadata.create_all(engine)
# Создаем сессию SQLAlchemy
Session = sessionmaker(bind=engine)
session = Session()

# slut1 = Sluts(name = 'Риана', age = 24, description = '''
# Королева минета, готова ублажить тебя до состояния умопомрачения, а также заставить тебя подчиняться. Люблю пожёстче))
# ''', services = '''МБР, окончание в рот, легкая доминация, садо-мазо''', prices={'Час':4600, "2 часа":8500, 'Ночь':21100 })
#
# slut2 = Sluts(name = 'Наташенька', age = 26, description = '''
# Жаркая малышка с очень аппетитными формами и сладкими дырочками. Показываю всю роскошсть своего тела и с удовольствием готова доставить тебе незабываемые эмоции🔥
# ''', services = '''Кунилингус, сексуальные костюмы, стриптиз''', prices={'Час':5300, "2 часа":9200, 'Ночь':21000 })
#
# slut3 = Sluts(name = 'Кристина', age = 22, description = '''
# Меня можно охарактеризовать несколькими словами: я похотливая девчонка и согласна на любые эксперименты для достижения обоюдного оргазма в постели))
# ''', services = '''МБР, анал, секс-игрушки, ролевые игры''', prices={'Час':4500, "2 часа":8000, 'Ночь':12600 })
#
# slut4 = Sluts(name = 'Настя', age = 24, description = '''
# Эта девочка обладает упругой попкой и заводным характером, то, что нужно попробовать каждому!
# ''', services = '''МБР, анал, фингеринг''', prices={'Час':6500, "2 часа":12000, 'Ночь':22300 })
#
# slut5 = Sluts(name = 'Вика', age = 24, description = '''
# Фингеринг, бондаж, окончание на грудь''', services = '''Фингеринг, бондаж, окончание на грудь''', prices={'Час':4500, "2 часа":8600, 'Ночь':18000 })
#
# slut6 = Sluts(name = 'Наташа', age = 27, description = '''
# Горячая и сексуальная девочка, способная удовлетворить каждого мужчину своими услугами)''', services = '''Анал, секс-игрушки, МБР, окончание в рот,
# окончание на грудь''', prices={'Час':8500, "2 часа":16100, 'Ночь':56400 })
#
# slut7 = Sluts(name = 'Валерия', age = 24, description = '''
# Широко известная в узких кругах Валерия сводит с ума наших клиентов уже на протяжении 2 лет. Пора перестать откладывать на потом, возьми все что хочешь прямо сейчас!
# ''', prices={'Час':12800, "2 часа":24200, 'Ночь':78600 }, services='''Анал, МБР, окончание в рот, окочание на грудь, фингеринг, кунилингус, секс-игрушки''')
#
# slut8 = Sluts(name = 'Юля', age = 23, description = '''
# Лучший вариант для тех, кто любит большую грудь и покорный характер. Юлечька сочетает в себе эти два преимущества, как никто другой😍
# ''', prices={'Час':10900, "2 часа":19500, 'Ночь':51500 }, services='''МБР, окончание на грудь, легкое подчинение''')
#
#
# session.add(slut1)
# session.add(slut2)
# session.add(slut3)
# session.add(slut4)
# session.add(slut5)
# session.add(slut6)
# session.add(slut7)
# session.add(slut8)
# session.commit()



# def return_datetime(date_str):
#     date_format = "%d.%m.%Y"
#     return datetime.strptime(date_str, date_format)
#
# list_for_reviews = []
# def save_in_db_review(review, slut_id=8):
#
#     processed_list = review.split('\n')[2:]
#     name = processed_list[0].split(' ')[0]
#     date = processed_list[0].split(' ')[1]
#     text = processed_list[1]
#     print(name,date,text)
#     slut_review = ReviewsAboutSluts(slut_id=slut_id, name=name, text=text,date=return_datetime(date))
#     session.add(slut_review)
#     session.commit()
#
# # for i in range(1,13):
# #     exec(f'''
# # session.add(review{i})
# # session.commit()
# #     ''')
# save_in_db_review(
#
# '''💕Отзывы о модели:
#
# Алексей 09.06.2019
# Сама безумно возбуждается и кайфует от процесса.
# ''')