# app/controllers/stock_controller.py
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from controllers.base_controller import BaseController
from repositories.stock_repository import StockRepository
from services.stock_service import StockService
from schemas.stock import StockBase
from core.database import SessionLocal

class StockController(BaseController):
    def __init__(self):
        super().__init__(prefix="/stocks", tags=["Stocks"])
        self.router.get("/{symbol}", response_model=StockBase)(
            lambda symbol, service=Depends(self._get_service): self.get_stock(symbol, service)
        )

    def _get_service(self) -> StockService:
        db: Session = SessionLocal()
        try:
            repo = StockRepository(db)
            service = StockService(repo)
            yield service
        finally:
            db.close()

    def get_stock(self, symbol: str, service: StockService):
        try:
            return service.fetch_and_update_stock(symbol)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
