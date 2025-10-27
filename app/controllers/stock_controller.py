# app/controllers/stock_controller.py
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.controllers.base_controller import BaseController
from app.repositories.stock_repository import StockRepository
from app.services.stock_service import StockService
from app.schemas.stock import StockBase
from app.core.database import SessionLocal


def get_stock_service():
    db: Session = SessionLocal()
    try:
        repo = StockRepository(db)
        service = StockService(repo)
        yield service
    finally:
        db.close()


class StockController(BaseController):
    def __init__(self):
        super().__init__(prefix="/stocks", tags=["Stocks"])
        self.router.add_api_route(
            "/{symbol}", self.get_stock, methods=["GET"], response_model=StockBase
        )

    def get_stock(self, symbol: str, service: StockService = Depends(get_stock_service)) -> StockBase:
        try:
            return service.fetch_and_update_stock(symbol)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
