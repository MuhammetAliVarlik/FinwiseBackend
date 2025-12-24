import pandas as pd
import numpy as np
import pandas_datareader.data as pdr
from datetime import datetime, timedelta

class FinwiseSymbolizer:
    def __init__(self, tickers, period="5y", n_quantiles=5):
        self.tickers = tickers
        self.period = period
        self.q = n_quantiles

    def fetch_data(self):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*2) # Fetch last 2 years
        
        data_frames = []
        for ticker in self.tickers:
            search_symbol = ticker if "." in ticker else f"{ticker}.US"
            try:
                df = pdr.get_data_stooq(search_symbol, start=start_date, end=end_date)
                if not df.empty:
                    df = df.sort_index() # Ensure ascending order
                    df['Ticker'] = ticker
                    data_frames.append(df)
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
                
        return pd.concat(data_frames) if data_frames else pd.DataFrame()

    def process(self, df):
        if df.empty:
            return None, None, pd.Series()
            
        # Simple discretization logic (Simplified for Microservice)
        df['Return'] = df['Close'].pct_change()
        df['Vol_Change'] = df['Volume'].pct_change()
        
        # Drop NaN
        df = df.dropna()

        # Define Tokens
        conditions = [
            (df['Return'] > 0.02) & (df['Vol_Change'] > 0.5), # P_SURGE_V_HIGH
            (df['Return'] > 0.01),                            # P_SURGE
            (df['Return'] < -0.02) & (df['Vol_Change'] > 0.5),# P_CRASH_V_HIGH
            (df['Return'] < -0.01),                           # P_CRASH
        ]
        choices = ['P_SURGE_V_HIGH', 'P_SURGE', 'P_CRASH_V_HIGH', 'P_CRASH']
        
        df['Token'] = np.select(conditions, choices, default='P_STABLE')
        
        return df, None, df['Token']