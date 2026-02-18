# app/services/stock_service.py
import asyncio
from pandas_datareader import data as pdr
from datetime import datetime, timedelta
from app.services.base_service import BaseService
from app.models.stock import Stock
import pandas as pd
import math
import logging
from app.repositories.stock_repository import StockRepository

logger = logging.getLogger(__name__)

class StockService(BaseService):
    def __init__(self, repository: StockRepository):
        self.repository = repository
    
    async def fetch_and_update_stock(self, symbol: str):
        start_date = datetime.now() - timedelta(days=10)
        search_symbol = symbol.upper()
        if "." not in search_symbol:
            search_symbol = f"{search_symbol}.US"
        
        try:
            # Run blocking Pandas IO in a separate thread
            df = await asyncio.to_thread(
                pdr.get_data_stooq, search_symbol, start=start_date
            )
        except Exception as e:
            raise ValueError(f"External API Error: {str(e)}")
        
        if df.empty:
            raise ValueError(f"Stock data not found for {symbol}")
        
        # Stooq returns Newest -> Oldest. We want the latest (first row).
        latest_data = df.iloc[0]
        current_price = float(latest_data['Close'])
        
        data = {
            "symbol": symbol.upper(),
            "company_name": symbol.upper(),
            "price": current_price,
            "currency": "USD"
        }

        # Update DB using the Async Repository
        stock = await self.repository.get_by_symbol(symbol)
        
        if stock:
            return await self.repository.update(stock, data)
        else:
            stock = Stock(**data)
            return await self.repository.create(stock)

    async def get_history(self, symbol: str, days: int = 100):
        """
        Fetches OHLCV data from Stooq (Live Data).
        Returns a list of dictionaries suitable for the Frontend Chart.
        """
        start_date = datetime.now() - timedelta(days=days)
        
        search_symbol = symbol.upper()
        if "." not in search_symbol:
            search_symbol = f"{search_symbol}.US"
            
        try:
            df = await asyncio.to_thread(
                pdr.get_data_stooq, search_symbol, start=start_date
            )
        except Exception:
             raise ValueError(f"Could not fetch history for {symbol}")
        
        if df.empty:
            raise ValueError(f"No historical data for {symbol}")

        # Sort Ascending (Oldest -> Newest) for Charts
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

    async def get_technical_analysis(self, symbol: str):
        """
        Calculates RSI, MACD, and SMA using pure Pandas.
        """
        try:
            # FIXED: Call 'self.get_history', NOT 'self.repository.get_history'
            # We are using Live Data from Stooq, not DB data.
            history = await self.get_history(symbol, days=100)
            
            if not history or len(history) < 50:
                return None

            # FIXED: history is already a list of dicts. Direct DataFrame creation.
            df = pd.DataFrame(history)
            
            # Ensure proper types for calculation
            df['close'] = df['close'].astype(float)
            
            # 2. Calculate SMA (Simple Moving Average)
            df['SMA_50'] = df['close'].rolling(window=50).mean()

            # 3. Calculate RSI (Relative Strength Index)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # 4. Calculate MACD
            exp12 = df['close'].ewm(span=12, adjust=False).mean()
            exp26 = df['close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp12 - exp26
            df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

            # 5. Get Latest Data
            latest = df.iloc[-1]
            
            # Helper to handle NaNs safely
            def safe_val(val, default=0):
                return val if not math.isnan(val) else default

            rsi_val = safe_val(latest['RSI'], 50)
            macd_val = safe_val(latest['MACD'], 0)
            signal_val = safe_val(latest['Signal_Line'], 0)
            sma_val = safe_val(latest['SMA_50'], latest['close'])
            close_price = latest['close']

            # 6. Interpret Signals
            rsi_status = "NEUTRAL"
            if rsi_val > 70: rsi_status = "OVERBOUGHT"
            elif rsi_val < 30: rsi_status = "OVERSOLD"

            trend = "BULLISH" if close_price > sma_val else "BEARISH"
            momentum = "POSITIVE" if macd_val > signal_val else "NEGATIVE"

            return {
                "symbol": symbol,
                "price": round(close_price, 2),
                "rsi": round(rsi_val, 2),
                "rsi_signal": rsi_status,
                "trend": trend,
                "momentum": momentum,
                "narrative": (
                    f"The stock {symbol} is trading at ${round(close_price, 2)}. "
                    f"Trend is {trend}. RSI is {round(rsi_val, 1)} ({rsi_status})."
                )
            }
        except Exception as e:
            logger.error(f"Technical Analysis Failed: {e}")
            return None