import os
import numpy as np
import pandas as pd
import joblib
import logging
# Suppress TF logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf
from tensorflow.keras.models import load_model
from app.ml.symbolizer import FinwiseSymbolizer

logger = logging.getLogger("uvicorn")

class LSTMEngine:
    def __init__(self, sequence_length: int = 60):
        self.sequence_length = sequence_length
        self.model_dir = "/app/models" 
        self.model_path = os.path.join(self.model_dir, "lstm_baseline.h5")
        self.scaler_path = os.path.join(self.model_dir, "lstm_scaler.joblib")
        
        self.model = None
        self.scaler = None
        self._load_resources()

    def _load_resources(self):
        try:
            if os.path.exists(self.model_path):
                # FIXED: compile=False prevents the "metrics" deserialization error
                self.model = load_model(self.model_path, compile=False)
                logger.info(f"LSTM: Model loaded successfully from {self.model_path}")
            
            if os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
                logger.info("LSTM: Scaler loaded.")
                
        except Exception as e:
            logger.error(f"LSTM Load Error: {e}")

    def _get_token_from_values(self, p_change, v_change):
        """
        Converts numeric predictions to tokens using Standard Technical Analysis thresholds.
        These match the logic used in symbolizer.py to ensure 'Ground Truth' alignment.
        """
        # 1. Price Token Logic
        if p_change >= 0.03: p_token = "P_SURGE"      # > 3%
        elif p_change <= -0.03: p_token = "P_CRASH"   # < -3%
        elif p_change >= 0.01: p_token = "P_HIGH"     # > 1%
        elif p_change <= -0.01: p_token = "P_LOW"     # < -1%
        else: p_token = "P_MID"                       # Stable (-1% to 1%)

        # 2. Volume Token Logic
        if v_change >= 0.20: v_token = "V_SURGE"      # > 20%
        elif v_change >= 0.10: v_token = "V_PEAK"     # > 10%
        elif v_change >= 0.05: v_token = "V_HIGH"     # > 5%
        elif v_change <= -0.05: v_token = "V_LOW"     # < -5%
        else: v_token = "V_MID"

        return f"{p_token}_{v_token}"

    def predict(self, symbol: str, data_override: pd.DataFrame = None):
        """
        Args:
            symbol: Ticker symbol
            data_override: Optional DataFrame. If provided, uses this data 
                           instead of fetching new data. 
                           Used for Backtesting/Validation loops.
        """
        if self.model is None or self.scaler is None:
            return {"error": "Model/Scaler not loaded."}

        try:
            # 1. Use Override Data (Validation) or Fetch New (Forecast)
            if data_override is not None:
                raw_data = data_override.copy()
            else:
                symbolizer = FinwiseSymbolizer(tickers=[symbol], period="1y") 
                raw_data = symbolizer.fetch_data()
            
            if raw_data.empty:
                return {"error": f"No data for {symbol}"}

            # 2. Process Features
            df = pd.DataFrame()
            df['P_Change'] = raw_data['Close'].pct_change()
            df['V_Change'] = raw_data['Volume'].pct_change()
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            df.dropna(inplace=True)

            if len(df) < self.sequence_length:
                return {"error": "Insufficient data length."}

            # 3. Create Sequence (Last 60 of the provided data)
            last_sequence = df.tail(self.sequence_length).values
            last_sequence_scaled = self.scaler.transform(last_sequence)
            input_tensor = last_sequence_scaled.reshape(1, self.sequence_length, 2)

            # 4. Predict
            prediction_scaled = self.model.predict(input_tensor, verbose=0)
            
            # 5. Inverse Transform
            prediction_actual = self.scaler.inverse_transform(prediction_scaled)[0]
            pred_p_change = prediction_actual[0]
            pred_v_change = prediction_actual[1]

            # 6. Tokenize
            token = self._get_token_from_values(pred_p_change, pred_v_change)

            return {
                "symbol": symbol,
                "predicted_change_pct": float(pred_p_change),
                "predicted_vol_change": float(pred_v_change),
                "prediction_token": token,
                "model": "LSTM_Dual_Output"
            }

        except Exception as e:
            logger.error(f"LSTM Inference Error: {e}")
            return {"error": str(e)}