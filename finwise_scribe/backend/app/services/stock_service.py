# backend/app/services/stock_service.py
from pandas_datareader import data as pdr
from datetime import datetime, timedelta
from app.services.base_service import BaseService
from app.models.stock import Stock
import pandas as pd

class StockService(BaseService):
    def fetch_and_update_stock(self, symbol: str):
        # [Existing code remains the same]
        start_date = datetime.now() - timedelta(days=10)
        search_symbol = symbol.upper()
        if "." not in search_symbol:
            search_symbol = f"{search_symbol}.US"
        
        df = pdr.get_data_stooq(search_symbol, start=start_date)
        
        if df.empty:
            raise ValueError(f"Stock data not found for {symbol}")
        
        latest_data = df.iloc[0]
        current_price = float(latest_data['Close'])
        
        data = {
            "symbol": symbol.upper(),
            "company_name": symbol.upper(),
            "price": current_price,
            "currency": "USD"
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
    
    def get_history(self, symbol: str, days: int = 100):
        """Fetches OHLCV data for the frontend chart."""
        start_date = datetime.now() - timedelta(days=days)
        
        search_symbol = symbol.upper()
        if "." not in search_symbol:
            search_symbol = f"{search_symbol}.US"
            
        # Stooq returns data index descending (newest first)
        df = pdr.get_data_stooq(search_symbol, start=start_date)
        
        if df.empty:
            raise ValueError(f"No historical data for {symbol}")

        # Lightweight Charts expects ascending order (oldest -> newest)
        df = df.sort_index(ascending=True)
        
        # Convert to list of dicts for JSON response
        history = []
        for date, row in df.iterrows():
            history.append({
                "time": date.strftime('%Y-%m-%d'),
                "open": row['Open'],
                "high": row['High'],
                "low": row['Low'],
                "close": row['Close'],
                "volume": int(row['Volume'])
            })
            
        return history
