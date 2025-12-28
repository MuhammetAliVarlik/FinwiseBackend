import pandas as pd
import numpy as np
import pandas_datareader.data as web
from datetime import datetime, timedelta

class FinwiseSymbolizer:
    def __init__(self, tickers=None, period="2y"):
        self.tickers = tickers if tickers else ["SPY"]
        self.period = period

    def _get_start_date(self):
        """Convert period string (e.g. '2y', '1y') to a datetime object."""
        today = datetime.now()
        if self.period == "5y":
            return today - timedelta(days=5*365)
        elif self.period == "2y":
            return today - timedelta(days=2*365)
        elif self.period == "1y":
            return today - timedelta(days=365)
        else:
            # Default to 1 year if unknown
            return today - timedelta(days=365)

    def fetch_data(self):
        if not self.tickers: return pd.DataFrame()
        
        ticker = self.tickers[0]
        start_date = self._get_start_date()
        
        try:
            # Use pandas_datareader (Source: Stooq is reliable/free for equities)
            data = web.DataReader(ticker, 'stooq', start=start_date)
            
            # CRITICAL: Stooq returns data newest-first. We need oldest-first.
            data = data.sort_index(ascending=True)
            
            return data
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()

    def process(self, df: pd.DataFrame):
        """
        Converts Price & Volume data into Composite Tokens: P_..._V_...
        """
        if df.empty: return df, None, pd.Series()

        data = df.copy()
        
        # 1. Calculate Changes
        data['P_Change'] = data['Close'].pct_change()
        data['V_Change'] = data['Volume'].pct_change()
        data.dropna(inplace=True)

        # 2. Define Conditions (Must match LSTM Engine logic)
        # Price Tokens
        p_conditions = [
            (data['P_Change'] >= 0.03),  # P_SURGE
            (data['P_Change'] <= -0.03), # P_CRASH
            (data['P_Change'] >= 0.01),  # P_HIGH
            (data['P_Change'] <= -0.01), # P_LOW
        ]
        p_choices = ['P_SURGE', 'P_CRASH', 'P_HIGH', 'P_LOW']
        data['P_Token'] = np.select(p_conditions, p_choices, default='P_MID')

        # Volume Tokens
        v_conditions = [
            (data['V_Change'] >= 0.20),  # V_SURGE
            (data['V_Change'] >= 0.10),  # V_PEAK
            (data['V_Change'] >= 0.05),  # V_HIGH
            (data['V_Change'] <= -0.05), # V_LOW
        ]
        v_choices = ['V_SURGE', 'V_PEAK', 'V_HIGH', 'V_LOW']
        data['V_Token'] = np.select(v_conditions, v_choices, default='V_MID')

        # 3. Create Composite Token
        data['Token'] = data['P_Token'] + "_" + data['V_Token']
        
        return data, None, data['Token']