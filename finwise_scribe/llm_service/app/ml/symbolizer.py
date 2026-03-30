import pandas as pd
import numpy as np
import pandas_datareader.data as web
from datetime import datetime, timedelta

try:
    import pandas_ta as ta
except Exception:  # pragma: no cover - optional dependency in some environments
    ta = None

class FinwiseSymbolizer:
    def __init__(self, tickers=None, period="2y", n_quantiles=10):
        self.tickers = tickers if tickers else ["SPY"]
        self.period = period
        self.n_quantiles = int(n_quantiles)
        if self.n_quantiles < 2:
            raise ValueError("n_quantiles must be >= 2")
        self.price_labels = [f"P_{i}" for i in range(self.n_quantiles)]
        self.volume_labels = [f"V_{i}" for i in range(self.n_quantiles)]

    def _get_start_date(self):
        """Convert period string (e.g. '2y', '1y') to a datetime object."""
        today = datetime.now()
        if self.period == "10y":
            return today - timedelta(days=10*365)
        elif self.period == "5y":
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
        [KEPT INTACT] Calculates RSI, MACD, and Trend indicators to match the Backend.
        This allows the LLM to 'see' the same chart data the user sees.
        """
        if df.empty or len(df) < 50:
            return {}

        data = df.copy()
        close = data['Close']

        # Prefer pandas-ta for stable indicator primitives, fallback to native pandas.
        if ta is not None:
            data['SMA_50'] = ta.sma(close, length=50)
            data['RSI'] = ta.rsi(close, length=14)
            macd_df = ta.macd(close, fast=12, slow=26, signal=9)
            if macd_df is not None and not macd_df.empty:
                data['MACD'] = macd_df.get('MACD_12_26_9')
                data['Signal'] = macd_df.get('MACDs_12_26_9')
            else:
                data['MACD'] = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
                data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
        else:
            data['SMA_50'] = close.rolling(window=50).mean()
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            exp12 = close.ewm(span=12, adjust=False).mean()
            exp26 = close.ewm(span=26, adjust=False).mean()
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

        macd_hist = (latest['MACD'] - latest['Signal']) if pd.notna(latest['MACD']) and pd.notna(latest['Signal']) else 0
        macd_state = "MACD_BULLISH" if macd_hist > 0 else "MACD_BEARISH"
        trend_token = f"TREND_{trend_status}"
        rsi_token = "RSI_HIGH" if latest['RSI'] > 70 else ("RSI_LOW" if latest['RSI'] < 30 else "RSI_NEUTRAL")

        indicator_tokens = [
            rsi_token,
            trend_token,
            macd_state,
        ]
        
        return {
            "RSI": round(latest['RSI'], 2),
            "RSI_SIGNAL": rsi_status,
            "TREND": trend_status,
            "MACD_HIST": round(macd_hist, 4),
            "PRICE": round(latest['Close'], 2),
            "INDICATOR_TOKENS": indicator_tokens,
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

        # 2. Quantile tokenization with integer bin labels to avoid label/bin mismatch.
        try:
            p_bin = pd.qcut(data['P_Change'], self.n_quantiles, labels=False, duplicates='drop')
            v_bin = pd.qcut(data['V_Change'], self.n_quantiles, labels=False, duplicates='drop')
        except ValueError:
            # Fallback to rank method if data lacks variance
            p_bin = pd.qcut(data['P_Change'].rank(method='first'), self.n_quantiles, labels=False, duplicates='drop')
            v_bin = pd.qcut(data['V_Change'].rank(method='first'), self.n_quantiles, labels=False, duplicates='drop')

        p_token = "P_" + p_bin.fillna(0).astype(int).astype(str)
        v_token = "V_" + v_bin.fillna(0).astype(int).astype(str)

        # 3. Create Composite Token
        data['Token'] = p_token.astype(str) + "_" + v_token.astype(str)
        
        # 4. Calculate Technical Indicators
        indicators = self.calculate_technicals(df)

        # Return: Data, Indicators (Dict), Token Series
        return data, indicators, data['Token']