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
            return today - timedelta(days=365)

    def fetch_data(self):
        if not self.tickers: return pd.DataFrame()
        
        ticker = self.tickers[0]
        start_date = self._get_start_date()
        
        try:
            # Use pandas_datareader (Stooq)
            data = web.DataReader(ticker, 'stooq', start=start_date)
            
            # CRITICAL: Stooq returns data newest-first. We need oldest-first.
            data = data.sort_index(ascending=True)
            
            return data
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return pd.DataFrame()

    def calculate_technicals(self, df: pd.DataFrame) -> dict:
        """
        [NEW] Calculates RSI, MACD, and Trend indicators to match the Backend.
        This allows the LLM to 'see' the same chart data the user sees.
        """
        if df.empty or len(df) < 50:
            return {}

        data = df.copy()

        # 1. SMA 50 (Trend Baseline)
        data['SMA_50'] = data['Close'].rolling(window=50).mean()

        # 2. RSI 14 (Overbought/Oversold)
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # 3. MACD (Momentum)
        exp12 = data['Close'].ewm(span=12, adjust=False).mean()
        exp26 = data['Close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = exp12 - exp26
        data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

        # 4. Extract Latest Values
        latest = data.iloc[-1]
        
        # 5. Interpret for LLM Context
        rsi_status = "NEUTRAL"
        if latest['RSI'] > 70: rsi_status = "OVERBOUGHT"
        elif latest['RSI'] < 30: rsi_status = "OVERSOLD"

        # Simple Trend Logic
        trend_status = "BULLISH" if latest['Close'] > latest['SMA_50'] else "BEARISH"
        
        return {
            "RSI": round(latest['RSI'], 2),
            "RSI_SIGNAL": rsi_status,
            "TREND": trend_status,
            "MACD_HIST": round(latest['MACD'] - latest['Signal'], 4),
            "PRICE": round(latest['Close'], 2)
        }

    def process(self, df: pd.DataFrame):
        """
        Converts Price & Volume data into Composite Tokens AND calculates Indicators.
        """
        if df.empty: return df, {}, pd.Series()

        data = df.copy()
        
        # 1. Calculate Changes
        data['P_Change'] = data['Close'].pct_change()
        data['V_Change'] = data['Volume'].pct_change()
        data.dropna(inplace=True)

        # 2. Define Conditions
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
        
        # 4. [NEW] Calculate Technical Indicators
        # We perform this AFTER dropna() so we have valid change data, 
        # but we might need the original DF length for SMA. 
        # Ideally, pass the original 'df' to calculate_technicals.
        indicators = self.calculate_technicals(df)

        # Return: Data, Indicators (Dict), Token Series
        return data, indicators, data['Token']