# app/controllers/stock_controller.py
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.controllers.base_controller import BaseController
from app.repositories.stock_repository import StockRepository
from app.services.stock_service import StockService
from app.schemas.stock import StockBase
from app.core.database import get_db

# NEW: Async Dependency Injection
async def get_stock_service(db: AsyncSession = Depends(get_db)):
    repo = StockRepository(db)
    service = StockService(repo)
    return service

class StockController(BaseController):
    def __init__(self):
        super().__init__(prefix="/stocks", tags=["Stocks"])
        
        self.router.add_api_route(
            "/{symbol}", self.get_stock, methods=["GET"], response_model=StockBase
        )
        self.router.add_api_route(
            "/{symbol}/history", self.get_history, methods=["GET"]
        )

    # NEW: async def
    async def get_stock(self, symbol: str, service: StockService = Depends(get_stock_service)) -> StockBase:
        try:
            # NEW: await
            return await service.fetch_and_update_stock(symbol)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        
    # NEW: async def
    async def get_history(self, symbol: str, timeframe: str = "1D", service: StockService = Depends(get_stock_service)) -> List[Dict[str, Any]]:
        days_map = {"1D": 100, "1W": 365, "1Y": 1000}
        days = days_map.get(timeframe, 100)
        
        try:
            # NEW: await
            return await service.get_history(symbol, days)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))