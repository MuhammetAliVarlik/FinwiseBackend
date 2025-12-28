# app/repositories/stock_repository.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.models.stock import Stock

class StockRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Stock)

    async def get_by_symbol(self, symbol: str) -> Stock | None:
        # NEW: Async select syntax
        query = select(Stock).where(Stock.symbol == symbol.upper())
        result = await self.db.execute(query)
        return result.scalars().first()