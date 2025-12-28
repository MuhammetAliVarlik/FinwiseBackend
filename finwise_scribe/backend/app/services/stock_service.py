# app/services/stock_service.py
import asyncio
from pandas_datareader import data as pdr
from datetime import datetime, timedelta
from app.services.base_service import BaseService
from app.models.stock import Stock
import pandas as pd

class StockService(BaseService):
    
    async def fetch_and_update_stock(self, symbol: str):
        start_date = datetime.now() - timedelta(days=10)
        search_symbol = symbol.upper()
        if "." not in search_symbol:
            search_symbol = f"{search_symbol}.US"
        
        # CRITICAL: Run blocking Pandas IO in a separate thread
        # This prevents the API from freezing while waiting for Stooq
        try:
            df = await asyncio.to_thread(
                pdr.get_data_stooq, search_symbol, start=start_date
            )
        except Exception as e:
            # Handle connection errors gracefuly
            raise ValueError(f"External API Error: {str(e)}")
        
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

        # NEW: Await the async repo call
        stock = await self.repo.get_by_symbol(symbol)
        
        if stock:
            # Reuse the generic async update method from BaseRepository
            # This handles setattr, commit, and refresh internally
            return await self.repo.update(stock, data)
        else:
            stock = Stock(**data)
            return await self.repo.create(stock)

    async def get_history(self, symbol: str, days: int = 100):
        """Fetches OHLCV data for the frontend chart."""
        start_date = datetime.now() - timedelta(days=days)
        
        search_symbol = symbol.upper()
        if "." not in search_symbol:
            search_symbol = f"{search_symbol}.US"
            
        # CRITICAL: Run blocking Pandas IO in a separate thread
        try:
            df = await asyncio.to_thread(
                pdr.get_data_stooq, search_symbol, start=start_date
            )
        except Exception:
             raise ValueError(f"Could not fetch history for {symbol}")
        
        if df.empty:
            raise ValueError(f"No historical data for {symbol}")

        # Lightweight Charts expects ascending order (oldest -> newest)
        df = df.sort_index(ascending=True)
        
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