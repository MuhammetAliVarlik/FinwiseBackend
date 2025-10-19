import yfinance as yf
from services.base_service import BaseService
from models.stock import Stock

class StockService(BaseService):
    def fetch_and_update_stock(self, symbol: str):
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info or "currentPrice" not in info:
            raise ValueError("Stock data not found")

        data = {
            "symbol": symbol.upper(),
            "company_name": info.get("longName", "Unknown"),
            "price": info.get("currentPrice", 0.0),
            "currency": info.get("currency", "USD")
        }

        stock = self.repo.get_by_symbol(symbol)
        if stock:
            for k, v in data.items():
                setattr(stock, k, v)
            self.repo.db.commit()
            self.repo.db.refresh(stock)
        else:
            stock = Stock(**data)
            self.repo.create(stock)

        return stock
