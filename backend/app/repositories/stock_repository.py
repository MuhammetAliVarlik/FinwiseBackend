# app/repositories/stock_repository.py
from app.repositories.base_repository import BaseRepository
from app.models.stock import Stock

class StockRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, Stock)

    def get_by_symbol(self, symbol: str):
        return self.db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
