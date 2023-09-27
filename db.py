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
    token = Column(String)
    children = relationship("Mammoth", back_populates="parent")


class Mammoth(Base):
    __tablename__ = 'mammonths'
    first_name = Column(String)
    telegram_id = Column(Integer, primary_key=True)
    service_id = Column(Integer, default=randint(100000000, 999999999))
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


engine = create_engine('sqlite:///mydatabase.db')
Base.metadata.create_all(engine)
# Создаем сессию SQLAlchemy
Session = sessionmaker(bind=engine)
session = Session()