from datetime import datetime
from random import randint
from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Worker(Base):
    __tablename__ = 'workers'

    telegram_id = Column(Integer, primary_key=True)
    name = Column(String)
    profit = Column(Float, default=0.0)
    balance = Column(Float, default=0.0)
    warnings = Column(Integer, default=0)
    payment_method = Column(String, default='Crypto USDT')
    created_at = Column(DateTime, default=datetime.utcnow)

class Mammoth(Base):
    __tablename__ = 'mammonths'
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

engine = create_engine('sqlite:///mydatabase.db')

# Создаем сессию SQLAlchemy
Session = sessionmaker(bind=engine)
session = Session()