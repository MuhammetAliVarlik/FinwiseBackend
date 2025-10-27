# app/models/stock.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.core.database import Base
from datetime import datetime

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    company_name = Column(String)
    price = Column(Float)
    currency = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)
