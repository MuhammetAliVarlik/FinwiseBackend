# app/schemas/stock.py
from pydantic import BaseModel
from datetime import datetime

class StockBase(BaseModel):
    symbol: str
    company_name: str
    price: float
    currency: str
    last_updated: datetime

    class Config:
        orm_mode = True
