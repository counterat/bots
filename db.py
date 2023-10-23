from datetime import datetime
from random import randint
from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, DateTime, Boolean, ForeignKey,ARRAY
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
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
    children = relationship("Mammoth", back_populates="parent")


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
    order_id = Column(Integer)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.now())
    cryptomus_link = Column(String)
    uuid = Column(String, primary_key=True)

engine = create_engine('sqlite:///mydatabase.db')
Base.metadata.create_all(engine)
# Создаем сессию SQLAlchemy
Session = sessionmaker(bind=engine)
session = Session()

for lol in (session.query(Futures).all()):
    print(lol.is_increase)

mm = session.query(Mammoth).filter(Mammoth.belongs_to_worker == 881704893).all()
for m in mm:
    print(m.telegram_id)