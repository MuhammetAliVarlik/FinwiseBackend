from pandas_datareader import data as pdr
from datetime import datetime, timedelta
from services.base_service import BaseService
from models.stock import Stock

class StockService(BaseService):
    def fetch_and_update_stock(self, symbol: str):
        start_date = datetime.now() - timedelta(days=10)
        
        try:
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
                stock.last_updated = datetime.utcnow()
                self.repo.db.commit()
                self.repo.db.refresh(stock)
            else:
                stock = Stock(**data)
                self.repo.create(stock)

            return stock
            
        except Exception as e:
             print(f"HATA: {e}")
             raise ValueError(f"Error fetching stock data: {str(e)}")