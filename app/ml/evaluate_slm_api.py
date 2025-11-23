# app/ml/evaluate_slm_api.py

import os
import numpy as np
import pandas as pd
import time
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError
from sklearn.metrics import mean_squared_error
from dotenv import load_dotenv
from typing import Dict, Tuple

# Import main class for data processing
from symbolizer import FinwiseSymbolizer

# --- Settings ---
TICKERS_LIST = ["MSFT", "AAPL", "GOOGL", "AMZN", "NVDA", "TSLA"]
TARGET_TICKER = "MSFT" 
CONTEXT_WINDOW_SIZE = 60 
TEST_SPLIT_RATIO = 0.8 

HF_MODEL_ID = "microsoft/Phi-3-mini-4k-instruct"
BASELINE_LSTM_RMSE = 0.01389

class SLM_API_Evaluator:
    """
    Evaluates an SLM's forecasting ability (via Hugging Face API)
    against the LSTM baseline. (PoC v2.3 - Robust Retries)
    """
    
    def __init__(self, target_ticker: str):
        load_dotenv()
        hf_token = os.environ.get("HUGGINGFACE_API_KEY")
        if not hf_token:
            raise ValueError("HUGGINGFACE_API_KEY not found in .env file.")
            
        self.hf_client = InferenceClient(model=HF_MODEL_ID, token=hf_token)
        print(f"Hugging Face client initialized for model: {HF_MODEL_ID}")
        
        self.target_ticker = target_ticker
        self.symbolizer = FinwiseSymbolizer(
            tickers=TICKERS_LIST,
            period="10y",
            n_quantiles=5
        )
        self.token_to_value_mapper = None

    # --- No changes to this method ---
    def _build_quantization_mapper(self, train_numerical_df: pd.DataFrame, train_symbolic_df: pd.DataFrame):
        print("Building de-quantization mapper (Task 5)...")
        
        target_p_col = f"{self.target_ticker}_P_Change"
        target_p_token_col = f"{self.target_ticker}_P_Token"
        target_v_token_col = f"{self.target_ticker}_V_Token"

        df = pd.concat([
            train_numerical_df[target_p_col],
            train_symbolic_df[[target_p_token_col, target_v_token_col]]
        ], axis=1)

        df['Full_Token'] = df[target_p_token_col].astype(str) + "_" + df[target_v_token_col].astype(str)

        mapper = df.groupby('Full_Token')[target_p_col].mean().to_dict()

        print(f"Mapper built. {len(mapper)} unique tokens found in training data.")
        self.token_to_value_mapper = mapper


    def _get_api_prediction(self, history_sequence: str) -> str:
        """
        Calls the Hugging Face API (Phi-3-mini) with robust retry logic
        for rate limits and cold starts.
        """

        # --- RATE LIMIT FIX (v2.3) ---
        # To avoid HF free-tier rate limits,
        # wait 2 seconds between API calls. (1 sec was not enough)
        time.sleep(2.0)

        system_prompt = (
            "You are a financial pattern recognition expert. "
            "Your task is to analyze a sequence of symbolic financial market tokens "
            "and predict ONLY the single next token in the sequence. "
            "The tokens represent quantized price and volume movements. "
            "Do not explain your reasoning. Respond only with the next token."
        )

        user_prompt = (
            "Here is the recent history of market tokens (60 days): "
            f"{history_sequence}"
            "\n\nWhat is the single next token?"
        )

        prompt_template = f"<|user|>\n{system_prompt}\n\n{user_prompt}<|end|>\n<|assistant|>"

        max_retries = 3

        for attempt in range(max_retries):
            try:
                prediction = self.hf_client.text_generation(
                    prompt=prompt_template,
                    max_new_tokens=20,
                    temperature=0.1,
                )

                prediction = prediction.strip()

                # Extract the token starting with "P_"
                for word in prediction.split():
                    if word.startswith("P_"):
                        return word.replace('.', '').replace(',', '')

                return "P_MID_V_MID"  # Successful but meaningless response
            
            except HfHubHTTPError as e:
                # --- RETRY LOGIC (v2.3) ---
                if e.response.status_code == 503:  # Model loading (cold start)
                    print(f"  ... API 503 (Model Loading). Retrying in 10s (Attempt {attempt+1}/{max_retries})...")
                    time.sleep(10)
                elif e.response.status_code == 429:  # Rate limit
                    print(f"  ... API 429 (Rate Limit). Retrying in 10s (Attempt {attempt+1}/{max_retries})...")
                    time.sleep(10)
                else:
                    print(f"Hugging Face API call failed (HTTP {e.response.status_code}): {e}")
                    return "P_MID_V_MID"

            except Exception as e:
                print(f"Hugging Face API call failed (Non-HTTP): {e}")
                return "P_MID_V_MID"

        print(f"  ... API call failed after {max_retries} retries. Fallback.")
        return "P_MID_V_MID"


    # --- run_evaluation (fully translated) ---
    def run_evaluation(self) -> Tuple[float, float]:
        print("Fetching data (using Stooq)...")

        raw_data = self.symbolizer.fetch_data()
        numerical_data = self.symbolizer._calculate_changes(raw_data)
        symbolic_data = self.symbolizer._quantize_data(numerical_data)

        combined_data = pd.concat([
            numerical_data,
            symbolic_data
        ], axis=1).dropna()

        split_index = int(len(combined_data) * TEST_SPLIT_RATIO)
        train_df = combined_data.iloc[:split_index]
        test_df = combined_data.iloc[split_index:]

        print(f"Data split: Train samples={len(train_df)}, Test samples={len(test_df)}")

        self._build_quantization_mapper(
            train_df[[col for col in train_df.columns if '_Change' in col]],
            train_df[[col for col in train_df.columns if '_Token' in col]]
        )

        target_p_col = f"{self.target_ticker}_P_Change"
        target_p_token_col = f"{self.target_ticker}_P_Token"
        target_v_token_col = f"{self.target_ticker}_V_Token"

        full_symbolic_sequence = (
            combined_data[target_p_token_col].astype(str) +
            "_" +
            combined_data[target_v_token_col].astype(str)
        ).tolist()

        slm_predictions_numerical = []
        ground_truth_numerical = []

        print(f"\n--- Starting Evaluation Race (Test Set: {len(test_df)} steps) ---")

        for i in range(len(train_df), len(combined_data)):
            if (i - len(train_df)) % 10 == 0:
                print(f"Step {i - len(train_df)} / {len(test_df)}...")

            context_tokens = full_symbolic_sequence[i-CONTEXT_WINDOW_SIZE : i]
            context_str = " ".join(context_tokens)

            predicted_token = self._get_api_prediction(context_str)
            true_token = full_symbolic_sequence[i]

            true_numerical_value = combined_data.iloc[i][target_p_col]
            predicted_numerical_value = self.token_to_value_mapper.get(predicted_token, 0.0)

            slm_predictions_numerical.append(predicted_numerical_value)
            ground_truth_numerical.append(true_numerical_value)

        slm_rmse = np.sqrt(mean_squared_error(
            ground_truth_numerical,
            slm_predictions_numerical
        ))

        print("\n--- Evaluation Complete ---")
        print(f"Target Ticker: {self.target_ticker}")
        print(f"LSTM (Baseline) RMSE: {BASELINE_LSTM_RMSE:.6f}")
        print(f"SLM (HF Phi-3) RMSE: {slm_rmse:.6f}")

        if slm_rmse < BASELINE_LSTM_RMSE:
            print("\nRESULT: SUCCESS! The SLM (Symbolic Language Model) hypothesis outperformed the numeric LSTM baseline.")
        else:
            print("\nRESULT: FAILED. The numeric LSTM baseline performed better than the SLM (API) predictions.")

        return BASELINE_LSTM_RMSE, slm_rmse


# --- Script Entry Point ---
if __name__ == "__main__":
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    
    evaluator = SLM_API_Evaluator(target_ticker=TARGET_TICKER)
    evaluator.run_evaluation()
