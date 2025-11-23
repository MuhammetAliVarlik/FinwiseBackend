import pandas as pd
import numpy as np
from pandas_datareader import data as pdr
from datetime import datetime, timedelta

# Sembolik Dil Tanımları (Modelin bildiği dil)
PRICE_QUANTILES = ["P_CRASH", "P_LOW", "P_MID", "P_HIGH", "P_SURGE"]
VOLUME_QUANTILES = ["V_LOW", "V_MID", "V_HIGH", "V_SURGE", "V_PEAK"]

class FinwiseSymbolizer:
    """
    Finansal veriyi çeker ve modelin anlayacağı sembolik dile çevirir.
    """
    def __init__(self, tickers, period="10y", n_quantiles=5):
        self.tickers = tickers
        self.period = period
        self.n_quantiles = n_quantiles
        self.price_labels = PRICE_QUANTILES[:n_quantiles]
        self.volume_labels = VOLUME_QUANTILES[:n_quantiles]

    def fetch_data(self):
        # Stooq üzerinden veri çekme (Daha stabil)
        start_date = datetime.now() - timedelta(days=365*10)
        all_data = []
        
        for ticker in self.tickers:
            try:
                search_symbol = f"{ticker}.US" if "." not in ticker else ticker
                df = pdr.get_data_stooq(search_symbol, start=start_date)
                
                if not df.empty:
                    df = df.sort_index(ascending=True)
                    # Sütun isimlerini standartlaştır
                    df = df[['Close', 'Volume']].rename(
                        columns={'Close': f'{ticker}_Close', 'Volume': f'{ticker}_Volume'}
                    )
                    all_data.append(df)
            except Exception as e:
                print(f"Uyarı: {ticker} verisi çekilemedi: {e}")
                
        if not all_data: 
            return pd.DataFrame()
            
        return pd.concat(all_data, axis=1).dropna()

    def process(self, df):
        pct_df = pd.DataFrame(index=df.index)
        tokens_df = pd.DataFrame(index=df.index)
        
        tickers = set([c.split('_')[0] for c in df.columns])
        
        for t in tickers:
            p_col, v_col = f"{t}_Close", f"{t}_Volume"
            if p_col not in df.columns: continue
            
            pct_df[f"{t}_P_Change"] = df[p_col].pct_change()
            pct_df[f"{t}_V_Change"] = df[v_col].pct_change()
            
        pct_df = pct_df.replace([np.inf, -np.inf], np.nan).dropna()
        
        # Tokenize Et
        for t in tickers:
            # qcut hatası verirse rank kullan (fallback)
            try:
                tokens_df[f"{t}_P_Token"] = pd.qcut(pct_df[f"{t}_P_Change"], self.n_quantiles, labels=self.price_labels, duplicates='drop')
                tokens_df[f"{t}_V_Token"] = pd.qcut(pct_df[f"{t}_V_Change"], self.n_quantiles, labels=self.volume_labels, duplicates='drop')
            except ValueError:
                tokens_df[f"{t}_P_Token"] = pd.qcut(pct_df[f"{t}_P_Change"].rank(method='first'), self.n_quantiles, labels=self.price_labels)
                tokens_df[f"{t}_V_Token"] = pd.qcut(pct_df[f"{t}_V_Change"].rank(method='first'), self.n_quantiles, labels=self.volume_labels)
            
        combined_tokens = []
        for t in tickers:
            combined_tokens.append(tokens_df[f"{t}_P_Token"].astype(str) + "_" + tokens_df[f"{t}_V_Token"].astype(str))
        
        final_text = pd.DataFrame(combined_tokens).T.agg(' '.join, axis=1)
        
        return pct_df, tokens_df, final_text