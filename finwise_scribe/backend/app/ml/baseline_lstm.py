# app/ml/baseline_lstm.py

import numpy as np
import pandas as pd
import joblib
import os
from typing import List, Tuple
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping

# Import our symbolizer to get the numerical data
from symbolizer import FinwiseSymbolizer

class LSTMBaselineModel:
    """
    Implements a standard LSTM model for time series forecasting.
    This model uses numerical percentage change data (Price/Volume)
    to predict the next day's price change.
    
    It serves as a baseline to compare against the Finwise Scribe SLM.
    """
    
    def __init__(self, tickers: List[str], ticker_to_predict: str, sequence_length: int = 60):
        """
        Args:
            tickers (List[str]): List of all tickers to use as features.
            ticker_to_predict (str): The specific ticker symbol we want to forecast.
            sequence_length (int): How many past days of data to use for one prediction.
        """
        self.tickers = tickers
        self.ticker_to_predict = ticker_to_predict.upper()
        self.sequence_length = sequence_length
        self.n_features = len(tickers) * 2 # Price_Change and Volume_Change for each ticker
        self.target_col_index = self._get_target_col_index()
        
        self.model_dir = "models"
        self.model_path = os.path.join(self.model_dir, "lstm_baseline.h5")
        self.scaler_path = os.path.join(self.model_dir, "lstm_scaler.joblib")
        
        self.model = None
        self.scaler = None

        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

    def _get_target_col_index(self) -> int:
        """Finds the column index of the target variable (e.g., 'MSFT_P_Change')."""
        try:
            # We assume a specific column order from the symbolizer
            target_p_change = f"{self.ticker_to_predict}_P_Change"
            all_cols = []
            for t in self.tickers:
                all_cols.append(f"{t}_P_Change")
                all_cols.append(f"{t}_V_Change")
            return all_cols.index(target_p_change)
        except ValueError:
            raise ValueError(f"Target {self.ticker_to_predict} not in tickers list {self.tickers}")

    def _get_numerical_data(self) -> pd.DataFrame:
        """
        Fetches and processes the numerical percentage change data
        using the FinwiseSymbolizer.
        """
        print("Fetching numerical data for LSTM baseline...")
        symbolizer = FinwiseSymbolizer(
            tickers=self.tickers,
            period="10y",
            interval="1d",
            n_quantiles=5 
        )
        
        raw_data = symbolizer.fetch_data()
        if raw_data.empty:
            raise ValueError("Failed to fetch data for LSTM.")
            
        change_data = symbolizer._calculate_changes(raw_data)
        
        # Ensure column order matches our expectation
        all_cols = []
        for t in self.tickers:
            all_cols.append(f"{t}_P_Change")
            all_cols.append(f"{t}_V_Change")
        
        return change_data[all_cols]

    def _preprocess_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Scales the data and creates time-step sequences for the LSTM.
        
        Returns:
            X_train, y_train, X_test, y_test
        """
        print("Preprocessing data: Scaling and creating sequences...")
        
        # 1. Scale the data
        # LSTMs are sensitive to scale. We use MinMaxScaler.
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = self.scaler.fit_transform(df)
        
        # Save the scaler to inverse-transform predictions later
        joblib.dump(self.scaler, self.scaler_path)
        print(f"Scaler saved to {self.scaler_path}")

        # 2. Create sequences
        # We slide a window (sequence_length) over the data.
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i-self.sequence_length:i, :]) # All features for the past N days
            y.append(scaled_data[i, self.target_col_index])   # The target price change for the next day
            
        X, y = np.array(X), np.array(y)
        
        # 3. Split into Train/Test
        # Time series data must not be shuffled.
        test_split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:test_split_idx], X[test_split_idx:]
        y_train, y_test = y[:test_split_idx], y[test_split_idx:]
        
        print(f"Data shape: X_train: {X_train.shape}, X_test: {X_test.shape}")
        return X_train, y_train, X_test, y_test

    def _build_model(self):
        """
        Defines the Keras LSTM model architecture.
        """
        print("Building LSTM model...")
        model = Sequential()
        
        # Layer 1: LSTM with 50 units
        model.add(LSTM(
            units=50, 
            return_sequences=True, 
            input_shape=(self.sequence_length, self.n_features)
        ))
        model.add(Dropout(0.2)) # Regularization

        # Layer 2: LSTM
        model.add(LSTM(units=50, return_sequences=False))
        model.add(Dropout(0.2))

        # Layer 3: Dense
        model.add(Dense(units=25))

        # Output Layer: Single neuron (predicting one value)
        model.add(Dense(units=1))

        # Compile the model
        model.compile(optimizer='adam', loss='mean_squared_error')
        self.model = model
        print(model.summary())

    def train(self, X_train, y_train, epochs=50, batch_size=32):
        """
        Trains the LSTM model.
        """
        if self.model is None:
            self._build_model()
            
        print("Starting model training...")
        
        # Callbacks for production-grade training
        # Save only the best model
        checkpoint = ModelCheckpoint(
            self.model_path, 
            monitor='val_loss', 
            save_best_only=True, 
            mode='min',
            verbose=1
        )
        
        # Stop training if the validation loss doesn't improve
        early_stopping = EarlyStopping(
            monitor='val_loss', 
            patience=10, 
            mode='min', 
            verbose=1,
            restore_best_weights=True
        )
        
        history = self.model.fit(
            X_train, 
            y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2, # Use part of training data for validation
            callbacks=[checkpoint, early_stopping],
            verbose=1
        )
        
        print(f"Training complete. Best model saved to {self.model_path}")
        self.model = load_model(self.model_path) # Load the best model

    def evaluate(self, X_test, y_test_scaled) -> dict:
        """
        Evaluates the model on the test set and returns metrics.
        """
        print("Evaluating model...")
        if self.model is None:
            if os.path.exists(self.model_path):
                self.model = load_model(self.model_path)
            else:
                raise ValueError("Model not trained. Run train() first.")
        
        if self.scaler is None:
            self.scaler = joblib.load(self.scaler_path)

        # 1. Make predictions (scaled)
        predictions_scaled = self.model.predict(X_test)
        
        # 2. Inverse Transform Predictions
        # We need to revert the scaling to compare apples-to-apples.
        # This is complex because the scaler was fit on ALL features.
        
        # Create a dummy array with the shape of the original data (n_samples, n_features)
        dummy_predictions = np.zeros((len(predictions_scaled), self.n_features))
        
        # Place our predictions into the correct column (the target column)
        dummy_predictions[:, self.target_col_index] = predictions_scaled.flatten()
        
        # Now, inverse transform the entire dummy array
        predictions_actual = self.scaler.inverse_transform(dummy_predictions)[:, self.target_col_index]

        # 3. Inverse Transform Ground Truth (y_test)
        dummy_y_test = np.zeros((len(y_test_scaled), self.n_features))
        dummy_y_test[:, self.target_col_index] = y_test_scaled.flatten()
        y_test_actual = self.scaler.inverse_transform(dummy_y_test)[:, self.target_col_index]

        # 4. Calculate Metrics
        rmse = np.sqrt(mean_squared_error(y_test_actual, predictions_actual))
        mape = mean_absolute_percentage_error(y_test_actual, predictions_actual)
        
        print(f"--- LSTM Baseline Evaluation ---")
        print(f"Target: {self.ticker_to_predict} Price Change")
        print(f"RMSE (Root Mean Squared Error): {rmse:.6f}")
        print(f"MAPE (Mean Abs Pct Error): {mape:.6f}")
        print("---------------------------------")
        
        return {"rmse": rmse, "mape": mape}

# --- Script'i çalıştırmak için ---
if __name__ == "__main__":
    
    TICKERS_LIST = ["MSFT", "AAPL", "GOOGL", "AMZN", "NVDA", "TSLA"]
    TARGET_TICKER = "MSFT" # We will try to predict Microsoft's price change
    
    lstm_builder = LSTMBaselineModel(
        tickers=TICKERS_LIST,
        ticker_to_predict=TARGET_TICKER
    )
    
    # 1. Get data
    numerical_data = lstm_builder._get_numerical_data()
    
    # 2. Preprocess
    X_train, y_train, X_test, y_test = lstm_builder._preprocess_data(numerical_data)
    
    # 3. Train
    lstm_builder.train(X_train, y_train, epochs=50) # Epochs=50 for speed, use 100+ for accuracy
    
    # 4. Evaluate
    metrics = lstm_builder.evaluate(X_test, y_test)
    
    print(f"Baseline model for {TARGET_TICKER} trained and evaluated.")
    print(f"Metrics: {metrics}")
    # Metrics: {'rmse': np.float64(0.01389415932052521), 'mape': 1.4731242292198676}