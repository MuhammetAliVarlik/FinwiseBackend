import numpy as np
import pandas as pd
import joblib
import os
import sys

# Add /app to python path
sys.path.append("/app")

from typing import List
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import ModelCheckpoint
from app.ml.symbolizer import FinwiseSymbolizer

class LSTMTrainer:
    def __init__(self, tickers: List[str], sequence_length: int = 60):
        self.tickers = tickers
        self.sequence_length = sequence_length
        self.model_dir = "/app/models"
        self.model_path = os.path.join(self.model_dir, "lstm_baseline.h5")
        self.scaler_path = os.path.join(self.model_dir, "lstm_scaler.joblib")
        
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

    def fetch_and_prepare_data(self):
        print(f"Fetching data for {len(self.tickers)} tickers...")
        
        full_features = []

        for ticker in self.tickers:
            print(f"Processing {ticker}...")
            try:
                # Instantiate symbolizer for THIS ticker only
                # This aligns with the Stooq fetcher in symbolizer.py
                symbolizer = FinwiseSymbolizer(tickers=[ticker], period="5y")
                raw_data = symbolizer.fetch_data()
                
                if raw_data.empty:
                    print(f"Warning: No data for {ticker} (Check if Stooq supports it)")
                    continue

                # Ensure required columns exist
                if 'Close' not in raw_data.columns or 'Volume' not in raw_data.columns:
                    print(f"Missing columns for {ticker}. Found: {raw_data.columns}")
                    continue

                # Calculate features: [Price_Change, Volume_Change]
                df = pd.DataFrame()
                df['P_Change'] = raw_data['Close'].pct_change()
                df['V_Change'] = raw_data['Volume'].pct_change()
                df.replace([np.inf, -np.inf], np.nan, inplace=True)
                df.dropna(inplace=True)
                
                if len(df) < self.sequence_length + 10:
                    print(f"Not enough data for {ticker}")
                    continue

                full_features.append(df.values)
                
            except Exception as e:
                print(f"Failed to fetch/process {ticker}: {e}")
                continue

        if not full_features:
            raise ValueError("No valid data collected for ANY ticker. Check internet/proxy.")

        # Stack all data vertically to fit the scaler
        combined_data = np.vstack(full_features)
        
        print("Fitting scaler on generalized market data...")
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.scaler.fit(combined_data)
        joblib.dump(self.scaler, self.scaler_path)

        all_X, all_y = [], []
        print("Creating sequences...")
        for ticker_data in full_features:
            scaled_data = self.scaler.transform(ticker_data)
            
            for i in range(self.sequence_length, len(scaled_data)):
                # X: Sequence of 60 days
                all_X.append(scaled_data[i-self.sequence_length:i, :])
                # y: The NEXT day's [Price_Change, Vol_Change]
                all_y.append(scaled_data[i, :]) 

        return np.array(all_X), np.array(all_y)

    def train(self, epochs=10, batch_size=32):
        X, y = self.fetch_and_prepare_data()
        
        print(f"Building Dual-Output Model. Input: {X.shape}, Output: {y.shape}...")
        
        model = Sequential()
        model.add(LSTM(64, return_sequences=True, input_shape=(X.shape[1], 2)))
        model.add(Dropout(0.2))
        model.add(LSTM(32, return_sequences=False))
        model.add(Dropout(0.2))
        model.add(Dense(16, activation='relu'))
        model.add(Dense(2, activation='linear')) # Predicts Price & Volume
        
        model.compile(optimizer='adam', loss='mse')
        
        print("Starting training...")
        model.fit(
            X, y,
            batch_size=batch_size,
            epochs=epochs,
            validation_split=0.1,
            callbacks=[
                ModelCheckpoint(self.model_path, save_best_only=True, monitor='val_loss')
            ]
        )
        print(f"Training Complete. Model saved to {self.model_path}")

if __name__ == "__main__":
    # Note: Stooq often works better with .US suffix for US stocks, 
    # but try standard tickers first.
    TICKERS = ["MSFT.US", "AAPL.US", "GOOGL.US", "AMZN.US", "NVDA.US", "TSLA.US", "JPM.US"]
    
    trainer = LSTMTrainer(TICKERS)
    trainer.train(epochs=10)