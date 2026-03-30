from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.core.database import Base

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), unique=True, nullable=False)
    company_name = Column(String(255), nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String(3), nullable=False, server_default="USD")
    last_updated = Column(DateTime(timezone=True), nullable=False, server_default=func.now())